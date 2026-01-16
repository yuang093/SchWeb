import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from app.services.schwab_client import schwab_client

def get_market_returns(start_date, end_date, dates_index=None):
    """
    獲取市場 (SPY) 報酬率。
    優先使用 Schwab API，若失敗則提供中性 Fallback。
    """
    try:
        print(f"DEBUG: Fetching SPY history from Schwab API")
        # 抓取 1 年數據 (預設)
        resp_data = schwab_client.get_price_history("SPY", period_type='year', period=1)
        
        if resp_data and "candles" in resp_data:
            candles = resp_data["candles"]
            if candles:
                # 轉換為 DataFrame
                df_spy = pd.DataFrame(candles)
                # Schwab 回傳的 datetime 是毫秒時間戳
                df_spy['date'] = pd.to_datetime(df_spy['datetime'], unit='ms').dt.date
                df_spy = df_spy.set_index('date')
                
                spy_prices = df_spy['close']
                
                # 轉為每日頻率並填充缺失值（處理市場休市）
                spy_prices.index = pd.to_datetime(spy_prices.index)
                spy_prices = spy_prices.resample('D').ffill()
                
                spy_returns = spy_prices.pct_change().dropna()
                
                # 轉回 date 物件索引以便與資料庫對齊
                spy_returns.index = spy_returns.index.date
                
                if len(spy_returns) >= 2:
                    return spy_returns
        
        raise ValueError("Empty or insufficient SPY data from Schwab API")

    except Exception as e:
        print(f"WARNING: Failed to get SPY from Schwab ({str(e)}). Using fallback.")
        
        # Fallback: 如果有提供 dates_index，則生成 0 報酬率（中性）而不是隨機
        if dates_index is not None and len(dates_index) > 0:
            return pd.Series(0.0, index=dates_index)
        return pd.Series()

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
