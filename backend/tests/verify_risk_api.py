import requests
import json

def test_risk_api():
    url = "http://127.0.0.1:8000/api/risk/metrics"
    try:
        # 測試不帶參數
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        
        # 測試帶 account_hash (雖然我們現在後端還沒實作按帳戶過濾歷史，但應該不崩潰)
        resp = requests.get(url, params={"account_hash": "test_hash"})
        print(f"\nWith account_hash Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Beta: {data.get('beta')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 注意：這需要後端正在運行。如果沒運行，我直接在本地呼叫 router 函數測試。
    from fastapi.testclient import TestClient
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from main import app
    
    client = TestClient(app)
    response = client.get("/api/risk/metrics")
    print(f"Status: {response.status_code}")
    print(response.json())
