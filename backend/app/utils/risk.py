import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def get_market_returns(start_date, end_date, dates_index):
    """
    獲取市場 (SPY) 報酬率，若失敗則回傳模擬數據
    """
    try:
        # 嘗試從 yfinance 下載
        # 抓取較寬的時間範圍以確保對齊
        spy_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        spy_end = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 嘗試解決 SSL 問題並增加超時
        spy_data = yf.download("SPY", start=spy_start, end=spy_end, progress=False, timeout=10)
        
        if not spy_data.empty:
            # 統一移除時區並轉為 date 物件
            if spy_data.index.tz is not None:
                spy_data.index = spy_data.index.tz_convert(None).date
            else:
                spy_data.index = spy_data.index.tz_localize(None).date
            
            # 處理可能的多重索引 (MultiIndex)
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_prices = spy_data['Adj Close'].iloc[:, 0]
            else:
                spy_prices = spy_data['Adj Close']
                
            spy_returns = spy_prices.pct_change().dropna()
            
            # 如果成功抓到足夠數據，直接回傳
            if len(spy_returns) >= 5:
                return spy_returns
        
        raise ValueError("Empty or insufficient SPY data from yfinance")

    except Exception as e:
        print(f"WARNING: Failed to download SPY data ({str(e)}). Using simulated market data for fallback.")
        
        # Fallback: 生成模擬大盤數據 (Random Walk)
        # 建立與使用者資產歷史日期完全一致的索引
        np.random.seed(42) # 固定種子確保數值穩定
        simulated_returns = pd.Series(
            np.random.normal(0.0005, 0.01, len(dates_index)), 
            index=dates_index
        )
        return simulated_returns

def calculate_weighted_beta(holdings, total_value):
    """
    計算持倉加權 Beta (Ex-ante Beta)
    """
    if not holdings or total_value <= 0:
        return 1.0
        
    portfolio_beta = 0
    total_weight = 0
    
    # 預設一些常用標的的 Beta (Fallback)
    default_betas = {
        "VOO": 1.0, "SPY": 1.0, "IVV": 1.0,
        "QQQ": 1.18, "IWY": 1.15, "RSP": 1.0,
        "NVDA": 1.67, "TSLA": 2.3, "AAPL": 1.1, 
        "META": 1.2, "GOOG": 1.05, "GOOGL": 1.05,
        "MSFT": 0.9, "TSM": 1.2, "IBIT": 2.5,
        "SGOV": 0.0, "SHV": 0.0, "BIL": 0.0,
        "BRK.B": 0.9, "COST": 0.6
    }
    
    for h in holdings:
        symbol = h.get('symbol', '')
        if h.get('asset_type') == 'OPTION':
            continue
            
        mkt_val = h.get('market_value', 0)
        weight = (mkt_val / total_value)
        
        beta = default_betas.get(symbol, 1.0)
        
        # 現金與國債 ETF Beta 為 0
        if "SGOV" in symbol or "SHV" in symbol or "BIL" in symbol or "Cash" in symbol:
            beta = 0.0
            
        portfolio_beta += weight * beta
        total_weight += weight
        
    return portfolio_beta
