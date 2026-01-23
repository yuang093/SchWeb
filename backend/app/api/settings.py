from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
from app.db.database import get_db
from app.models.persistence import SystemSetting

router = APIRouter(tags=["settings"])

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]

def mask_value(value: str) -> str:
    if not value or len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    keys = ["SCHWAB_API_KEY", "SCHWAB_API_SECRET", "SCHWAB_REDIRECT_URI"]
    results = {}
    
    for key in keys:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            # 對於 Key 和 Secret 進行遮罩
            if key in ["SCHWAB_API_KEY", "SCHWAB_API_SECRET"]:
                results[key] = mask_value(setting.value)
            else:
                results[key] = setting.value
        else:
            # 嘗試從環境變數讀取（僅作為 fallback）
            from app.core.config import settings as app_settings
            # 注意：這裡同時檢查 SCHWAB_API_XXX 和 SCHWAB_APP_XXX
            val = getattr(app_settings, key, None)
            if val is None and key == "SCHWAB_API_KEY": val = app_settings.SCHWAB_APP_KEY
            if val is None and key == "SCHWAB_API_SECRET": val = app_settings.SCHWAB_APP_SECRET
            
            if val:
                # 自動遷移到資料庫，以便後續管理
                print(f"🚀 [SETTINGS] Migrating {key} from environment to Database")
                new_setting = SystemSetting(key=key, value=val)
                db.add(new_setting)
                db.commit()
                
                if key in ["SCHWAB_API_KEY", "SCHWAB_API_SECRET"]:
                    results[key] = mask_value(val)
                else:
                    results[key] = val
            else:
                results[key] = ""
            
    print(f"🚀 [DEBUG] Returning settings to frontend: {results}")
    return results

@router.post("")
def update_settings(update_data: SettingsUpdate, db: Session = Depends(get_db)):
    for key, value in update_data.settings.items():
        if not value:
            print(f"🔍 [DEBUG] Skipping empty value for key: {key}")
            continue
            
        # 如果使用者輸入的是遮罩後的字串 (全是 * 或含有 * 且長度跟原本可能不符)，則不更新
        if "*" in value:
            print(f"🔍 [DEBUG] Skipping masked value for key: {key}")
            continue

        print(f"🔍 [DEBUG] Updating key: {key} with value: {value[:4]}***")
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)
            
    db.commit()
    print(f"🚀 [DEBUG] Settings updated in DB: {list(update_data.settings.keys())}")
    
    # 強制重整 SchwabClient
    from app.services.schwab_client import schwab_client
    schwab_client._refresh_config()
    
    return {"message": "Settings updated successfully"}

from fastapi import UploadFile, File
from app.services.importer import importer_service

from fastapi import Form

@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    account_hash: str = Form(...)
):
    """
    接收上傳的 CSV 檔案與目標帳戶 Hash，並進行資料匯入
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支援 CSV 檔案格式")
    
    try:
        content = await file.read()
        # 現在將 account_hash 直接傳入，不再讓 importer 猜測
        result = importer_service.process_csv(content, file.filename, account_hash)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "匯入失敗"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")

@router.delete("/reset-history")
def reset_history(db: Session = Depends(get_db)):
    """
    危險操作：清空並重建資產歷史相關資料表 (Live & CSV)
    這也解決了 Schema 變更後的遷移問題。
    """
    try:
        from app.models.persistence import AssetHistory, HistoricalBalance
        from app.db.database import engine, Base
        
        # 1. 直接刪除表格以確保 Schema 更新
        AssetHistory.__table__.drop(engine, checkfirst=True)
        HistoricalBalance.__table__.drop(engine, checkfirst=True)
        
        # 2. 重新建立表格
        Base.metadata.create_all(bind=engine)
        
        print(f"🔥 [SYSTEM] History tables dropped and recreated to apply new schema.")
        return {
            "success": True,
            "message": "成功清空歷史資料並重置資料表結構。"
        }
    except Exception as e:
        db.rollback()
        print(f"❌ [SYSTEM] History reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"清空失敗: {str(e)}")
