from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance, AssetHistory
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
    聯合查詢 HistoricalBalance (CSV 匯入) 與 AssetHistory (即時同步)，回傳趨勢數據。
    """
    # 1. 取得所有不重複的帳戶 ID (從 HistoricalBalance)
    account_ids = db.query(HistoricalBalance.account_id).distinct().all()
    accounts = [str(a.account_id) for a in account_ids if a.account_id]
    
    # 2. 建立資料容器
    data_by_date = {}

    # 3. 匯入 HistoricalBalance 數據 (優先權高)
    hist_results = db.query(
        HistoricalBalance.date,
        HistoricalBalance.account_id,
        HistoricalBalance.balance
    ).order_by(HistoricalBalance.date.asc()).all()

    for r in hist_results:
        # 強制轉為 YYYY-MM-DD
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        if date_str not in data_by_date:
            data_by_date[date_str] = {"date": date_str, "total": 0.0}
        
        acc_id = str(r.account_id)
        data_by_date[date_str][acc_id] = float(r.balance)
        data_by_date[date_str]["total"] += float(r.balance)

    # 4. 匯入 AssetHistory 數據 (補足沒有 CSV 的日期)
    asset_results = db.query(AssetHistory).order_by(AssetHistory.date.asc()).all()
    for r in asset_results:
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        if date_str not in data_by_date:
            data_by_date[date_str] = {
                "date": date_str,
                "total": float(r.total_value),
                "total_sync": float(r.total_value) # 使用更具體的 Key
            }
        else:
            # 即使當天有 CSV 數據，我們也可以把 Live Sync 的總值存進去供比對
            data_by_date[date_str]["total_sync"] = float(r.total_value)

    # 5. 轉換為列表並按日期排序
    formatted_history = sorted(data_by_date.values(), key=lambda x: x["date"])
    
    all_keys = set()
    if formatted_history:
        all_keys = set(formatted_history[0].keys()) - {"date", "total"}
        print(f"DEBUG: History Data Keys = {all_keys}")
        print(f"DEBUG: Sample Row = {formatted_history[0]}")

    return {
        "history": formatted_history,
        "accounts": list(set(accounts + ["total_sync"]))
    }
