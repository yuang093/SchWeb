
import sys
import os

# 將 backend 目錄加入 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_new_logic():
    # 模擬股票數據 (Day Chg % 遺失情況)
    mock_p = {
        "longQuantity": 10.0,
        "averagePrice": 150.0,
        "marketValue": 2000.0,
        "currentDayProfitLoss": 20.0, # 當日漲了 20 元
        "yearToDateProfitLossPercent": 0, # API 給 0
        "instrument": {
            "symbol": "AAPL",
            "assetType": "EQUITY",
            "high52Week": 210.0
        }
    }
    
    p = mock_p
    instrument = p.get("instrument", {})
    symbol = instrument.get("symbol", "UNKNOWN")
    asset_type = instrument.get("assetType", "EQUITY")
    
    # --- 複製實作成員方法中的邏輯 ---
    long_qty = float(p.get("longQuantity") or 0)
    short_qty = float(p.get("shortQuantity") or 0)
    qty = -1 * short_qty if short_qty > 0 else long_qty
    cost_basis = float(p.get("averagePrice") or 0)
    multiplier = 100 if asset_type == 'OPTION' else 1
    total_cost = qty * cost_basis * multiplier
    market_value = float(p.get("marketValue") or (qty * cost_basis * multiplier))
    price = market_value / (qty * multiplier) if qty != 0 else 0
    
    day_pnl = float(p.get("currentDayProfitLoss") or 0)
    day_pnl_pct = p.get("currentDayProfitLossPercentage")
    if day_pnl_pct is not None:
        day_pnl_pct = float(day_pnl_pct)
    
    # Fallback Logic
    if (day_pnl_pct is None or day_pnl_pct == 0) and day_pnl != 0:
        start_value = market_value - day_pnl
        if start_value != 0:
            day_pnl_pct = (day_pnl / abs(start_value)) * 100
        else:
            day_pnl_pct = 0
    elif day_pnl_pct is None:
        day_pnl_pct = 0
        
    # YTD Logic
    raw_ytd = p.get("yearToDateProfitLossPercent")
    if raw_ytd is None or float(raw_ytd) == 0:
        ytd_pnl_pct = None
    else:
        ytd_pnl_pct = float(raw_ytd)
        
    # 52WeekHigh Logic
    market_data = p.get("marketData", {})
    quote = p.get("quote", {})
    high_52week = (
        instrument.get("high52Week") or 
        p.get("high52Week") or 
        market_data.get("high52Week") or 
        quote.get("high52Week") or
        instrument.get("52WeekHigh") or
        market_data.get("52WeekHigh")
    )
    # --- 邏輯結束 ---

    print(f"Symbol: {symbol}")
    print(f"Price: {price}")
    print(f"Day P&L: {day_pnl}")
    print(f"Calculated Day Chg %: {day_pnl_pct}%")
    print(f"YTD P&L %: {ytd_pnl_pct}")
    print(f"52Week High: {high_52week}")

    # 驗證
    # start_value = 2000 - 20 = 1980
    # day_pnl_pct = (20 / 1980) * 100 = 1.0101...
    assert abs(day_pnl_pct - 1.0101) < 0.001
    assert ytd_pnl_pct is None
    assert high_52week == 210.0
    assert multiplier == 1

if __name__ == "__main__":
    test_new_logic()
    print("\n✅ 邏輯驗證成功！")
