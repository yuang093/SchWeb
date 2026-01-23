from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance, AssetHistory, TransactionHistory
from app.utils.risk import calculate_risk_metrics, calculate_weighted_beta
from typing import List
import datetime
import pandas as pd

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/history")
def get_historical_net_worth(account_hash: str = None, db: Session = Depends(get_db)):
    """
    聯合查詢 HistoricalBalance (CSV 匯入) 與 AssetHistory (即時同步)，回傳趨勢數據。
    支援依 account_hash 過濾。
    """
    # 1. 取得所有不重複的帳戶 ID (從 HistoricalBalance)，用於前端收集 Series
    account_ids_query = db.query(HistoricalBalance.account_id).distinct()
    if account_hash:
        account_ids_query = account_ids_query.filter(HistoricalBalance.account_id == account_hash)
    account_ids = account_ids_query.all()
    accounts = [str(a.account_id) for a in account_ids if a.account_id]
    
    # 2. 建立資料容器
    data_by_date = {}

    # 3. 匯入 HistoricalBalance 數據 (優先權高)
    hist_query = db.query(
        HistoricalBalance.date,
        HistoricalBalance.account_id,
        HistoricalBalance.balance
    )
    if account_hash:
        hist_query = hist_query.filter(HistoricalBalance.account_id == account_hash)
    
    hist_results = hist_query.order_by(HistoricalBalance.date.asc()).all()

    for r in hist_results:
        # 強制轉為 YYYY-MM-DD
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        if date_str not in data_by_date:
            data_by_date[date_str] = {"date": date_str, "total": 0.0}
        
        acc_id = str(r.account_id)
        data_by_date[date_str][acc_id] = float(r.balance)
        data_by_date[date_str]["total"] += float(r.balance)

    # 4. 匯入 AssetHistory 數據 (補足沒有 CSV 的日期)
    # 4. 匯入 AssetHistory 數據 (即時同步數據)
    # 現在 AssetHistory 也有 account_id 了，依據帳戶過濾
    asset_query = db.query(AssetHistory)
    if account_hash:
        asset_query = asset_query.filter(AssetHistory.account_id == account_hash)
    
    asset_results = asset_query.order_by(AssetHistory.date.asc()).all()
    
    for r in asset_results:
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        val = float(r.total_value) if r.total_value is not None else 0.0
        
        # 如果是特定帳戶查詢，AssetHistory 的 account_id 會匹配
        series_key = str(r.account_id) if r.account_id else "total_sync"
        
        if date_str not in data_by_date:
            data_by_date[date_str] = {
                "date": date_str,
                "total": val,
                series_key: val
            }
        else:
            data_by_date[date_str][series_key] = val
            # 優先權：Live 數據優先覆蓋 CSV 數據的 total
            if val > 0:
                data_by_date[date_str]["total"] = val

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

@router.get("/risk-metrics")
def get_risk_analysis(account_hash: str = None, db: Session = Depends(get_db)):
    """
    獲取風險分析指標。
    逻辑：
    1. 抓取完整歷史數據 (與資產走勢圖邏輯相同)
    2. 使用 pandas 計算每日報酬率
    3. 計算年化波動率、夏普比率、最大回撤、VaR
    4. 獲取即時持倉計算 Beta
    """
    from app.services.schwab_client import schwab_client
    
    # --- 1. 抓取歷史序列 (total_value) ---
    data_by_date = {}

    # HistoricalBalance
    hist_query = db.query(HistoricalBalance.date, HistoricalBalance.balance)
    if account_hash:
        hist_query = hist_query.filter(HistoricalBalance.account_id == account_hash)
    hist_results = hist_query.all()
    for r in hist_results:
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        data_by_date[date_str] = float(r.balance)

    # AssetHistory (Live)
    asset_query = db.query(AssetHistory.date, AssetHistory.total_value)
    if account_hash:
        asset_query = asset_query.filter(AssetHistory.account_id == account_hash)
    asset_results = asset_query.all()
    for r in asset_results:
        date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, (datetime.date, datetime.datetime)) else str(r.date)[:10]
        val = float(r.total_value) if r.total_value is not None else 0.0
        # Live 優先覆蓋
        if val > 0:
            data_by_date[date_str] = val

    if not data_by_date:
        return {
            "volatility": 0, "sharpe_ratio": 0, "max_drawdown": 0,
            "annual_return": 0, "beta": 1.0, "var_95": 0,
            "current_value": 0
        }

    # 轉為 DataFrame
    history_list = [{"date": d, "total_value": v} for d, v in data_by_date.items()]
    df_history = pd.DataFrame(history_list)
    
    # --- 1.5 抓取交易紀錄 (用於 TWR 修正) ---
    tx_query = db.query(TransactionHistory)
    if account_hash:
        tx_query = tx_query.filter(TransactionHistory.account_id == account_hash)
    transactions = tx_query.all()

    # --- 2. 呼叫工具函數計算指標 ---
    # 傳送完整的 DataFrame 以支援智慧型模糊對齊 (Smart Flow Alignment)
    vol, sharpe, mdd, var = calculate_risk_metrics(df_history, transactions=transactions)
    
    # 計算年化報酬率 (由夏普比率與波動率反推)
    annual_return = float(sharpe * vol + 0.02)

    metrics = {
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "max_drawdown": mdd,
        "var_95": var,
        "annual_return": annual_return,
        "current_value": float(df_history.sort_values('date')['total_value'].iloc[-1]) if not df_history.empty else 0
    }

    # --- 3. 額外計算 Beta (基於當前持倉) ---
    weighted_beta = 1.0
    try:
        real_data = schwab_client.get_real_account_data(account_hash)
        if "error" not in real_data and real_data.get('accounts'):
            acc_info = real_data['accounts'][0]
            weighted_beta = calculate_weighted_beta(acc_info.get('holdings', []), acc_info.get('total_balance', 0))
    except Exception as e:
        print(f"Error calculating weighted beta: {e}")

    metrics["beta"] = weighted_beta
    
    return metrics
