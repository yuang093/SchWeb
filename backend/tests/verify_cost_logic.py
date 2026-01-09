
def test_cost_basis_logic():
    # 模擬資料
    positions = [
        {
            "instrument": {"symbol": "ABBV", "assetType": "EQUITY"},
            "longQuantity": 12.834,
            "averagePrice": 121.94,
            "marketValue": 2132.33,
            "longOpenProfitLoss": 567.27
        },
        {
            "instrument": {"symbol": "SPY", "assetType": "COLLECTIVE_INVESTMENT"},
            "longQuantity": 10,
            "averagePrice": 450.00,
            "marketValue": 4800.00,
            "longOpenProfitLoss": 300.00
        },
        {
            "instrument": {"symbol": "NVDA  261218C00200000", "assetType": "OPTION"},
            "longQuantity": 1,
            "averagePrice": 50.00,
            "marketValue": 6000.00,
            "longOpenProfitLoss": 1000.00
        }
    ]

    holdings = []
    total_account_value = 20000

    for p in positions:
        instrument = p.get("instrument", {})
        symbol = instrument.get("symbol", "UNKNOWN")
        asset_type = instrument.get("assetType", "EQUITY")
        
        long_qty = float(p.get("longQuantity") or 0)
        short_qty = float(p.get("shortQuantity") or 0)
        
        if short_qty > 0:
            qty = -1 * short_qty
        else:
            qty = long_qty
        
        cost_basis = float(p.get("averagePrice") or 0)
        multiplier = 100 if asset_type == 'OPTION' else 1
        
        # 這是我們在代碼中修改的邏輯
        total_cost = qty * cost_basis * multiplier
        market_value = float(p.get("marketValue") or (qty * cost_basis * multiplier))
        price = market_value / (qty * multiplier) if qty != 0 else 0
        total_pnl = float(p.get("longOpenProfitLoss") or p.get("shortOpenProfitLoss") or (market_value - total_cost))
        
        if abs(total_cost) > 0:
            total_pnl_pct = (total_pnl / abs(total_cost)) * 100
        else:
            total_pnl_pct = 0

        # 新邏輯：display_cost_basis
        display_cost_basis = total_cost

        holdings.append({
            "symbol": symbol,
            "qty": qty,
            "total_cost": total_cost,
            "display_cost_basis": display_cost_basis,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct
        })

    # 驗證 ABBV
    abbv = next(h for h in holdings if h["symbol"] == "ABBV")
    print(f"ABBV Display Cost Basis: ${abbv['display_cost_basis']:.2f}")
    print(f"ABBV Total P&L: ${abbv['total_pnl']:.2f}")
    print(f"ABBV P&L %: {abbv['total_pnl_pct']:.2f}%")
    
    assert abs(abbv["display_cost_basis"] - 1565.06) < 0.1
    # 預期 P&L % = (567.27 / 1565.06) * 100 = 36.25%
    assert abs(abbv["total_pnl_pct"] - 36.25) < 0.1

    # 驗證 Option (NVDA)
    nvda = next(h for h in holdings if h["symbol"] == "NVDA  261218C00200000")
    print(f"NVDA Option Display Cost Basis: ${nvda['display_cost_basis']:.2f}")
    assert nvda["display_cost_basis"] == 5000.0  # 50 * 1 * 100

    print("\n✅ 所有邏輯驗證通過！")

if __name__ == "__main__":
    test_cost_basis_logic()
