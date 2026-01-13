from fastapi import APIRouter
from app.services.repository import account_repo
import pandas as pd
import numpy as np
from datetime import datetime
from app.utils.risk import get_market_returns, calculate_weighted_beta

router = APIRouter()

@router.get("/metrics")
def get_risk_metrics(account_hash: str = None):
    """
    計算並回傳風險分析指標，包含 Volatility, Sharpe Ratio, Max Drawdown, Beta 與 VaR
    """
    from app.services.schwab_client import schwab_client
    
    # 1. 獲取即時持倉用於計算加權 Beta
    real_data = schwab_client.get_real_account_data(account_hash)
    weighted_beta = 1.0
    if "error" not in real_data:
        acc_info = real_data['accounts'][0]
        weighted_beta = calculate_weighted_beta(acc_info['holdings'], acc_info['total_balance'])

    # 2. 獲取歷史數據用於其他統計指標
    history = account_repo.get_history_from_db()
    
    if not history:
        return {
            "volatility": 0, "sharpe_ratio": 0, "max_drawdown": 0,
            "annual_return": 0, "beta": weighted_beta, "var_95": 0,
            "current_value": real_data.get('accounts', [{}])[0].get('total_balance', 0)
        }
    
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
            reg_beta = float(covariance / spy_variance) if spy_variance > 0 else None
            
            # 如果回歸計算出來的 Beta 太誇張 (例如負數且是 Long Portfolio)，則與加權 Beta 混合或優先使用加權
            if reg_beta is not None and reg_beta > 0:
                beta = reg_beta # 使用回歸 Beta
            else:
                beta = weighted_beta # 使用加權 Beta
        else:
            beta = weighted_beta
    except Exception as e:
        print(f"Error calculating Beta: {str(e)}")
        beta = weighted_beta

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
