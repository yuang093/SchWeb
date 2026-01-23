import sys
import os

# 將父目錄加入路徑以便載入 app 模組
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance

def clear_history():
    print("🚀 [TOOLS] 正在清除 CSV 匯入的歷史餘額 (HistoricalBalance)...")
    db = SessionLocal()
    try:
        # 執行刪除
        count = db.query(HistoricalBalance).delete()
        db.commit()
        print(f"✅ [TOOLS] 成功清空 historical_balances 表，共刪除 {count} 筆資料。")
        print("ℹ️ [TOOLS] Live 同步的 asset_history 已保留。")
    except Exception as e:
        print(f"❌ [TOOLS] 清除失敗: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_history()
