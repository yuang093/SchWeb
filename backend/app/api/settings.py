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
            results[key] = ""
            
    return results

@router.post("")
def update_settings(update_data: SettingsUpdate, db: Session = Depends(get_db)):
    for key, value in update_data.settings.items():
        if not value:
            continue
            
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)
            
    db.commit()
    return {"message": "Settings updated successfully"}
