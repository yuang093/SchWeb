import os
import sys
import pathlib
from pathlib import Path  # [修正1] 補上這行，才能使用 Path()
from dotenv import load_dotenv  # [修正2] 補上這行，才能讀取 .env

# 1. 強制尋找並載入專案根目錄的 .env
# 這樣可以確保程式讀得到 SCHWAB_API_KEY
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent
root_dir = backend_dir.parent  # backend/scripts -> backend -> root
env_path = root_dir / ".env"

print(f"正在讀取設定檔: {env_path}")
load_dotenv(dotenv_path=env_path)

# 2. 將 backend 目錄加入 python path
# 這樣才能 import app.core.config
sys.path.append(str(backend_dir))

# 3. 檢查環境變數 (在 Import settings 之前先檢查，比較好除錯)
api_key = os.getenv("SCHWAB_API_KEY")
api_secret = os.getenv("SCHWAB_API_SECRET")
redirect_uri = os.getenv("SCHWAB_REDIRECT_URI")

print(f"API Key 狀態: {'✅ 已讀取' if api_key else '❌ 未讀取 (請檢查 .env)'}")

# 4. 開始執行授權
import schwab

def run_auth():
    if not api_key or not api_secret or not redirect_uri:
        print("錯誤：請在 .env 中設定 SCHWAB_API_KEY, SCHWAB_API_SECRET, SCHWAB_REDIRECT_URI")
        return

    print("\n🚀 正在啟動 Schwab 授權流程...")
    print("請複製下方的網址，貼到瀏覽器登入，然後將跳轉後的網址貼回來。")
    print("-" * 50)
    
    # 設定 token 儲存位置 (存放在 backend 資料夾下)
    token_path = backend_dir / "token.json"
    
    try:
        # 使用 schwab-py 的手動認證功能
        client = schwab.auth.client_from_manual_flow(
            api_key,
            api_secret,
            redirect_uri,
            str(token_path)
        )
        print("-" * 50)
        print(f"\n🎉 Token 獲取成功！")
        print(f"已儲存至: {token_path}")
        print("現在您可以執行 .\\start_app.ps1 看到真實資產了！")
    except Exception as e:
        print(f"\n❌ 授權失敗：{str(e)}")

if __name__ == "__main__":
    run_auth()