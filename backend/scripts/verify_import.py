import os
import sys

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance
from sqlalchemy import func

def verify_import():
    db = SessionLocal()
    try:
        count = db.query(HistoricalBalance).count()
        print(f"總筆數: {count}")
        
        accounts = db.query(HistoricalBalance.account_id).distinct().all()
        print(f"帳戶列表: {[a[0] for a in accounts]}")
        
        # 檢查 API 邏輯：按日期加總
        results = db.query(
            HistoricalBalance.date,
            func.sum(HistoricalBalance.balance).label("total_balance")
        ).group_by(HistoricalBalance.date).order_by(HistoricalBalance.date.desc()).limit(5).all()
        
        print("\n最近 5 天總資產:")
        for r in results:
            print(f"日期: {r.date}, 總金額: ${r.total_balance:,.2f}")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_import()
