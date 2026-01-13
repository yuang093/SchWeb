import schwab
import pathlib
import json
import re
import os
from datetime import datetime
from app.core.config import settings
from app.db.database import SessionLocal
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

    def _save_token_to_db(self, token_dict: Dict[str, Any]):
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

    def get_client(self):
        self._migrate_token_file_if_needed()
        if self._client: return self._client
        token_data = self._load_token_from_db()
        if not token_data:
            print("❌ [DEBUG] No token data found in Database.")
            raise FileNotFoundError("找不到有效 Token，請先執行授權。")

        # 使用 client_from_access_functions，注意其內部會對 token_read_func 的結果做索引 ['token']
        self._client = schwab.auth.client_from_access_functions(
            self.api_key,
            self.api_secret,
            token_read_func=self._load_token_from_db,
            token_write_func=self._save_token_to_db
        )
        return self._client

    def get_linked_accounts(self) -> List[Dict[str, Any]]:
        try:
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
                sector = symbol_quote.get("fundamental", {}).get("sector") or symbol_quote.get("quote", {}).get("sector") or p.get("sector") or inst.get("sector") or "Other"
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

schwab_client = SchwabClient()
