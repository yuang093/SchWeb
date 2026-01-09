import os
from pathlib import Path
from dotenv import load_dotenv

# 定位 .env
current_dir = Path.cwd()
env_path = current_dir / ".env"

print(f"🔍 正在檢查路徑: {env_path}")

# 1. 檢查檔案是否存在
if not env_path.exists():
    print("❌ 檔案不存在！程式找不到 .env 檔。")
else:
    print("✅ 檔案存在。")
    
    # 2. 嘗試讀取原始內容
    try:
        content = env_path.read_text(encoding='utf-8')
        print(f"📄 檔案內容預覽 (前 50 字): {content[:50]}...")
    except Exception as e:
        print(f"❌ 讀取失敗 (可能是編碼問題): {e}")

    # 3. 測試 load_dotenv
    loaded = load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"🔧 load_dotenv 回傳值: {loaded}")

    # 4. 檢查變數
    key = os.getenv("SCHWAB_API_KEY")
    print(f"🔑 SCHWAB_API_KEY 讀取結果: {'✅ 成功抓到!' if key else '❌ 還是 None'}")