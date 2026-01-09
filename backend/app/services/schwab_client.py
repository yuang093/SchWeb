import schwab
import pathlib
import json
import re
from datetime import datetime
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.persistence import SystemSetting
from typing import List, Dict, Any, Optional

class SchwabClient:
    def __init__(self):
        # 初始化為 None，在使用時延遲加載
        self._api_key = None
        self._api_secret = None
        self._redirect_uri = None
        # token.json 預計放在 backend 根目錄
        self.token_path = pathlib.Path(__file__).parent.parent.parent / "token.json"
        self._client = None

    def _refresh_config(self):
        """
        從資料庫讀取設定，若無則 fallback 到環境變數
        """
        db = SessionLocal()
        try:
            # 讀取 API Key
            setting_key = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_KEY").first()
            self._api_key = setting_key.value if setting_key else settings.SCHWAB_API_KEY
            
            # 讀取 API Secret
            setting_secret = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_SECRET").first()
            self._api_secret = setting_secret.value if setting_secret else settings.SCHWAB_API_SECRET
            
            # 讀取 Redirect URI
            setting_uri = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_REDIRECT_URI").first()
            self._redirect_uri = setting_uri.value if setting_uri else settings.SCHWAB_REDIRECT_URI
        finally:
            db.close()

    @property
    def api_key(self):
        if not self._api_key:
            self._refresh_config()
        return self._api_key

    @property
    def api_secret(self):
        if not self._api_secret:
            self._refresh_config()
        return self._api_secret

    def _parse_option_expiration(self, symbol: str) -> Optional[str]:
        """
        從選擇權 Symbol (例如 NVDA 261218C00200000 或 NVDA  261218C00200000) 解析出到期日 (Format: YY/MM/DD)
        標準 OSI 格式: Symbol (6 chars) + YYMMDD (6 chars) + Type (1 char) + Strike (8 chars)
        但嘉信 Symbol 可能中間有空格。
        """
        try:
            # 使用正則表達式尋找 6 位數字的日期部分
            # 尋找格式為: 至少一個字母 + 選擇性空格 + 6位數字(YYMMDD) + C/P + 8位數字
            match = re.search(r"([A-Z]+)\s*(\d{2})(\d{2})(\d{2})([CP])(\d+)", symbol)
            if match:
                yy = match.group(2)
                mm = match.group(3)
                dd = match.group(4)
                return f"{yy}/{mm}/{dd}"
        except Exception:
            pass
        return None

    def _get_52_week_high(self, data: Dict[str, Any]) -> Optional[float]:
        """
        強化的 52 週高點解析邏輯
        """
        # 嘉信 API 的結構可能在 quote 或 fundamental 下
        val = data.get("quote", {}).get("52WeekHigh")
        if val is None:
            val = data.get("fundamental", {}).get("high52Week")
        if val is None:
            val = data.get("quote", {}).get("high52Week")
        if val is None:
            val = data.get("52WeekHigh")
        
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def get_client(self):
        if self._client:
            return self._client
        
        if not self.token_path.exists():
            raise FileNotFoundError(f"找不到 token.json，請先執行 auth_schwab.py。路徑: {self.token_path}")

        self._client = schwab.auth.client_from_token_file(
            str(self.token_path),
            self.api_key,
            self.api_secret
        )
        return self._client

    def get_linked_accounts(self) -> List[Dict[str, Any]]:
        """
        獲取所有連結的帳戶清單並格式化 (schwab-py 1.0+ 語法)
        """
        try:
            client = self.get_client()
            resp = client.get_account_numbers()
            
            if resp.status_code != 200:
                print(f"❌ 向嘉信請求帳戶清單失敗: {resp.text}")
                return []
            
            raw_data = resp.json()
            accounts_list = raw_data if isinstance(raw_data, list) else [raw_data]
            
            formatted_accounts = []
            for acc in accounts_list:
                formatted_accounts.append({
                    "account_name": acc.get("accountType", "Schwab Account"),
                    "account_number": acc.get("accountNumber", "XXXX"),
                    "hash_value": acc.get("hashValue")
                })
            
            return formatted_accounts
        except Exception as e:
            print(f"❌ 獲取帳戶清單發生異常: {str(e)}")
            return []

    def get_real_account_data(self, account_hash: Optional[str] = None):
        """
        獲取真實數據並轉換為系統統一格式 (實作強制計算邏輯)
        """
        try:
            client = self.get_client()
            
            if not account_hash:
                accounts_list = self.get_linked_accounts()
                if not accounts_list:
                    return {"error": "未找到任何連結的帳戶"}
                account_hash = accounts_list[0]['hash_value']

            if not account_hash:
                return {"error": "無法獲取有效的 account_hash"}

            # 使用 get_account 獲取包含 positions 的詳細資訊
            resp = client.get_account(
                account_hash, 
                fields=client.Account.Fields.POSITIONS
            )
            
            if resp.status_code != 200:
                return {"error": f"獲取帳戶詳情失敗: {resp.text}"}
            
            raw_details = resp.json()
            details = raw_details[0] if isinstance(raw_details, list) else raw_details
            
            securities_account = details.get("securitiesAccount", {})
            positions = securities_account.get("positions", [])
            current_balances = securities_account.get("currentBalances", {})
            
            # 取得帳戶總資產 (用於計算佔比)
            total_account_value = float(current_balances.get("liquidationValue") or 0)

            # --- 新增：批量獲取報價 (Batch Quotes Fetching) ---
            symbols_to_quote = []
            for p in positions:
                instrument = p.get("instrument", {})
                asset_type = instrument.get("assetType", "EQUITY")
                # 包含 ETF 等資產類型
                if asset_type in ["EQUITY", "COLLECTIVE_INVESTMENT"]:
                    symbol = instrument.get("symbol")
                    if symbol:
                        # 嘉信 API 對於帶點的股票 (如 BRK.B) 需要轉換為 BRK/B
                        quote_symbol = symbol.replace(".", "/")
                        symbols_to_quote.append(quote_symbol)
            
            quote_map = {}
            if symbols_to_quote:
                try:
                    # 根據 schwab-py 文件，get_quotes 支援傳入 list
                    q_resp = client.get_quotes(symbols_to_quote)
                    
                    # --- 加入強力除錯訊息 (Debug Logs) ---
                    print(f"🔍 [DEBUG] Requesting Quotes for: {symbols_to_quote[:5]}...") # 印出前5個
                    if q_resp.status_code == 200:
                        raw_quotes = q_resp.json()
                        if raw_quotes:
                            first_key = list(raw_quotes.keys())[0]
                            print(f"🔍 [DEBUG] First Quote Key: {first_key}")
                            print(f"🔍 [DEBUG] First Quote Body: {raw_quotes[first_key]}")
                            
                            # 將轉換後的 key 映射回原本的 symbol
                            for p_inner in positions:
                                inst_inner = p_inner.get("instrument", {})
                                a_type = inst_inner.get("assetType")
                                if a_type in ["EQUITY", "COLLECTIVE_INVESTMENT"]:
                                    s_orig = inst_inner.get("symbol")
                                    if s_orig:
                                        # 嘗試多種匹配方式：原始、斜槓、點
                                        s_slash = s_orig.replace(".", "/")
                                        s_dot = s_orig.replace("/", ".")
                                        
                                        target_quote = None
                                        if s_orig in raw_quotes:
                                            target_quote = raw_quotes[s_orig]
                                        elif s_slash in raw_quotes:
                                            target_quote = raw_quotes[s_slash]
                                        elif s_dot in raw_quotes:
                                            target_quote = raw_quotes[s_dot]
                                        
                                        if target_quote:
                                            quote_map[s_orig] = target_quote
                            
                            # 特殊處理：再次掃描確保沒有遺漏 (不分大小寫匹配)
                            for k, v in raw_quotes.items():
                                if k not in quote_map:
                                    for p_inner in positions:
                                        s_orig = p_inner.get("instrument", {}).get("symbol")
                                        if s_orig:
                                            # 標準化後比較
                                            norm_k = k.replace("/", ".").upper()
                                            norm_s = s_orig.replace("/", ".").upper()
                                            if norm_k == norm_s:
                                                quote_map[s_orig] = v
                                                break
                        else:
                            print("❌ [DEBUG] Quote Response JSON is EMPTY!")
                    else:
                        print(f"❌ [DEBUG] Quote Response Failed! Status: {q_resp.status_code}")
                        print(f"⚠️ 批量獲取報價失敗: {q_resp.status_code} {q_resp.text}")
                    # --------------------------------------------
                except Exception as q_e:
                    print(f"⚠️ 批量獲取報價時發生異常: {str(q_e)}")
            # --------------------------------------------
            
            holdings = []
            for p in positions:
                instrument = p.get("instrument", {})
                symbol = instrument.get("symbol", "UNKNOWN")
                asset_type = instrument.get("assetType", "EQUITY")
                
                # 1. 基礎欄位獲取 (帶有 fallback)
                long_qty = float(p.get("longQuantity") or 0)
                short_qty = float(p.get("shortQuantity") or 0)
                
                if short_qty > 0:
                    qty = -1 * short_qty
                else:
                    qty = long_qty
                
                cost_basis = float(p.get("averagePrice") or 0)
                
                # 判斷乘數 (Multiplier)
                multiplier = 100 if asset_type == 'OPTION' else 1
                
                # 2. 損益與市值計算邏輯
                # 修正成本基礎 (Cost Basis): Short 單 (Qty=-1) 的成本會變成負數 (Credit)
                total_cost = qty * cost_basis * multiplier
                
                # 市值 (Market Value): 優先使用 API 提供的值，否則計算
                market_value = float(p.get("marketValue") or (qty * cost_basis * multiplier))
                
                # 反推現價 (若 API 沒有提供獨立的 currentPrice 欄位)
                price = market_value / (qty * multiplier) if qty != 0 else 0
                
                # 開倉損益 (Total P&L)
                total_pnl = float(p.get("longOpenProfitLoss") or p.get("shortOpenProfitLoss") or (market_value - total_cost))
                
                # 盈虧%: 分母必須取絕對值
                if abs(total_cost) > 0:
                    total_pnl_pct = (total_pnl / abs(total_cost)) * 100
                else:
                    total_pnl_pct = float(p.get("longOpenProfitLossPercent") or p.get("shortOpenProfitLossPercent") or 0)
                
                # 當日損益 (Day P&L)
                day_pnl = float(p.get("currentDayProfitLoss") or 0)
                
                # 強制計算當日變動百分比 (Day Chg %)
                # 優先使用 API 數值
                day_pnl_pct = p.get("currentDayProfitLossPercentage")
                if day_pnl_pct is not None:
                    day_pnl_pct = float(day_pnl_pct)
                
                # 如果 API 沒給 (None) 或為 0，但當日有損益 (day_pnl != 0)，則手動計算
                if (day_pnl_pct is None or day_pnl_pct == 0) and day_pnl != 0:
                    # 昨收市值 = 當前市值 - 當日損益
                    start_value = market_value - day_pnl
                    if start_value != 0:
                        day_pnl_pct = (day_pnl / abs(start_value)) * 100
                    else:
                        day_pnl_pct = 0
                elif day_pnl_pct is None:
                    day_pnl_pct = 0
                
                # 年度損益 (ytd_pnl_pct)
                # 若 API 回傳 0 或 None，明確設為 None，以便前端顯示為 -
                raw_ytd = p.get("yearToDateProfitLossPercent")
                if raw_ytd is None or float(raw_ytd) == 0:
                    ytd_pnl_pct = None
                else:
                    ytd_pnl_pct = float(raw_ytd)
                
                # 3. 新增欄位計算
                # 重新定義 cost_basis 為總成本 (使用者回饋)
                # 對於 EQUITY 和 COLLECTIVE_INVESTMENT，原本 cost_basis 儲存的是平均成本
                # 現在統一將回傳給前端的 cost_basis 欄位改為總投資成本
                display_cost_basis = total_cost
                
                # 解析選擇權到期日
                expiration_date = None
                if asset_type == "OPTION":
                    expiration_date = self._parse_option_expiration(symbol)
                
                # 計算資產佔比
                allocation_pct = (market_value / total_account_value * 100) if total_account_value > 0 else 0
                
                # 股票進階數據 (52WeekHigh, drawdown_pct)
                # 優先從批量獲取的 quote_map 中尋找數據
                symbol_quote = quote_map.get(symbol, {})
                
                # 使用強化的解析邏輯
                high_52week = self._get_52_week_high(symbol_quote)
                
                # 如果批量報價沒拿到，嘗試從持倉資料中的內嵌數據拿
                if high_52week is None:
                    # 嘗試從 positions 的多個可能位置提取
                    for source in [p, p.get("marketData", {}), p.get("quote", {}), instrument]:
                        if source:
                            high_52week = self._get_52_week_high({"quote": source}) if isinstance(source, dict) else None
                            if high_52week:
                                break
                
                drawdown_pct = None
                if high_52week and high_52week > 0:
                    drawdown_pct = ((price - high_52week) / high_52week) * 100
                
                holdings.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "price": price,
                    "cost_basis": display_cost_basis,
                    "market_value": market_value,
                    "total_pnl_pct": total_pnl_pct,
                    "total_pnl": total_pnl,
                    "day_pnl": day_pnl,
                    "day_pnl_pct": day_pnl_pct,
                    "ytd_pnl_pct": ytd_pnl_pct,
                    "asset_type": asset_type,
                    "expiration_date": expiration_date,
                    "allocation_pct": allocation_pct,
                    "drawdown_pct": drawdown_pct
                })

            total_balance = total_account_value
            cash_balance = current_balances.get("cashBalance", 0)
            
            return {
                "accounts": [{
                    "account_id": account_hash,
                    "total_balance": total_balance,
                    "cash_balance": cash_balance,
                    "buying_power": current_balances.get("buyingPower", 0),
                    "day_pl": float(securities_account.get("currentBalances", {}).get("totalCash", 0)),
                    "day_pl_percent": 0,
                    "holdings": holdings
                }]
            }
        except Exception as e:
            print(f"❌ [DEBUG] SchwabClient.get_real_account_data 發生異常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

schwab_client = SchwabClient()
