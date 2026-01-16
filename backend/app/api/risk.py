from fastapi import APIRouter
from app.services.repository import account_repo
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.risk import get_market_returns, calculate_weighted_beta
from app.core.config import settings

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
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # --- 數據清理 ---
    # 1. 移除異常小的值 (可能是壞數據)
    df = df[df['value'] > 100]
    
    # 2. 處理重複日期
    df = df.groupby('date')['value'].last().reset_index()

    # 優化：處理日期不連續導致的 Volatility 異常
    # 注意：我們只使用有實際變動的日子來計算波動率，
    # 或者我們應該使用工作日 (Business Days) 採樣而非每日 (Daily)，因為週末/假期不交易。
    df = df.set_index('date').resample('B').ffill().reset_index() # 使用 Business Days
    df['date_only'] = df['date'].dt.date
    
    # 計算日報酬率
    df['raw_returns'] = df['value'].pct_change()
    
    # 實作「異常值過濾法」：處理大額轉帳干擾
    # 若單日變動絕對值 > 10%，判定為資金異動，將該日回報設為 0
    df['returns'] = df['raw_returns'].copy()
    df.loc[abs(df['returns']) > 0.10, 'returns'] = 0
    
    # --- 1. 年化波動率 (Volatility) ---
    # 過濾掉 0 報酬率 (無變動或被過濾掉的資金異動)
    actual_returns = df['returns'].dropna()
    actual_returns = actual_returns[actual_returns != 0]
    
    daily_std = actual_returns.std()
    # 若有效數據太少，波動率設為 0
    volatility = daily_std * np.sqrt(252) if not np.isnan(daily_std) and len(actual_returns) > 2 else 0
    
    # --- 2. 最大回撤 (Max Drawdown) ---
    # 重要修正：基於排除資金流干擾後的幾何收益率序列計算 MDD
    max_drawdown = 0
    if not actual_returns.empty:
        # 建立財富指數 (Wealth Index)
        wealth_index = (1 + actual_returns).cumprod()
        # 計算滾動最高點
        previous_peaks = wealth_index.cummax()
        # 計算回撤序列
        drawdown_series = (wealth_index - previous_peaks) / previous_peaks
        max_drawdown = float(drawdown_series.min())

    # --- 3. 年化報酬率 (Annual Return) 與 夏普比率 (Sharpe Ratio) ---
    rf = settings.RISK_FREE_RATE
    annual_return = 0
    try:
        # 取得該帳戶的績效元數據 (從已校正本金的 repository 獲取)
        current_hash = account_hash
        if not current_hash and "accounts" in real_data and real_data["accounts"]:
            current_hash = real_data["accounts"][0].get("account_id")
        
        if current_hash:
            perf_meta = account_repo.get_account_performance_meta(current_hash)
            total_return_val = perf_meta.get("total_return", 0)
            first_date = perf_meta.get("first_transaction_date")
            
            if first_date:
                if isinstance(first_date, str):
                    first_date = datetime.strptime(first_date[:10], "%Y-%m-%d").date()
                
                days_held = (datetime.now().date() - first_date).days
                if days_held >= 365:
                    annual_return = (1 + total_return_val) ** (365 / days_held) - 1
                else:
                    annual_return = total_return_val
    except Exception as e:
        print(f"Error calculating annual return from meta: {e}")
        
    annual_return = max(min(annual_return, 2.0), -0.99)
    sharpe_ratio = (annual_return - rf) / volatility if volatility > 0 else 0

    # --- 4. Beta 係數 (vs SPY) ---
    beta = "N/A"
    try:
        # 固定計算窗口為「過去 1 年」
        end_date = df['date'].max()
        start_date_1y = end_date - timedelta(days=365)
        df_1y = df[df['date'] >= start_date_1y].copy()
        
        spy_returns = get_market_returns(
            start_date_1y.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            df_1y['date_only'].unique()
        )
        
        port_returns_1y = df_1y.set_index('date_only')['returns'].dropna()
        combined = pd.concat([port_returns_1y, spy_returns], axis=1).dropna()
        combined.columns = ['portfolio', 'spy']
        
        if len(combined) >= 20:
            covariance = combined.cov().iloc[0, 1]
            spy_variance = combined['spy'].var()
            reg_beta = float(covariance / spy_variance) if spy_variance > 0 else None
            if reg_beta is not None and 0 < reg_beta < 5:
                beta = reg_beta
            else:
                beta = weighted_beta
        else:
            beta = weighted_beta
    except Exception as e:
        print(f"Error calculating Beta: {str(e)}")
        beta = weighted_beta

    # --- 5. 風險值 VaR (95% 信心水準, 參數法) ---
    # 改用參數法：VaR = Current_Balance * Daily_Volatility * 1.65
    var_95 = 0
    try:
        current_value = float(df['value'].iloc[-1])
        daily_vol = daily_std if not np.isnan(daily_std) else 0
        if daily_vol > 0:
            # 95% Z-score 約為 1.65 (一尾檢定)
            var_95 = current_value * daily_vol * 1.65
            var_95 = -abs(var_95) # 強制為負值表示潛在損失
    except Exception as e:
        print(f"Error calculating VaR: {e}")

    return {
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "annual_return": float(annual_return),
        "beta": beta,
        "var_95": var_95,
        "current_value": float(df['value'].iloc[-1]),
        "benchmark_return": 0.0
    }
