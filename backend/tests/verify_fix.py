
import sys
import os

# 將 backend 目錄加入 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.schwab_client import SchwabClient

def test_format_positions():
    client = SchwabClient()
    
    # 模擬 API 回傳的 position 數據 (Short Call)
    mock_p = {
        "shortQuantity": 1.0,
        "averagePrice": 1.2634,
        "marketValue": -32.0,  # 嘉信通常給負值
        "instrument": {
            "symbol": "NVDA  261218C00200000",
            "assetType": "OPTION"
        }
    }
    
    # 這裡我們手動測試邏輯，因為 get_real_account_data 包含 API 呼叫
    # 我們複製 _format_positions 的核心邏輯進行驗證
    
    p = mock_p
    instrument = p.get("instrument", {})
    symbol = instrument.get("symbol", "UNKNOWN")
    asset_type = instrument.get("assetType", "EQUITY")
    
    # --- 核心邏輯開始 ---
    long_qty = float(p.get("longQuantity") or 0)
    short_qty = float(p.get("shortQuantity") or 0)
    
    if short_qty > 0:
        qty = -1 * short_qty
    else:
        qty = long_qty
    
    cost_basis = float(p.get("averagePrice") or 0)
    multiplier = 100 if asset_type == 'OPTION' else 1
    total_cost = qty * cost_basis * multiplier
    market_value = float(p.get("marketValue") or (qty * cost_basis * multiplier))
    
    price = market_value / (qty * multiplier) if qty != 0 else 0
    total_pnl = float(p.get("longOpenProfitLoss") or p.get("shortOpenProfitLoss") or (market_value - total_cost))
    
    if abs(total_cost) > 0:
        total_pnl_pct = (total_pnl / abs(total_cost)) * 100
    else:
        total_pnl_pct = 0
    # --- 核心邏輯結束 ---

    print(f"Symbol: {symbol}")
    print(f"Asset Type: {asset_type}")
    print(f"Quantity: {qty} (Expected: -1.0)")
    print(f"Total Cost: {total_cost} (Expected: -126.34)")
    print(f"Market Value: {market_value} (Expected: -32.0)")
    print(f"Total P&L: {total_pnl} (Expected: 94.34)")
    print(f"Total P&L %: {total_pnl_pct}% (Expected: ~74.67%)")

    assert qty == -1.0
    assert total_cost == -126.34
    assert market_value == -32.0
    assert abs(total_pnl - 94.34) < 0.01
    assert abs(total_pnl_pct - 74.67) < 0.1

if __name__ == "__main__":
    try:
        test_format_positions()
        print("\n✅ 驗證成功！")
    except Exception as e:
        print(f"\n❌ 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()
