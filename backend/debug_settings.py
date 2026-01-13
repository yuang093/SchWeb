from app.db.database import SessionLocal
from app.models.persistence import SystemSetting

db = SessionLocal()
try:
    settings = db.query(SystemSetting).all()
    print("Database Settings Content:")
    for s in settings:
        # 遮罩顯示以維護隱私
        masked_val = "*" * (len(s.value)-4) + s.value[-4:] if len(s.value) > 4 else "****"
        print(f"{s.key}: {masked_val}")
    
    if not settings:
        print("No settings found in database.")
finally:
    db.close()
