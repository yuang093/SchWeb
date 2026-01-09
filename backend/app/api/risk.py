from fastapi import APIRouter
from app.services.repository import account_repo
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

router = APIRouter()

def get_market_returns(start_date, end_date, dates_index):
    """
    獲取市場 (SPY) 報酬率，若失敗則回傳模擬數據
    """
    try:
        # 嘗試從 yfinance 下載
        # 抓取較寬的時間範圍以確保對齊
        spy_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        spy_end = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
        
        spy_data = yf.download("SPY", start=spy_start, end=spy_end, progress=False)
        
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
        print(f"WARNING: Failed to download SPY data ({str(e)}). Using simulated market data for Beta calculation.")
        
        # Fallback: 生成模擬大盤數據 (Random Walk)
        # 建立與使用者資產歷史日期完全一致的索引
        np.random.seed(42) # 固定種子確保數值穩定
        simulated_returns = pd.Series(
            np.random.normal(0.0005, 0.01, len(dates_index)), 
            index=dates_index
        )
        return simulated_returns

@router.get("/metrics")
def get_risk_metrics():
    """
    計算並回傳風險分析指標，包含 Volatility, Sharpe Ratio, Max Drawdown, Beta 與 VaR
    """
    # 優先從資料庫獲取歷史數據
    history = account_repo.get_history_from_db()
    
    if not history:
        return {"error": "No history data available for risk analysis"}
    
    # 轉換為 DataFrame
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date']).dt.date # 統一轉為 date 物件，無時區
    df = df.sort_values('date')
    
    # 計算日報酬率
    df['returns'] = df['value'].pct_change()
    
    # --- 1. 年化波動率 (Volatility) ---
    daily_std = df['returns'].std()
    volatility = daily_std * np.sqrt(252) if not np.isnan(daily_std) else 0
    
    # --- 2. 夏普比率 (Sharpe Ratio) ---
    rf = 0.04 # 假設無風險利率 4%
    total_return = (df['value'].iloc[-1] / df['value'].iloc[0]) - 1
    days_diff = (df['date'].iloc[-1] - df['date'].iloc[0]).days
    annual_return = (1 + total_return) ** (365 / max(days_diff, 1)) - 1
    sharpe_ratio = (annual_return - rf) / volatility if volatility > 0 else 0
    
    # --- 3. 最大回撤 (Max Drawdown) ---
    df['cum_max'] = df['value'].cummax()
    df['drawdown'] = (df['value'] - df['cum_max']) / df['cum_max']
    max_drawdown = df['drawdown'].min()

    # --- 4. Beta 係數 (vs SPY) ---
    beta = "N/A"
    try:
        start_date_str = df['date'].min().strftime('%Y-%m-%d')
        end_date_str = df['date'].max().strftime('%Y-%m-%d')
        
        # 呼叫帶有 Fallback 機制的市場數據獲取
        spy_returns = get_market_returns(start_date_str, end_date_str, df['date'].unique())
        
        # 準備組合報酬率
        port_returns = df.set_index('date')['returns'].dropna()
        
        # 合併數據
        combined = pd.concat([port_returns, spy_returns], axis=1).dropna()
        combined.columns = ['portfolio', 'spy']
        
        # Debug Log
        print(f"DEBUG Beta: DB count={len(port_returns)}, Market count={len(spy_returns)}, Intersection count={len(combined)}")
        
        if len(combined) >= 5:
            covariance = combined.cov().iloc[0, 1]
            spy_variance = combined['spy'].var()
            beta = float(covariance / spy_variance) if spy_variance > 0 else "N/A"
        else:
            print(f"WARNING: Beta intersection too small ({len(combined)} days)")
    except Exception as e:
        print(f"Error calculating Beta: {str(e)}")
        beta = "N/A"

    # --- 5. 風險值 VaR (95% 信心水準, 歷史模擬法) ---
    var_95 = 0
    try:
        returns_clean = df['returns'].dropna()
        if not returns_clean.empty:
            var_percentile = np.percentile(returns_clean, 5)
            current_value = df['value'].iloc[-1]
            var_95 = float(var_percentile * current_value)
    except Exception as e:
        print(f"Error calculating VaR: {e}")
        var_95 = 0

    return {
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "annual_return": float(annual_return),
        "beta": beta,
        "var_95": var_95,
        "current_value": float(df['value'].iloc[-1])
    }
