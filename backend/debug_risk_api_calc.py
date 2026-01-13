import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# 加入 backend 目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.repository import account_repo

def get_market_returns_debug(start_date, end_date, dates_index):
    try:
        spy_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        spy_end = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"DEBUG: Downloading SPY from {spy_start} to {spy_end}")
        spy_data = yf.download("SPY", start=spy_start, end=spy_end, progress=False)
        
        if not spy_data.empty:
            if spy_data.index.tz is not None:
                spy_data.index = spy_data.index.tz_convert(None).date
            else:
                spy_data.index = spy_data.index.tz_localize(None).date
            
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_prices = spy_data['Adj Close'].iloc[:, 0]
            else:
                spy_prices = spy_data['Adj Close']
                
            spy_returns = spy_prices.pct_change().dropna()
            return spy_returns
        
        raise ValueError("Empty SPY data")
    except Exception as e:
        print(f"Error downloading SPY: {e}")
        return pd.Series()

def debug_risk_api_calculation():
    print("🔍 偵錯後端 Risk API 的 Beta 計算邏輯...")
    
    # 1. 獲取歷史數據
    history = account_repo.get_history_from_db()
    if not history:
        print("❌ 資料庫中沒有歷史數據")
        return
    
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values('date')
    
    # 計算日報酬率
    df['returns'] = df['value'].pct_change()
    
    print(f"數據點數量: {len(df)}")
    print(f"日期範圍: {df['date'].min()} to {df['date'].max()}")
    
    # 2. 獲取市場數據
    start_date_str = df['date'].min().strftime('%Y-%m-%d')
    end_date_str = df['date'].max().strftime('%Y-%m-%d')
    spy_returns = get_market_returns_debug(start_date_str, end_date_str, df['date'].unique())
    
    if spy_returns.empty:
        print("❌ 無法獲取 SPY 數據")
        return

    # 3. 合併並計算 Beta
    port_returns = df.set_index('date')['returns'].dropna()
    
    # 合併數據
    combined = pd.concat([port_returns, spy_returns], axis=1).dropna()
    combined.columns = ['portfolio', 'spy']
    
    print(f"\n合併後的數據點 (Intersection): {len(combined)}")
    print(combined.tail(10)) # 印出最後 10 筆
    
    if len(combined) >= 2:
        covariance = combined.cov().iloc[0, 1]
        spy_variance = combined['spy'].var()
        beta = float(covariance / spy_variance) if spy_variance > 0 else 0
        
        print(f"\n--- 計算結果 ---")
        print(f"Covariance (Portfolio, SPY): {covariance:.8f}")
        print(f"Variance (SPY): {spy_variance:.8f}")
        print(f"Beta: {beta:.4f}")
        
        correlation = combined.corr().iloc[0, 1]
        print(f"Correlation: {correlation:.4f}")
    else:
        print("❌ 數據點不足，無法計算 Beta")

if __name__ == "__main__":
    debug_risk_api_calculation()
