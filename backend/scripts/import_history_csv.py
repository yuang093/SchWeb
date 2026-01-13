import os
import sys
import csv
import glob
import re
from datetime import datetime
from pathlib import Path

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.persistence import HistoricalBalance
from app.services.schwab_client import schwab_client

def parse_amount(amount_str):
    """將 '$48,250.05' 轉為 48250.05"""
    if not amount_str:
        return 0.0
    clean_str = str(amount_str).replace('$', '').replace(',', '').strip()
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_date(date_str):
    """將 '1/13/2026' 轉為 date 物件"""
    try:
        # 去除引號
        clean_date = date_str.strip('"')
        return datetime.strptime(clean_date, '%m/%d/%Y').date()
    except ValueError:
        return None

def get_account_mapping():
    """獲獲帳戶 hash 映射"""
    accs = schwab_client.get_linked_accounts()
    mapping = {}
    for acc in accs:
        # 使用最後三碼或四碼作為識別碼
        # 根據檔名範例 XXXX024 -> 024, XXXX323 -> 323
        num_suffix = acc['account_number'][-3:]
        mapping[num_suffix] = acc['hash_value']
        print(f"Mapped suffix {num_suffix} to {acc['hash_value'][:10]}...")
    return mapping

def import_csv_files():
    db = SessionLocal()
    data_dir = Path(__file__).parent.parent / "data"
    # 搜尋包含 Balances 的 CSV
    csv_files = glob.glob(str(data_dir / "*Balances*.CSV"))
    
    if not csv_files:
        print(f"在 {data_dir} 中找不到符合的 CSV 檔案。")
        return

    mapping = get_account_mapping()
    total_count = 0

    try:
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            print(f"\n正在處理檔案: {filename}")
            
            # 決定帳戶 Hash
            account_hash = None
            for suffix, a_hash in mapping.items():
                if suffix in filename:
                    account_hash = a_hash
                    print(f"  匹配到帳戶後綴: {suffix}")
                    break
            
            if not account_hash:
                print(f"  ⚠️ 找不到匹配的帳戶 Hash，跳過。")
                continue

            file_record_count = 0
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_date = row.get('Date')
                    raw_amount = row.get('Amount')
                    
                    if not raw_date or not raw_amount:
                        continue
                    
                    date_obj = parse_date(raw_date)
                    balance = parse_amount(raw_amount)
                    
                    if not date_obj:
                        continue
                    
                    # 寫入資料庫 (Upsert)
                    existing = db.query(HistoricalBalance).filter(
                        HistoricalBalance.date == date_obj,
                        HistoricalBalance.account_id == account_hash
                    ).first()
                    
                    if existing:
                        existing.balance = balance
                    else:
                        new_entry = HistoricalBalance(
                            date=date_obj,
                            account_id=account_hash,
                            balance=balance
                        )
                        db.add(new_entry)
                    
                    file_record_count += 1
            
            print(f"  ✅ 已匯入 {file_record_count} 筆紀錄。")
            total_count += file_record_count
        
        db.commit()
        print(f"\n🎉 匯入完成！總共更新/新增 {total_count} 筆歷史數據。")
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_files()
