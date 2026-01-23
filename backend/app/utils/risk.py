import pandas as pd
import numpy as np
from datetime import timedelta
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
    
    # 預設一些常用標的的 Beta
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
        
        if "SGOV" in symbol or "SHV" in symbol or "BIL" in symbol or "Cash" in symbol:
            beta = 0.0
            
        portfolio_beta += weight * beta
        total_weight += weight
        
    return portfolio_beta

def calculate_risk_metrics(df_history: pd.DataFrame, transactions: list = None, risk_free_rate: float = 0.02):
    """
    智慧型 TWR 風險計算 (Smart Risk Engine)
    交易紀錄驅動 + 模糊對齊 + 軟性濾網 (Soft Filter)
    """
    if df_history.empty or len(df_history) < 2:
        return 0.0, 0.0, 0.0, 0.0

    # 1. 準備數據並重新採樣為連續工作日
    df = df_history.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    df = df.resample('B').ffill()
    
    # 2. 彙整交易流 (Flows)
    df['daily_flow'] = 0.0
    if transactions:
        FLOW_KEYWORDS = ['Journal', 'Deposit', 'Wire', 'Check', 'Transfer', 'ACH']
        EXCLUDE_KEYWORDS = ['Buy', 'Sell', 'Dividend', 'Reinvest', 'Fee', 'Tax']
        
        tx_data = []
        for t in transactions:
            action = t.action.lower()
            is_flow = any(k.lower() in action for k in FLOW_KEYWORDS)
            is_invest = any(k.lower() in action for k in EXCLUDE_KEYWORDS)
            
            # 排除描述中包含 Div 的 Journal (股息調整)
            desc = (getattr(t, 'description', '') or '').lower()
            if 'journal' in action and 'div' in desc:
                is_flow = False
            
            if is_flow and not is_invest:
                tx_data.append({
                    'date': pd.to_datetime(t.date).date(),
                    'amount': float(t.amount)
                })
        
        if tx_data:
            df_tx = pd.DataFrame(tx_data)
            df_daily_flow = df_tx.groupby('date')['amount'].sum()
            
            # 建立一個副本用於消耗 flow，實現模糊對齊
            remaining_flow = df_daily_flow.copy()
            df['aligned_flow'] = 0.0
            
            # 模糊對齊邏輯：將 Flow 分配給最匹配的餘額跳動日 (T 或 T-1)
            # 這是為了解決嘉信交易紀錄延遲入帳的問題
            df_dates = df.index.date
            for i in range(1, len(df)):
                idx_t = df.index[i]
                date_t = idx_t.date()
                
                # 計算 T 日的原始變動
                raw_change = df.iloc[i]['total_value'] - df.iloc[i-1]['total_value']
                
                # 檢查 T 與 T+1 的 Flow (因為 Transaction 往往晚於 Balance 更新)
                # 注意：這裡我們尋找的是「能解釋 Balance_T 變動」的交易
                flow_t = remaining_flow.get(date_t, 0.0)
                
                # 獲取 T+1 日的日期
                date_next = None
                if i + 1 < len(df):
                    date_next = df.index[i+1].date()
                flow_next = remaining_flow.get(date_next, 0.0) if date_next else 0.0
                
                best_flow = 0.0
                
                # 如果 T 日自有的 Flow 能解釋變動
                if abs(raw_change - flow_t) < abs(raw_change) * 0.5:
                    best_flow += flow_t
                    if date_t in remaining_flow: remaining_flow[date_t] -= flow_t
                
                # 如果 T 日還沒解釋完，且 T+1 有 Flow (入帳延遲)
                if abs(best_flow) < abs(raw_change) * 0.5 and flow_next != 0:
                    if abs(raw_change - (best_flow + flow_next)) < abs(raw_change - best_flow):
                        best_flow += flow_next
                        if date_next in remaining_flow: remaining_flow[date_next] -= flow_next
                
                df.at[idx_t, 'aligned_flow'] = best_flow
    else:
        df['aligned_flow'] = 0.0

    # 3. 計算每日報酬率 (TWR)
    df['returns'] = 0.0
    for i in range(1, len(df)):
        balance_t = df.iloc[i]['total_value']
        balance_prev = df.iloc[i-1]['total_value']
        flow_t = df.iloc[i]['aligned_flow']
        
        if (balance_prev + flow_t) > 0:
            daily_ret = (balance_t - balance_prev - flow_t) / (balance_prev + flow_t)
            
            # 保護機制 (Soft Filter): 
            # 只有在 Flow 為 0 且單日漲跌幅 > 50% 時才視為異常並歸零
            # 10%~30% 的波動對於選擇權帳戶 (Account 2) 是合理的
            if flow_t == 0 and abs(daily_ret) > 0.50:
                daily_ret = 0.0
                
            df.iloc[i, df.columns.get_loc('returns')] = daily_ret

    # 4. 指標計算
    adj_returns = df['returns'].dropna()
    adj_returns = adj_returns[adj_returns != 0] # 排除無交易日
    
    if adj_returns.empty:
        return 0.0, 0.0, 0.0, 0.0

    # 年化波動率
    volatility = float(adj_returns.std() * np.sqrt(252))
    
    # 夏普比率 (Sharpe Ratio)
    daily_rf = risk_free_rate / 252
    mean_ret = adj_returns.mean()
    std_ret = adj_returns.std()
    sharpe_ratio = float(np.sqrt(252) * (mean_ret - daily_rf) / std_ret) if std_ret > 0 else 0.0
    
    # 最大回撤 (MDD)
    equity_curve = (1 + adj_returns).cumprod()
    max_drawdown = float(((equity_curve - equity_curve.cummax()) / equity_curve.cummax()).min())
    
    # VaR (95% 歷史模擬法)
    var_95 = float(np.percentile(adj_returns, 5))

    return volatility, sharpe_ratio, max_drawdown, var_95
