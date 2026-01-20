from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.persistence import SystemSetting
from app.services.schwab_auth import fetch_token_from_schwab, token_storage
from app.services.schwab_client import schwab_client
import urllib.parse

router = APIRouter()

@router.get("/status")
def get_auth_status():
    """
    回傳當前是否已完成嘉信連線，並進行實時驗證
    """
    try:
        # 1. 先初步檢查資料庫是否有 token
        token_data = schwab_client._load_token_from_db()
        if not token_data:
            return {"authenticated": False}
        
        # 2. 進行實時 API 驗證，確保 token 有效或可自動刷新
        # get_account_numbers() 會觸發 get_client()，進而檢查 token 有效性
        accounts = schwab_client.get_linked_accounts()
        if accounts and len(accounts) > 0:
            return {"authenticated": True}
        
    except Exception as e:
        print(f"⚠️ [AUTH_STATUS] 驗證失敗: {e}")
        
    return {"authenticated": False}

@router.get("/login")
def get_login_url(db: Session = Depends(get_db)):
    """
    產生並回傳 Schwab 授權 URL
    優先從資料庫 SystemSetting 讀取憑證，若無則使用環境變數
    """
    # 讀取 API Key (client_id)
    db_api_key = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_KEY").first()
    # 優先順序：DB > settings.SCHWAB_API_KEY > settings.SCHWAB_APP_KEY
    client_id = db_api_key.value if db_api_key else (settings.SCHWAB_API_KEY or settings.SCHWAB_APP_KEY)
    
    # 讀取 Redirect URI
    db_redirect_uri = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_REDIRECT_URI").first()
    redirect_uri = db_redirect_uri.value if db_redirect_uri else settings.SCHWAB_REDIRECT_URI
    
    # 偵錯日誌
    print(f"🔍 [DEBUG] get_login_url")
    print(f"  - DB Key found: {db_api_key is not None}")
    if db_api_key:
        print(f"  - DB Key value: {db_api_key.value[:4] if db_api_key.value else 'EMPTY'}***")
    print(f"  - Settings.SCHWAB_API_KEY: {settings.SCHWAB_API_KEY[:4] if settings.SCHWAB_API_KEY else 'NONE'}***")
    print(f"  - Settings.SCHWAB_APP_KEY: {settings.SCHWAB_APP_KEY[:4] if settings.SCHWAB_APP_KEY else 'NONE'}***")
    print(f"  - Final client_id: {client_id}")
    print(f"  - Final redirect_uri: {redirect_uri}")

    print(f"🚀 [LOGIN] Generating URL with client_id={client_id[:4] if client_id else 'EMPTY'}***")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "readonly",
    }
    base_url = "https://api.schwab.com/v1/oauth/authorize"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"login_url": url}

@router.get("/callback")
def auth_callback(code: str):
    """
    接收授權碼 (code) 或完整 URL，自動換 Token 並存檔至資料庫
    """
    # 解析邏輯：如果使用者貼入的是完整網址，解析出 code 參數
    actual_code = code
    if "code=" in code:
        try:
            parsed_url = urllib.parse.urlparse(code)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'code' in query_params:
                actual_code = query_params['code'][0]
            elif '?' in code: # 處理沒協定的情況如 "127.0.0.1/?code=..."
                # 簡單正則或分割
                import re
                match = re.search(r'code=([^&]+)', code)
                if match:
                    actual_code = match.group(1)
        except Exception as pe:
            print(f"⚠️ [CALLBACK] URL 解析失敗: {pe}")

    print(f"🚀 [CALLBACK] Processing authorization code: {actual_code[:10]}...")
    
    try:
        # 1. 換取 Token (fetch_token_from_schwab 已修正為讀取 DB 憑證)
        token_data = fetch_token_from_schwab(actual_code)
        
        # 2. 存入資料庫 (統一使用 schwab_client 的儲存邏輯)
        # 注意：schwab_client._save_token_to_db 會處理格式包裝
        schwab_client._save_token_to_db(token_data)
        
        # 3. 強制刷新記憶體中的 Client 實例
        schwab_client.reload_token()
        
        return {"message": "登入成功", "token_type": token_data.get("token_type", "Bearer")}
    except Exception as e:
        print(f"❌ [CALLBACK] Token 交換失敗: {e}")
        return {"message": "Token 交換失敗", "error": str(e)}
