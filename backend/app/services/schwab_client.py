import schwab
import pathlib
import json
import re
import os
from datetime import datetime, timedelta
from app.core.config import settings
from app.db.database import SessionLocal
from app.utils.sector_mapper import get_sector as get_fallback_sector
from app.models.persistence import SystemSetting, AssetHistory, HoldingSnapshot
from typing import List, Dict, Any, Optional

class SchwabClient:
    def __init__(self):
        self._api_key = None
        self._api_secret = None
        self._redirect_uri = None
        self.backend_dir = pathlib.Path(__file__).parent.parent.parent
        self.root_dir = self.backend_dir.parent
        self._client = None

    def _refresh_config(self):
        db = SessionLocal()
        try:
            setting_key = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_KEY").first()
            self._api_key = setting_key.value if setting_key else settings.SCHWAB_API_KEY
            setting_secret = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_SECRET").first()
            self._api_secret = setting_secret.value if setting_secret else settings.SCHWAB_API_SECRET
            setting_uri = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_REDIRECT_URI").first()
            self._redirect_uri = setting_uri.value if setting_uri else settings.SCHWAB_REDIRECT_URI
            
            key_preview = self._api_key[:4] if self._api_key else "None"
            secret_preview = self._api_secret[:4] if self._api_secret else "None"
            print(f"🚀 [DEBUG] Config Loaded: Key={key_preview}***, Secret={secret_preview}***")
            self._client = None
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

    def _save_token_to_db(self, token_dict: Dict[str, Any], **kwargs):
        db = SessionLocal()
        try:
            # 偵錯
            # print(f"🚀 [DEBUG] _save_token_to_db received: {list(token_dict.keys())}")
            
            # 如果傳入的是內部的 token (包含 access_token)
            # 但不包含外部包裝 'token' 鍵
            if "access_token" in token_dict and "token" not in token_dict:
                # 重新包裝成 token.json 原始格式
                # 嘗試尋找 creation_timestamp，若無則建立
                creation = token_dict.get("creation_timestamp") or int(datetime.now().timestamp())
                token_to_save = {
                    "token": token_dict,
                    "creation_timestamp": creation,
                    "expires_at": token_dict.get("expires_at") or (creation + token_dict.get("expires_in", 1800))
                }
            else:
                token_to_save = token_dict

            token_json = json.dumps(token_to_save)
            setting = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_TOKEN_DATA").first()
            if setting:
                setting.value = token_json
            else:
                setting = SystemSetting(key="SCHWAB_TOKEN_DATA", value=token_json)
                db.add(setting)
            db.commit()
            print("✅ [DEBUG] Database Token updated.")
        except Exception as e:
            print(f"❌ [ERROR] Failed to save token to DB: {e}")
            db.rollback()
        finally:
            db.close()

    def _load_token_from_db(self) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            setting = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_TOKEN_DATA").first()
            if setting and setting.value:
                data = json.loads(setting.value)
                # 這裡必須回傳最外層包含 'token' 的 Dict，滿足 schwab.auth 的格式驗證
                if isinstance(data, dict) and "token" in data:
                    return data
                elif isinstance(data, dict) and "access_token" in data:
                    # 如果資料庫裡存的是內層，則補齊外層
                    return {
                        "token": data,
                        "creation_timestamp": data.get("creation_timestamp") or int(datetime.now().timestamp())
                    }
        except Exception as e:
            print(f"❌ [ERROR] Failed to load token from DB: {e}")
        finally:
            db.close()
        return None

    def _archive_token_file(self, file_path: pathlib.Path):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = file_path.with_suffix(f".json.bak.{timestamp}")
            if archive_path.exists():
                os.remove(archive_path)
            os.rename(file_path, archive_path)
            print(f"📦 [DEBUG] Token file archived to {archive_path}")
        except Exception as e:
            print(f"⚠️ [WARNING] Failed to archive token file: {e}")

    def _migrate_token_file_if_needed(self):
        search_paths = [
            self.backend_dir / "token.json",
            self.root_dir / "token.json",
            pathlib.Path("token.json").absolute(),
            pathlib.Path("backend/token.json").absolute()
        ]
        unique_paths = []
        for p in search_paths:
            if p not in unique_paths:
                unique_paths.append(p)
        for path in unique_paths:
            if path.exists():
                try:
                    print(f"🔍 [DEBUG] Detecting token file at {path}...")
                    with open(path, 'r') as f:
                        file_token = json.load(f)
                    if isinstance(file_token, dict):
                        self._save_token_to_db(file_token)
                        print(f"🚀 [DEBUG] Successfully synced token file from {path} to Database.")
                        self._archive_token_file(path)
                        self._client = None
                        break
                except Exception as e:
                    print(f"❌ [ERROR] Forced migration from {path} failed: {e}")

    def _parse_option_expiration(self, symbol: str) -> Optional[str]:
        try:
            match = re.search(r"([A-Z]+)\s*(\d{2})(\d{2})(\d{2})([CP])(\d+)", symbol)
            if match:
                return f"{match.group(2)}/{match.group(3)}/{match.group(4)}"
        except Exception: pass
        return None

    def _get_52_week_high(self, data: Dict[str, Any]) -> Optional[float]:
        val = data.get("quote", {}).get("52WeekHigh") or \
              data.get("fundamental", {}).get("high52Week") or \
              data.get("quote", {}).get("high52Week") or \
              data.get("52WeekHigh")
        try: return float(val) if val is not None else None
        except: return None

    def reload_token(self):
        """
        強制清除記憶體中的 client 緩存，下次請求時會重新從資料庫讀取 Token
        """
        print("🔄 [DEBUG] Reloading token from database...")
        self._client = None
        self._refresh_config() # 同步刷新 API Key 設定

    def get_client(self):
        self._migrate_token_file_if_needed()
        if self._client: return self._client
        token_data = self._load_token_from_db()
        if not token_data:
            print("❌ [DEBUG] No token data found in Database.")
            raise FileNotFoundError("找不到有效 Token，請先執行授權。")

        # 使用 client_from_access_functions，注意其內部會對 token_read_func 的結果做索引 ['token']
        try:
            self._client = schwab.auth.client_from_access_functions(
                self.api_key,
                self.api_secret,
                token_read_func=self._load_token_from_db,
                token_write_func=self._save_token_to_db
            )
        except Exception as e:
            # 如果初始化失敗（例如 Token 格式錯誤），嘗試清除快照
            print(f"⚠️ [DEBUG] Client initialization failed: {e}")
            self._client = None
            raise
            
        return self._client

    def get_linked_accounts(self) -> List[Dict[str, Any]]:
        try:
            client = self.get_client()
            resp = client.get_account_numbers()
            
            # 如果發生 Token 錯誤，嘗試重新載入並重試一次
            if resp.status_code == 400 and "unsupported_token_type" in resp.text:
                print("⚠️ [DEBUG] Unsupported token type detected, retrying with fresh token...")
                self.reload_token()
                client = self.get_client()
                resp = client.get_account_numbers()

            if resp.status_code != 200: return []
            raw_data = resp.json()
            accounts_list = raw_data if isinstance(raw_data, list) else [raw_data]
            return [{
                "account_name": acc.get("accountType", "Schwab Account"),
                "account_number": acc.get("accountNumber", "XXXX"),
                "hash_value": acc.get("hashValue")
            } for acc in accounts_list]
        except Exception as e:
            print(f"❌ 獲取帳戶清單發生異常: {str(e)}")
            return []

    def get_real_account_data(self, account_hash: Optional[str] = None):
        try:
            client = self.get_client()
            if not account_hash:
                accs = self.get_linked_accounts()
                if not accs: return {"error": "未找到任何連結的帳戶"}
                account_hash = accs[0]['hash_value']

            resp = client.get_account(account_hash, fields=client.Account.Fields.POSITIONS)
            
            # Token 錯誤處理與重試
            if resp.status_code == 400 and "unsupported_token_type" in resp.text:
                print("⚠️ [DEBUG] Unsupported token type in get_account, retrying...")
                self.reload_token()
                client = self.get_client()
                resp = client.get_account(account_hash, fields=client.Account.Fields.POSITIONS)

            if resp.status_code != 200: return {"error": f"獲取帳戶詳情失敗: {resp.text}"}
            
            raw_details = resp.json()
            details = raw_details[0] if isinstance(raw_details, list) else raw_details
            securities_account = details.get("securitiesAccount", {})
            positions = securities_account.get("positions", [])
            current_balances = securities_account.get("currentBalances", {})
            total_account_value = float(current_balances.get("liquidationValue") or 0)

            symbols_to_quote = []
            for p in positions:
                inst = p.get("instrument", {})
                if inst.get("assetType") in ["EQUITY", "COLLECTIVE_INVESTMENT"]:
                    s = inst.get("symbol")
                    if s: symbols_to_quote.append(s.replace(".", "/"))
            
            quote_map = {}
            if symbols_to_quote:
                try:
                    q_resp = client.get_quotes(symbols_to_quote)
                    if q_resp.status_code == 200:
                        raw_quotes = q_resp.json()
                        if raw_quotes:
                            for p_inner in positions:
                                s_orig = p_inner.get("instrument", {}).get("symbol")
                                if not s_orig: continue
                                for k, v in raw_quotes.items():
                                    if k.replace("/", ".").upper() == s_orig.replace("/", ".").upper():
                                        quote_map[s_orig] = v
                                        break
                except Exception as q_e: print(f"⚠️ 報價異常: {q_e}")
            
            holdings = []
            for p in positions:
                inst = p.get("instrument", {})
                symbol = inst.get("symbol", "UNKNOWN")
                asset_type = inst.get("assetType", "EQUITY")
                
                qty = -float(p.get("shortQuantity") or 0) if float(p.get("shortQuantity") or 0) > 0 else float(p.get("longQuantity") or 0)
                cost_basis = float(p.get("averagePrice") or 0)
                multiplier = 100 if asset_type == 'OPTION' else 1
                total_cost = qty * cost_basis * multiplier
                market_value = float(p.get("marketValue") or total_cost)
                price = market_value / (qty * multiplier) if qty != 0 else 0
                total_pnl = float(p.get("longOpenProfitLoss") or p.get("shortOpenProfitLoss") or (market_value - total_cost))
                total_pnl_pct = (total_pnl / abs(total_cost)) * 100 if abs(total_cost) > 0 else float(p.get("longOpenProfitLossPercent") or 0)
                
                day_pnl = float(p.get("currentDayProfitLoss") or 0)
                day_pnl_pct = float(p.get("currentDayProfitLossPercentage") or 0)
                if day_pnl_pct == 0 and day_pnl != 0:
                    start_val = market_value - day_pnl
                    day_pnl_pct = (day_pnl / abs(start_val)) * 100 if start_val != 0 else 0
                
                raw_ytd = p.get("yearToDateProfitLossPercent")
                ytd_pnl_pct = float(raw_ytd) if raw_ytd is not None and float(raw_ytd) != 0 else None
                
                symbol_quote = quote_map.get(symbol, {})
                high_52w = self._get_52_week_high(symbol_quote)
                if high_52w is None:
                    for src in [p, p.get("marketData", {}), p.get("quote", {}), inst]:
                        high_52w = self._get_52_week_high({"quote": src}) if isinstance(src, dict) else None
                        if high_52w: break
                
                drawdown_pct = ((price - high_52w) / high_52w * 100) if high_52w and high_52w > 0 else None
                sector = symbol_quote.get("fundamental", {}).get("sector") or \
                         symbol_quote.get("quote", {}).get("sector") or \
                         p.get("sector") or \
                         inst.get("sector")
                
                # 如果 API 沒給，使用預定義映射
                if not sector or sector == "Other":
                    sector = get_fallback_sector(symbol, asset_type)

                name = symbol_quote.get("reference", {}).get("description") or inst.get("description") or p.get("description") or symbol

                holdings.append({
                    "symbol": symbol, "name": name, "quantity": qty, "price": price,
                    "cost_basis": total_cost, "market_value": market_value,
                    "total_pnl_pct": total_pnl_pct, "total_pnl": total_pnl,
                    "day_pnl": day_pnl, "day_pnl_pct": day_pnl_pct,
                    "ytd_pnl_pct": ytd_pnl_pct, "asset_type": asset_type,
                    "expiration_date": self._parse_option_expiration(symbol) if asset_type == "OPTION" else None,
                    "allocation_pct": (market_value / total_account_value * 100) if total_account_value > 0 else 0,
                    "drawdown_pct": drawdown_pct, "sector": sector
                })

            total_balance = total_account_value
            cash_balance = current_balances.get("cashBalance", 0)
            self._sync_real_data_to_db(account_hash, total_balance, cash_balance, holdings)
            
            # 非同步同步交易紀錄 (股息與已實現損益)
            try:
                self.sync_transactions(account_hash)
            except Exception as e:
                print(f"⚠️ 同步交易紀錄失敗: {e}")

            return {
                "accounts": [{
                    "account_id": account_hash,
                    "total_balance": total_balance,
                    "cash_balance": cash_balance,
                    "buying_power": current_balances.get("buyingPower", 0),
                    "day_pl": sum(h["day_pnl"] for h in holdings),
                    "day_pl_percent": (sum(h["day_pnl"] for h in holdings) / abs(total_account_value - sum(h["day_pnl"] for h in holdings)) * 100) if (total_account_value - sum(h["day_pnl"] for h in holdings)) != 0 else 0,
                    "holdings": holdings
                }]
            }
        except Exception as e:
            print(f"❌ [DEBUG] SchwabClient.get_real_account_data 異常: {str(e)}")
            import traceback; traceback.print_exc()
            return {"error": str(e)}

    def _sync_real_data_to_db(self, account_hash: str, total_balance: float, cash_balance: float, holdings: List[Dict[str, Any]]):
        db = SessionLocal()
        try:
            today = datetime.now().date()
            hist = db.query(AssetHistory).filter(AssetHistory.date == today).first()
            if hist:
                hist.total_value, hist.cash_balance = total_balance, cash_balance
            else:
                db.add(AssetHistory(date=today, total_value=total_balance, cash_balance=cash_balance))
            
            db.query(HoldingSnapshot).filter(HoldingSnapshot.date == today).delete()
            for h in holdings:
                db.add(HoldingSnapshot(
                    date=today, symbol=h["symbol"], name=h.get("name") or h["symbol"],
                    quantity=h["quantity"], market_value=h["market_value"],
                    cost_basis=h["cost_basis"], industry=h.get("sector", "Equity")
                ))
            db.commit()
            print("✅ [DEBUG] Sync REAL data to DB success.")
        except Exception as e:
            print(f"❌ [ERROR] Sync REAL data to DB fail: {e}")
            db.rollback()
        finally: db.close()

    def sync_transactions(self, account_hash: str):
        """
        同步交易紀錄，提取股息與已實現損益
        """
        try:
            client = self.get_client()
            db = SessionLocal()
            try:
                from app.models.persistence import Dividend, TradeHistory
                
                # 循環抓取最近 5 年的交易 (API 限制單次請求範圍不得超過一年)
                now = datetime.now()
                # 追蹤本次同步已處理的 ID，避免段落重疊造成的重複
                processed_ids = set()
                
                for i in range(5):
                    # 每一段抓取一年的資料
                    # 為了避免重疊，結束日期減去一秒
                    seg_start = now - timedelta(days=365 * (i + 1))
                    seg_end = now - timedelta(days=365 * i) - timedelta(seconds=1)
                    if i == 0: seg_end = now # 第一段包含到現在
                    
                    print(f"🔄 [DEBUG] 同步交易段落 {i+1}: {seg_start.date()} -> {seg_end.date()}")
                    resp = client.get_transactions(account_hash, start_date=seg_start, end_date=seg_end)
                    
                    if resp.status_code != 200:
                        print(f"⚠️ 無法獲取交易紀錄 ({seg_start.date()} 區段): {resp.text}")
                        continue

                    transactions = resp.json()
                    if not transactions:
                        continue

                    for tx in transactions:
                        tx_type = tx.get("type")
                        tx_id = str(tx.get("activityId")) if tx.get("activityId") else None
                        
                        if tx_id:
                            if tx_id in processed_ids: continue
                            processed_ids.add(tx_id)
                        tx_date_str = tx.get("settlementDate") or tx.get("tradeDate")
                        if not tx_date_str: continue
                        tx_date = datetime.strptime(tx_date_str[:10], "%Y-%m-%d").date()
                        
                        # 處理股息 (包含現金股息與再投入)
                        desc = tx.get("description", "")
                        # 嘗試從其他地方抓描述
                        if not desc:
                            if "transactionItem" in tx:
                                desc = tx["transactionItem"].get("description", "")
                            elif "transferItems" in tx and len(tx["transferItems"]) > 0:
                                desc = tx["transferItems"][0].get("description", "")
                        
                        is_div_type = tx_type == "DIVIDEND_OR_INTEREST"
                        is_div_desc = any(k in desc for k in ["Div", "Dividend", "Reinvest", "DRIP"])
                        
                        if is_div_type or is_div_desc:
                            amount = 0
                            symbol = "CASH"
                            
                            # 優先從 transferItems 提取金額
                            if "transferItems" in tx:
                                for item in tx["transferItems"]:
                                    amount += abs(float(item.get("amount") or 0))
                                    symbol = item.get("instrument", {}).get("symbol", symbol)
                            
                            # 如果 transferItems 沒金額，嘗試從 transactionItem (針對 TRADE 型態的 Reinvest)
                            if amount == 0 and "transactionItem" in tx:
                                item = tx["transactionItem"]
                                amount = abs(float(item.get("amount") or 0) * float(item.get("price") or 1))
                                symbol = item.get("instrument", {}).get("symbol", symbol)

                            if amount > 0:
                                # 檢查是否已存在
                                existing = None
                                if tx_id:
                                    existing = db.query(Dividend).filter(Dividend.transaction_id == tx_id).first()
                                
                                if not existing:
                                    # 回退方案
                                    existing = db.query(Dividend).filter(
                                        Dividend.account_hash == account_hash,
                                        Dividend.date == tx_date,
                                        Dividend.symbol == symbol,
                                        Dividend.amount == amount
                                    ).first()
                                
                                if not existing:
                                    db.add(Dividend(
                                        transaction_id=tx_id,
                                        account_hash=account_hash,
                                        date=tx_date,
                                        symbol=symbol,
                                        amount=amount,
                                        description=desc
                                    ))

                        # 處理交易 (買入/賣出)
                        elif tx_type == "TRADE":
                            # 統一處理不同格式的交易項目 (某些 API 回傳 transactionItem, 某些回傳 transferItems)
                            items = []
                            if "transactionItem" in tx:
                                items.append(tx["transactionItem"])
                            if "transferItems" in tx:
                                for t_item in tx["transferItems"]:
                                    # 排除貨幣項目，只保留證券項目
                                    if t_item.get("instrument", {}).get("assetType") not in ["CURRENCY", "CASH"]:
                                        items.append(t_item)
                            
                            for item in items:
                                symbol = item.get("instrument", {}).get("symbol", "UNKNOWN")
                                qty = float(item.get("amount") or 0)
                                price = float(item.get("price") or 0)
                                
                                # 判定方向 (SELL/BUY)
                                # 1. 優先看 instruction
                                instruction = item.get("instruction")
                                # 2. 若無 instruction，看 positionEffect
                                if not instruction:
                                    effect = item.get("positionEffect")
                                    if effect == "CLOSING": instruction = "SELL"
                                    elif effect == "OPENING": instruction = "BUY"
                                
                                # 3. 最後看 netAmount 與數量的正負號 (錢進來為 SELL)
                                if not instruction:
                                    instruction = "SELL" if tx.get("netAmount", 0) > 0 else "BUY"

                                if instruction in ["SELL", "BUY"] and qty > 0:
                                    # 檢查是否已重複 (優先使用 tx_id)
                                    existing = None
                                    if tx_id:
                                        existing = db.query(TradeHistory).filter(TradeHistory.transaction_id == tx_id).first()
                                    
                                    if not existing:
                                        # 回退方案：組合鍵排重
                                        existing = db.query(TradeHistory).filter(
                                            TradeHistory.account_hash == account_hash,
                                            TradeHistory.date == tx_date,
                                            TradeHistory.symbol == symbol,
                                            TradeHistory.side == instruction,
                                            TradeHistory.quantity == qty
                                        ).first()
    
                                    if not existing:
                                        # 嘗試提取已實現損益 (某些 API 欄位可能會提供)
                                        realized_pnl = float(tx.get("realizedPnL") or item.get("realizedPnL") or 0.0)
                                        
                                        # 如果 realized_pnl 為 0 且是賣出，試著從描述中找看看 (有的話)
                                        if realized_pnl == 0 and instruction == "SELL":
                                            match = re.search(r"Realized [^:]+:\s*([+-]?[\d,.]+)", desc)
                                            if match:
                                                try:
                                                    realized_pnl = float(match.group(1).replace(',', ''))
                                                except: pass
                                            else:
                                                db.add(TradeHistory(
                                            account_hash=account_hash,
                                            date=tx_date,
                                            symbol=symbol,
                                            transaction_id=tx_id,
                                            side=instruction,
                                            quantity=qty,
                                            price=price,
                                            realized_pnl=realized_pnl,
                                            description=desc
                                        ))
                            
                        # 處理轉帳 (入金/出金)
                        else:
                            desc = desc.upper()
                            amount = abs(tx.get("netAmount", 0))
                            if amount > 0:
                                side = None
                                # 排除來自 TD Ameritrade 的初始移轉紀錄 (避免與手動校正重複計算)
                                if any(k in desc for k in ["TD AMERITRADE", "TOA ACAT"]):
                                    side = None
                                # 入金邏輯
                                elif (tx_type == 'WIRE_IN') or ('FUNDS RECEIVED' in desc) or ('ACH RECEIPT' in desc):
                                    side = 'DEPOSIT'
                                # 出金邏輯
                                elif (tx_type == 'CASH_DISBURSEMENT') or ('ATM' in desc) or ('WITHDRAWAL' in desc):
                                    side = 'WITHDRAWAL'
                                # 內部轉帳 (Journal) - 區分方向 (排除非資金性質的帳務調整)
                                elif tx_type == 'JOURNAL':
                                    # 必須有明確的轉入/轉出關鍵字，且排除到期或再投資
                                    if any(k in desc for k in ['MATURED', 'REINVEST', 'DIVIDEND']):
                                        side = None
                                    elif any(k in desc for k in ['TRF FUNDS FRM', 'JOURNAL FRM']):
                                        side = 'DEPOSIT'
                                    elif any(k in desc for k in ['TRF FUNDS TO', 'JOURNAL TO']):
                                        side = 'WITHDRAWAL'
                                
                                if side:
                                    # 檢查是否已重複 (優先使用 tx_id)
                                    existing = None
                                    if tx_id:
                                        existing = db.query(TradeHistory).filter(TradeHistory.transaction_id == tx_id).first()
                                    
                                    if not existing:
                                        db.add(TradeHistory(
                                            transaction_id=tx_id,
                                            account_hash=account_hash,
                                            date=tx_date,
                                            symbol='CASH',
                                            side=side,
                                            quantity=amount,
                                            price=1.0,
                                            realized_pnl=0.0,
                                            description=desc
                                        ))
    
                    # 結束所有段落後一次提交
                db.commit()
            except Exception as e:
                print(f"❌ [ERROR] Processing transactions fail: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            print(f"❌ [ERROR] sync_transactions 異常: {e}")
            
    def get_price_history(self, symbol: str,
                          period_type: str = 'year', period: int = 1,
                          frequency_type: str = 'daily', frequency: int = 1):
        """
        獲取 Market Data Price History
        API Endpoint: /marketdata/v1/pricehistory
        """
        try:
            client = self.get_client()
            # schwab-py 封裝了此方法
            resp = client.get_price_history(
                symbol,
                period_type=client.PriceHistory.PeriodType(period_type),
                period=client.PriceHistory.Period(period),
                frequency_type=client.PriceHistory.FrequencyType(frequency_type),
                frequency=client.PriceHistory.Frequency(frequency)
            )
            
            if resp.status_code != 200:
                print(f"⚠️ 獲取價格歷史失敗 ({symbol}): {resp.text}")
                return None
                
            return resp.json()
        except Exception as e:
            print(f"❌ [ERROR] get_price_history 異常 ({symbol}): {e}")
            return None
 
schwab_client = SchwabClient()
