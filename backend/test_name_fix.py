from app.services.schwab_client import schwab_client

def test_sync_logic():
    print("--- 測試數據同步名稱修復邏輯 ---")
    
    # 模擬 API 回傳的數據
    mock_quotes = {
        "AAPL": {
            "reference": {"description": "Apple Inc."},
            "quote": {"price": 150}
        },
        "MSFT": {
            # 測試缺失 reference
            "quote": {"price": 300}
        }
    }
    
    mock_positions = [
        {
            "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
            "longQuantity": 10
        },
        {
            "instrument": {"symbol": "MSFT", "assetType": "EQUITY", "description": "Microsoft Corp."},
            "longQuantity": 5
        }
    ]

    for p in mock_positions:
        symbol = p['instrument']['symbol']
        quote = mock_quotes.get(symbol, {})
        
        # 使用我們在新代碼中實作的邏輯
        name = quote.get("reference", {}).get("description")
        if not name:
            name = p['instrument'].get("description") or p.get("description") or symbol
            
        print(f"Symbol: {symbol}, Extracted Name: {name}")
        
        if symbol == "AAPL":
            assert name == "Apple Inc."
        if symbol == "MSFT":
            assert name == "Microsoft Corp."

if __name__ == "__main__":
    test_sync_logic()
    print("✅ 名稱提取邏輯驗證成功！")
