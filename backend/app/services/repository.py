import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.persistence import AssetHistory, HoldingSnapshot, Dividend, TradeHistory
from sqlalchemy import func
from app.services.schwab_client import schwab_client
from datetime import datetime

# 設定基礎目錄 (backend 根目錄)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class AccountRepository:
    def __init__(self, mock_file: str = "mock_data/account.json"):
        # 使用絕對路徑
        self.mock_file_path = BASE_DIR / mock_file

    def get_account_list(self) -> List[Dict[str, Any]]:
        """
        獲取所有可選帳戶
        """
        # 防呆：清理字串
        current_mode = settings.APP_MODE.strip().upper()
        print(f"\n🚀 [DEBUG] Repository Check: Mode='{current_mode}' (Raw='{settings.APP_MODE}')")
        
        if current_mode == "REAL":
            print("🚀 [DEBUG] 進入 REAL 分支，正在呼叫嘉信 API...")
            try:
                accounts = schwab_client.get_linked_accounts()
                print(f"🚀 [DEBUG] 成功獲取帳戶: {accounts}")
                
                if not accounts:
                    print("⚠️ [WARNING] 嘉信回傳了空列表！")
                    # 回傳一個「錯誤提示帳戶」讓前端顯示，而不是切回 Mock
                    return [{"hash_value": "ERROR", "account_number": "0000", "account_name": "No Accounts Found"}]
                
                return accounts
            except Exception as e:
                print(f"❌ [CRITICAL ERROR] 呼叫嘉信 API 失敗: {e}")
                import traceback
                traceback.print_exc()
                # 發生錯誤時，回傳錯誤提示，絕對不要 fallback 到 mock
                return [{"hash_value": "ERROR", "account_number": "XXXX", "account_name": f"Error: {str(e)[:20]}"}]
        
        # 僅在 MOCK 模式下回傳模擬數據
        print("ℹ️ [INFO] 非 REAL 模式，回傳 Mock Data")
        return [{
            "account_name": "MOCK ACCOUNT",
            "account_number": "MOCK-123",
            "hash_value": "mock_hash_123"
        }]

    def get_account_data(self, account_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        根據 APP_MODE 獲取資料 (REAL 或 MOCK)
        """
        current_mode = settings.APP_MODE.strip().upper()
        
        if current_mode == "REAL":
            try:
                print(f"INFO: APP_MODE=REAL, fetching data for account: {account_hash or 'default'}")
                data = schwab_client.get_real_account_data(account_hash)
                # 注意：schwab_client.get_real_account_data 內部已經實作了 _sync_real_data_to_db
                # 這裡不需重複呼叫，避免重複寫入且格式不一致的問題
                if "error" in data:
                    print(f"❌ [CRITICAL] 真實數據獲取包含錯誤: {data['error']}")
                return data
            except Exception as e:
                print(f"❌ [CRITICAL] 真實數據獲取失敗: {e}")
                import traceback
                traceback.print_exc()
                return {"error": str(e)}
        else:
            # 預設為 MOCK
            return self._load_mock_data()

    def _sync_real_data_to_db(self, data: Dict[str, Any]):
        """
        將從 API 抓到的最新數據寫入 SQLite
        """
        db = SessionLocal()
        try:
            acc = data["accounts"][0]
            today = datetime.now().date()
            
            # 1. 更新或建立今日資產歷史
            existing_history = db.query(AssetHistory).filter(AssetHistory.date == today).first()
            if existing_history:
                existing_history.total_value = acc["total_balance"]
                existing_history.cash_balance = acc["cash_balance"]
            else:
                new_history = AssetHistory(
                    date=today,
                    total_value=acc["total_balance"],
                    cash_balance=acc["cash_balance"]
                )
                db.add(new_history)
            
            # 2. 更新今日持倉快照 (先刪除今日舊的，再重新寫入最新的)
            db.query(HoldingSnapshot).filter(HoldingSnapshot.date == today).delete()
            for h in acc["holdings"]:
                snapshot = HoldingSnapshot(
                    date=today,
                    symbol=h["symbol"],
                    name=h["name"],
                    quantity=h["quantity"],
                    market_value=h["market_value"],
                    cost_basis=h["average_cost"] * h["quantity"],
                    industry=h.get("sector", "Equity")
                )
                db.add(snapshot)
            
            db.commit()
            print("INFO: Successfully synced REAL data to SQLite.")
        except Exception as e:
            print(f"Error syncing REAL data to DB: {e}")
            db.rollback()
        finally:
            db.close()

    def get_account_summary(self, account_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取帳戶摘要
        """
        data = self.get_account_data(account_hash)
        if "error" in data:
            return data
        
        acc_summary = data["accounts"][0].copy()
        
        db = SessionLocal()
        try:
            total_dividends = db.query(func.sum(Dividend.amount)).scalar() or 0.0
            acc_summary["total_dividends"] = float(total_dividends)

            realized_pnl = db.query(func.sum(TradeHistory.realized_pnl)).scalar() or 0.0
            acc_summary["realized_pnl"] = float(realized_pnl)

        except Exception as e:
            print(f"Error loading summary stats from DB: {str(e)}")
        finally:
            db.close()
            
        # 計算 Beta 係數 (加權持倉)
        from app.utils.risk import calculate_weighted_beta
        holdings = data["accounts"][0].get("holdings", [])
        total_val = data["accounts"][0].get("total_balance", 0)
        beta_val = calculate_weighted_beta(holdings, total_val)

        return {
            "total_balance": acc_summary.get("total_balance", 0),
            "day_pl": acc_summary.get("day_pl", 0),
            "day_pl_percent": acc_summary.get("day_pl_percent", 0),
            "cash_balance": acc_summary.get("cash_balance", 0),
            "buying_power": acc_summary.get("buying_power", 0),
            "beta": float(beta_val),
            "total_dividends": acc_summary.get("total_dividends", 0),
            "realized_pnl": acc_summary.get("realized_pnl", 0)
        }

    def get_positions(self, account_hash: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取所有持倉
        """
        data = self.get_account_data(account_hash)
        if "error" in data:
            return []
        
        return data["accounts"][0].get("holdings", [])

    def get_history_from_db(self) -> List[Dict[str, Any]]:
        """
        從 SQLite 讀取歷史數據 (目前歷史數據是全帳戶加總，或是今日同步的最後一個帳戶)
        """
        db = SessionLocal()
        try:
            history_records = db.query(AssetHistory).order_by(AssetHistory.date).all()
            if history_records:
                return [{"date": str(r.date), "value": r.total_value} for r in history_records]
            return []
        except Exception as e:
            print(f"Error reading history from DB: {str(e)}")
            return []
        finally:
            db.close()

    def _load_mock_data(self) -> Dict[str, Any]:
        try:
            if not self.mock_file_path.exists():
                return {"error": "Mock file not found"}

            with open(self.mock_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to load mock data: {str(e)}"}

account_repo = AccountRepository()
