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
            # 計算本年度 (YTD) 股息與已實現損益
            current_year = datetime.now().year
            start_of_year = datetime(current_year, 1, 1).date()
            
            # 優先使用傳入的 hash，若無則從資料中提取 (相容 REAL 與 MOCK 模式)
            actual_hash = account_hash or acc_summary.get("hash_value") or acc_summary.get("account_id")

            # 股息查詢 (改為全期累計，滿足使用者對「累積股息」的預期)
            div_query = db.query(func.sum(Dividend.amount))
            if actual_hash:
                div_query = div_query.filter(Dividend.account_hash == actual_hash)
            
            total_dividends = div_query.scalar() or 0.0
            acc_summary["total_dividends"] = float(total_dividends)

            # 總報酬 (Total Return) 計算
            # 手動校正項 (處理如 ACAT 移轉或 5 年前的舊本金)
            MANUAL_ADJUSTMENTS = {
                # 帳號 323: TD Ameritrade Legacy Capital (2021-2024)
                '0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991': 47400.37,
                '7681CABBC1C889DACD28A6EF327AF5003CDBE8E4CF801C69F491209D3C8F8AA9': 0.0,
            }

            # 1. 獲取總入金
            deposit_query = db.query(func.sum(TradeHistory.quantity)).filter(TradeHistory.side == 'DEPOSIT')
            if actual_hash:
                deposit_query = deposit_query.filter(TradeHistory.account_hash == actual_hash)
            total_deposits = deposit_query.scalar() or 0.0
            
            # 2. 獲取總出金
            withdrawal_query = db.query(func.sum(TradeHistory.quantity)).filter(TradeHistory.side == 'WITHDRAWAL')
            if actual_hash:
                withdrawal_query = withdrawal_query.filter(TradeHistory.account_hash == actual_hash)
            total_withdrawals = withdrawal_query.scalar() or 0.0
            
            # 加入手動校正項
            adjustment = MANUAL_ADJUSTMENTS.get(actual_hash, 0.0)
            net_invested = total_deposits - total_withdrawals + adjustment
            
            current_net_worth = acc_summary.get("total_balance", 0)
            
            total_return_abs = current_net_worth - net_invested
            total_return_pct = (total_return_abs / net_invested * 100) if net_invested > 0 else 0.0
            
            acc_summary["total_return_abs"] = float(total_return_abs)
            acc_summary["total_return_pct"] = float(total_return_pct)
            
            # 保留 realized_pnl 以防萬一，但前端主要會改用 total_return
            pnl_query = db.query(func.sum(TradeHistory.realized_pnl))
            if actual_hash:
                pnl_query = pnl_query.filter(TradeHistory.account_hash == actual_hash)
            acc_summary["realized_pnl"] = float(pnl_query.scalar() or 0.0)

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
            "realized_pnl": acc_summary.get("realized_pnl", 0),
            "total_return_abs": acc_summary.get("total_return_abs", 0),
            "total_return_pct": acc_summary.get("total_return_pct", 0)
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

    def get_account_performance_meta(self, account_hash: str) -> Dict[str, Any]:
        """
        獲取帳戶績效元數據 (總報酬率與起始日期) 用於風險分析。
        """
        db = SessionLocal()
        try:
            # 1. 獲取最早交易日期
            first_tx = db.query(func.min(TradeHistory.date)).filter(TradeHistory.account_hash == account_hash).scalar()
            
            # 2. 獲取當前總報酬率 (借用現有邏輯)
            summary = self.get_account_summary(account_hash)
            total_return_pct = summary.get("total_return_pct", 0.0) / 100.0 # 轉為小數
            
            return {
                "first_transaction_date": first_tx,
                "total_return": total_return_pct
            }
        except Exception as e:
            print(f"Error getting performance meta: {e}")
            return {"first_transaction_date": None, "total_return": 0.0}
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
