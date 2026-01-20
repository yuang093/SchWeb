import requests
import json
import time
from typing import Optional, Tuple
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.persistence import SystemSetting
from app.schemas.token import SchwabToken
from app.utils.auth_utils import get_basic_auth_header

def _get_credentials_from_db() -> Tuple[str, str, str]:
    """
    從資料庫獲取 Schwab 憑證，若無則回退至 settings
    回傳 (api_key, api_secret, redirect_uri)
    """
    db = SessionLocal()
    try:
        setting_key = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_KEY").first()
        api_key = setting_key.value if setting_key else (settings.SCHWAB_API_KEY or settings.SCHWAB_APP_KEY)
        
        setting_secret = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_SECRET").first()
        api_secret = setting_secret.value if setting_secret else (settings.SCHWAB_API_SECRET or settings.SCHWAB_APP_SECRET)
        
        setting_uri = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_REDIRECT_URI").first()
        redirect_uri = setting_uri.value if setting_uri else settings.SCHWAB_REDIRECT_URI
        
        return api_key, api_secret, redirect_uri
    finally:
        db.close()

def fetch_token_from_schwab(code: str) -> dict:
    """
    發送 POST 請求換取 Token
    """
    api_key, api_secret, redirect_uri = _get_credentials_from_db()
    
    url = "https://api.schwab.com/v1/oauth/token"
    headers = {
        "Authorization": get_basic_auth_header(api_key, api_secret),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    # 判斷是否為 REAL 模式，若否則回傳 Mock
    if settings.APP_MODE.upper() != "REAL":
        print("ℹ️ [AUTH] Non-REAL mode, returning mock token.")
        return {
            "access_token": f"mock_access_{int(time.time())}",
            "refresh_token": "mock_refresh_token",
            "expires_in": 1800,
            "token_type": "Bearer",
            "scope": "readonly"
        }

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()

def refresh_schwab_token(refresh_token: str) -> dict:
    """
    使用 Refresh Token 申請新的 Access Token
    """
    api_key, api_secret, _ = _get_credentials_from_db()
    
    url = "https://api.schwab.com/v1/oauth/token"
    headers = {
        "Authorization": get_basic_auth_header(api_key, api_secret),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    if settings.APP_MODE.upper() != "REAL":
        return {
            "access_token": f"mock_refreshed_access_{int(time.time())}",
            "refresh_token": refresh_token,
            "expires_in": 1800,
            "token_type": "Bearer"
        }

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()

class TokenStorage:
    def __init__(self, file_path: str = "tokens.json"):
        self.file_path = file_path

    def save_token(self, token_data: dict):
        token_data["created_at"] = time.time()
        with open(self.file_path, "w") as f:
            json.dump(token_data, f)

    def load_token(self) -> Optional[SchwabToken]:
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                return SchwabToken(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

token_storage = TokenStorage()

def get_valid_token() -> Optional[str]:
    """
    判斷 Token 是否過期並自動刷新
    """
    token = token_storage.load_token()
    if not token:
        return None
    
    # 檢查是否即時過期 (保留 60 秒緩衝)
    if time.time() > (token.created_at + token.expires_in - 60):
        print("Token expired, refreshing...")
        new_data = refresh_schwab_token(token.refresh_token)
        token_storage.save_token(new_data)
        return new_data["access_token"]
    
    return token.access_token
