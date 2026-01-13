import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.schwab_client import schwab_client

def check_quote_structure():
    client = schwab_client.get_client()
    symbol = "VOO"
    resp = client.get_quotes([symbol])
    if resp.status_code == 200:
        data = resp.json()
        print(f"--- {symbol} Quote Structure ---")
        print(json.dumps(data.get(symbol, {}), indent=2))
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    check_quote_structure()
