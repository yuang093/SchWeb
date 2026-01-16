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
            val = getattr(app_settings, key, "")
            if val:
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
            continue
            
        # 如果使用者輸入的是遮罩後的字串 (全是 * 或含有 * 且長度跟原本可能不符)，則不更新
        if "*" in value:
            continue

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

@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """
    接收上傳的 CSV 檔案並進行資料匯入
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支援 CSV 檔案格式")
    
    try:
        content = await file.read()
        result = importer_service.process_csv(content, file.filename)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "匯入失敗"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")
