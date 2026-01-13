import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 將 backend 目錄加入 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.schwab_client import schwab_client

def force_import():
    # 支援多個搜尋路徑
    backend_dir = Path(__file__).parent
    root_dir = backend_dir.parent
    
    search_paths = [
        backend_dir / "token.json",
        root_dir / "token.json",
        Path("token.json").absolute(),
        Path("backend/token.json").absolute()
    ]
    
    # 移除重複
    unique_paths = []
    for p in search_paths:
        if p not in unique_paths:
            unique_paths.append(p)

    target_path = None
    for p in unique_paths:
        if p.exists():
            target_path = p
            break
    
    if not target_path:
        print(f"❌ 在以下位置均找不到 token.json：")
        for p in unique_paths:
            print(f"  - {p}")
        return

    print(f"🔍 發現 token.json 於 {target_path}，準備強制匯入...")
    
    try:
        with open(target_path, 'r') as f:
            token_data = json.load(f)
        
        # 驗證格式
        if not isinstance(token_data, dict) or "token" not in token_data:
            print("❌ 檔案內容格式不正確，取消匯入。")
            return

        # 呼叫 schwab_client 的內部方法儲存 Token
        schwab_client._save_token_to_db(token_data)
        print("✅ Token 已成功強制匯入資料庫！")
        
        # 使用專用封存方法
        schwab_client._archive_token_file(target_path)
        
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")

if __name__ == "__main__":
    force_import()
