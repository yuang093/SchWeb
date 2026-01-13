from app.services.schwab_client import schwab_client
import json
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

def debug_quotes():
    try:
        client = schwab_client.get_client()
        print(f"DEBUG: Using API Key len {len(schwab_client.api_key)}, Secret len {len(schwab_client.api_secret)}")
        symbols = ["AAPL", "MSFT", "GOOGL", "JNJ"]
        print(f"🔍 Fetching quotes for: {symbols}")
        
        resp = client.get_quotes(symbols)
        if resp.status_code == 200:
            data = resp.json()
            for sym, quote in data.items():
                print(f"\n--- Symbol: {sym} ---")
                # 檢查所有一級鍵
                print(f"Top level keys: {list(quote.keys())}")
                
                # 檢查 fundamental
                fund = quote.get("fundamental", {})
                print(f"Fundamental keys: {list(fund.keys())}")
                if "sector" in fund: print(f"  SECTOR found in fundamental: {fund['sector']}")
                if "industry" in fund: print(f"  INDUSTRY found in fundamental: {fund['industry']}")
                
                # 檢查 reference
                ref = quote.get("reference", {})
                print(f"Reference keys: {list(ref.keys())}")
                if "sector" in ref: print(f"  SECTOR found in reference: {ref['sector']}")
                
                # 檢查 quote
                q = quote.get("quote", {})
                if "sector" in q: print(f"  SECTOR found in quote: {q['sector']}")

            # 嘗試 search_instruments (實際上是 get_instruments)
            print("\n🔍 Testing get_instruments (search) for AAPL")
            # 獲取 Projection 枚舉
            try:
                # Projection 在 schwab.client.base.Instrument.Projection ? 
                # 或者是 client.Instrument.Projection
                proj = client.Instrument.Projection.FUNDAMENTAL
                i_resp = client.get_instruments(["AAPL"], projection=proj)
                if i_resp.status_code == 200:
                    i_data = i_resp.json()
                    # i_data usually contains 'instruments' key or is a list
                    print("Instrument Data Found")
                    print(json.dumps(i_data, indent=2))
                else:
                    print(f"❌ get_instruments failed: {i_resp.status_code} {i_resp.text}")
            except Exception as e:
                print(f"❌ Error during get_instruments: {e}")

        else:
            print(f"❌ get_quotes failed: {resp.status_code} {resp.text}")

    except Exception as e:
        print(f"❌ Error during debug: {e}")

if __name__ == "__main__":
    debug_quotes()
