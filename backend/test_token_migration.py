from app.services.schwab_client import schwab_client
import time

print("--- 測試 SchwabClient 初始化與遷移 ---")
try:
    # 存取 client 會觸發遷移
    client = schwab_client.get_client()
    print("✅ Client 取得成功")
    
    # 檢查資料庫是否有 Token
    from app.db.database import SessionLocal
    from app.models.persistence import SystemSetting
    import json
    
    db = SessionLocal()
    token_setting = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_TOKEN_DATA").first()
    if token_setting:
        print("✅ 資料庫中已存在 Token 數據")
        token_data = json.loads(token_setting.value)
        print(f"Token 類型: {token_data.get('token', {}).get('token_type')}")
        print(f"過期時間: {time.ctime(token_data.get('expires_at'))}")
    else:
        print("❌ 資料庫中找不到 Token 數據")
    db.close()

except Exception as e:
    print(f"❌ 發生錯誤: {e}")
