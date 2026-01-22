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
                "total_sync": float(r.total_value)
            }
        else:
            # 以 Live Sync 的數據為最高優先權，覆蓋 CSV 的加總值
            data_by_date[date_str]["total"] = float(r.total_value)
            data_by_date[date_str]["total_sync"] = float(r.total_value)

    # 5. 轉換為列表並按日期排序
    formatted_history = sorted(data_by_date.values(), key=lambda x: x["date"])
    
    # 6. 收集所有出現過的帳戶 Key (確保前端知道有哪些 Series)
    all_series_keys = set()
    for item in formatted_history:
        keys = set(item.keys()) - {"date", "total"}
        all_series_keys.update(keys)

    print(f"🚀 [ANALYTICS] History merged: {len(formatted_history)} points, Keys: {all_series_keys}")

    return {
        "history": formatted_history,
        "accounts": list(all_series_keys)
    }
