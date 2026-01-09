from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance
from typing import List
import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/history")
def get_historical_net_worth(db: Session = Depends(get_db)):
    """
    從 HistoricalBalance 撈取資料，回傳寬格式數據與帳戶列表。
    """
    # 1. 取得所有不重複的帳戶 ID
    account_ids = db.query(HistoricalBalance.account_id).distinct().all()
    accounts = [a.account_id for a in account_ids]

    # 2. 取得所有原始數據
    raw_results = db.query(
        HistoricalBalance.date,
        HistoricalBalance.account_id,
        HistoricalBalance.balance
    ).order_by(HistoricalBalance.date.asc()).all()

    # 3. 按日期分組 (Pivot logic)
    data_by_date = {}
    for r in raw_results:
        date_str = r.date.strftime("%Y-%m-%d")
        if date_str not in data_by_date:
            data_by_date[date_str] = {"date": date_str, "total": 0.0}
        
        data_by_date[date_str][r.account_id] = float(r.balance)
        data_by_date[date_str]["total"] += float(r.balance)

    # 4. 轉換為列表並排序
    formatted_history = sorted(data_by_date.values(), key=lambda x: x["date"])

    return {
        "history": formatted_history,
        "accounts": accounts
    }
