import requests
import json
import time
from typing import Optional
from app.core.config import settings
from app.schemas.token import SchwabToken
from app.utils.auth_utils import get_basic_auth_header

def fetch_token_from_schwab(code: str) -> dict:
    """
    發送 POST 請求換取 Token
    """
    url = "https://api.schwab.com/v1/oauth/token" # 範例網址
    headers = {
        "Authorization": get_basic_auth_header(settings.SCHWAB_APP_KEY, settings.SCHWAB_APP_SECRET),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SCHWAB_REDIRECT_URI
    }
    
    # 模擬請求 (實際開發時取消註解)
    # response = requests.post(url, headers=headers, data=payload)
    # response.raise_for_status()
    # return response.json()
    
    # 目前先回傳 Mock 資料以利開發
    return {
        "access_token": f"mock_access_{int(time.time())}",
        "refresh_token": "mock_refresh_token",
        "expires_in": 1800,
        "token_type": "Bearer",
        "scope": "readonly"
    }

def refresh_schwab_token(refresh_token: str) -> dict:
    """
    使用 Refresh Token 申請新的 Access Token
    """
    url = "https://api.schwab.com/v1/oauth/token"
    headers = {
        "Authorization": get_basic_auth_header(settings.SCHWAB_APP_KEY, settings.SCHWAB_APP_SECRET),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    # 模擬回傳
    return {
        "access_token": f"mock_refreshed_access_{int(time.time())}",
        "refresh_token": refresh_token,
        "expires_in": 1800,
        "token_type": "Bearer"
    }

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
