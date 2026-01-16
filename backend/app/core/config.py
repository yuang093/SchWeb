import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 1. 定位目錄
# backend/app/core/config.py -> backend/app/core -> backend/app -> backend
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
# 考慮到 .env 可能在 backend/ 目錄或專案根目錄
# 這裡我們優先嘗試 backend/.env
ENV_PATH = BACKEND_DIR / ".env"

print(f"\n🔧 [CONFIG] 正在尋找設定檔: {ENV_PATH}")

# 2. 強制載入
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print("✅ [CONFIG] 設定檔載入成功！")
else:
    # 嘗試上一層目錄 (專案根目錄)
    ROOT_ENV_PATH = BACKEND_DIR.parent / ".env"
    print(f"🔧 [CONFIG] 嘗試尋找根目錄設定檔: {ROOT_ENV_PATH}")
    if ROOT_ENV_PATH.exists():
        load_dotenv(ROOT_ENV_PATH)
        print("✅ [CONFIG] 根目錄設定檔載入成功！")
    else:
        print("⚠️ [CONFIG] 在任何預期位置都找不到 .env 檔案，將使用預設值或系統環境變數。")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Schwab AI Investment Dashboard"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # App Mode (將由環境變數覆蓋)
    APP_MODE: str = "MOCK"
    
    # Schwab OAuth
    SCHWAB_APP_KEY: str = ""
    SCHWAB_APP_SECRET: str = ""
    SCHWAB_REDIRECT_URI: Optional[str] = None
    
    # Schwab API (New Fields)
    SCHWAB_API_KEY: Optional[str] = None
    SCHWAB_API_SECRET: Optional[str] = None
    
    # Demo Mode
    DEMO_MODE: bool = True
    
    # Risk Metrics
    RISK_FREE_RATE: float = 0.04
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"🔥 [CONFIG] 最終生效模式 APP_MODE = {self.APP_MODE}")

    model_config = {
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()
