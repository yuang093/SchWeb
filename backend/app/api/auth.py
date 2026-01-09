from fastapi import APIRouter, Depends
from app.core.config import settings
from app.services.schwab_auth import fetch_token_from_schwab, token_storage
import urllib.parse

router = APIRouter()

@router.get("/login")
def get_login_url():
    """
    產生並回傳 Schwab 授權 URL
    """
    params = {
        "response_type": "code",
        "client_id": settings.SCHWAB_APP_KEY,
        "redirect_uri": settings.SCHWAB_REDIRECT_URI,
        "scope": "readonly",
    }
    base_url = "https://api.schwab.com/v1/oauth/authorize"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"login_url": url}

@router.get("/callback")
def auth_callback(code: str):
    """
    接收授權碼 (code)，自動換 Token 並存檔
    """
    print(f"Received authorization code: {code}")
    try:
        token_data = fetch_token_from_schwab(code)
        token_storage.save_token(token_data)
        return {"message": "登入成功", "token_type": token_data["token_type"]}
    except Exception as e:
        return {"message": "Token 交換失敗", "error": str(e)}
