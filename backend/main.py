from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, account, risk, copilot, analytics, settings as api_settings
from app.core.config import settings
from app.db.database import engine, Base
from app.models.persistence import SystemSetting # 確保模型被載入以自動建立表格

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# 自動建立資料表 (僅限開發環境)
Base.metadata.create_all(bind=engine)

# 模式偵測：如果當前是 MOCK 模式，但資料庫有 Key，則切換到 REAL 模式
if settings.APP_MODE == "MOCK":
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        db_key = db.query(SystemSetting).filter(SystemSetting.key == "SCHWAB_API_KEY").first()
        if db_key and db_key.value:
            print(f"🚀 [CONFIG] Detected API Key in Database. Switching to REAL mode.")
            settings.APP_MODE = "REAL"
    except Exception as e:
        print(f"⚠️ [CONFIG] Failed to check database for settings: {e}")
    finally:
        db.close()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 開發環境允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(account.router, prefix=f"{settings.API_V1_STR}/account", tags=["account"])
app.include_router(risk.router, prefix=f"{settings.API_V1_STR}/risk", tags=["risk"])
app.include_router(copilot.router, prefix=f"{settings.API_V1_STR}/copilot", tags=["copilot"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(api_settings.router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
