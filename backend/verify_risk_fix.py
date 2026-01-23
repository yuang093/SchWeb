
import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime

# 確保可以匯入 app 模組
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.database import SessionLocal
from backend.app.api.analytics import get_risk_analysis

def test_risk_api():
    db = SessionLocal()
    try:
        print("Testing Risk API with dynamic calculation...")
        # 測試不帶 account_hash (全部)
        result = get_risk_analysis(account_hash=None, db=db)
        print("\n[Result - All Accounts]")
        for k, v in result.items():
            print(f"{k}: {v}")
            
        # 測試帶 account_hash (如果有的話)
        from backend.app.models.persistence import HistoricalBalance
        first_acc = db.query(HistoricalBalance.account_id).first()
        if first_acc:
            acc_hash = first_acc.account_id
            print(f"\nTesting Risk API for account: {acc_hash}")
            result_acc = get_risk_analysis(account_hash=acc_hash, db=db)
            print(f"[Result - {acc_hash}]")
            for k, v in result_acc.items():
                print(f"{k}: {v}")
        else:
            print("\nNo historical data found to test specific account.")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_risk_api()
