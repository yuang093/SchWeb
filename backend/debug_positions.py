from app.services.schwab_client import schwab_client
import json
import logging

# logging.basicConfig(level=logging.DEBUG)

def debug_positions():
    try:
        # 嘗試直接獲取帳戶持倉
        data = schwab_client.get_real_account_data()
        if "error" in data:
            print(f"❌ Error: {data['error']}")
            return

        # 如果成功，查看持倉
        accounts = data.get("accounts", [])
        if not accounts:
            print("No accounts found")
            return
            
        holdings = accounts[0].get("holdings", [])
        if holdings:
            print(f"Found {len(holdings)} holdings")
            for h in holdings[:3]:
                print(f"Symbol: {h['symbol']}, Sector: {h['sector']}")
        else:
            print("No holdings found")

        # 這裡我們想看原始的 positions 資料，所以我們直接調用 client
        client = schwab_client.get_client()
        accs = schwab_client.get_linked_accounts()
        if not accs:
            print("No linked accounts")
            return
            
        account_hash = accs[0]['hash_value']
        resp = client.get_account(account_hash, fields=client.Account.Fields.POSITIONS)
        if resp.status_code == 200:
            raw_data = resp.json()
            # print(json.dumps(raw_data, indent=2))
            details = raw_data[0] if isinstance(raw_data, list) else raw_data
            positions = details.get("securitiesAccount", {}).get("positions", [])
            if positions:
                print("\n--- Raw Position [0] Instrument ---")
                print(json.dumps(positions[0].get("instrument", {}), indent=2))
                print("\n--- Raw Position [0] Keys ---")
                print(list(positions[0].keys()))
            else:
                print("No raw positions found")
        else:
            print(f"Failed to get raw account data: {resp.status_code} {resp.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_positions()
