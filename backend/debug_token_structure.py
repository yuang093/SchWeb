from app.services.schwab_client import schwab_client
import json

print("--- 深度偵錯 Token 載入 ---")
try:
    token = schwab_client._load_token_from_db()
    if token:
        print(f"✅ Token 載入成功")
        print(f"型別: {type(token)}")
        print(f"鍵值清單: {list(token.keys())}")
        if "token" in token:
            print(f"內部 Token 鍵值: {list(token['token'].keys())}")
            print(f"Has Refresh Token: {'refresh_token' in token['token']}")
        else:
            print(f"Has Refresh Token: {'refresh_token' in token}")
    else:
        print("❌ 資料庫中找不到 Token")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
