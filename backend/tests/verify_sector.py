
import sys
import os

# 將 backend 目錄加入 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_sector_logic():
    print("--- 測試 Sector 獲取邏輯 ---")
    
    # 模擬資料 1: 有 fundamental.sector (新報價格式)
    symbol_quote_1 = {
        "fundamental": {"sector": "Technology"},
        "quote": {"price": 100}
    }
    
    # 模擬資料 2: 有 quote.sector
    symbol_quote_2 = {
        "quote": {"sector": "Financials", "price": 150}
    }
    
    # 模擬資料 3: 只有 position 裡的 sector
    symbol_quote_3 = {}
    p_3 = {"sector": "Energy"}
    
    # 模擬資料 4: 只有 instrument 裡的 sector
    symbol_quote_4 = {}
    p_4 = {"instrument": {"sector": "Healthcare"}}
    
    # 模擬資料 5: 全空
    symbol_quote_5 = {}
    p_5 = {}

    def get_sector(symbol_quote, p):
        sector = symbol_quote.get("fundamental", {}).get("sector")
        if not sector:
            sector = symbol_quote.get("quote", {}).get("sector")
        if not sector:
            instrument = p.get("instrument", {})
            sector = p.get("sector") or instrument.get("sector") or "Other"
        return sector

    s1 = get_sector(symbol_quote_1, {})
    s2 = get_sector(symbol_quote_2, {})
    s3 = get_sector(symbol_quote_3, p_3)
    s4 = get_sector(symbol_quote_4, p_4)
    s5 = get_sector(symbol_quote_5, p_5)

    print(f"S1: {s1} (Expected: Technology)")
    print(f"S2: {s2} (Expected: Financials)")
    print(f"S3: {s3} (Expected: Energy)")
    print(f"S4: {s4} (Expected: Healthcare)")
    print(f"S5: {s5} (Expected: Other)")

    assert s1 == "Technology"
    assert s2 == "Financials"
    assert s3 == "Energy"
    assert s4 == "Healthcare"
    assert s5 == "Other"

if __name__ == "__main__":
    test_sector_logic()
    print("\n✅ Sector 邏輯驗證成功！")
