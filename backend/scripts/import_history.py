import os
import sys
import csv
import glob
from datetime import datetime
import re

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal, engine, Base
from app.models.persistence import HistoricalBalance

def parse_amount(amount_str):
    """將 '$47,880.64' 轉為 47880.64"""
    if not amount_str:
        return 0.0
    clean_str = amount_str.replace('$', '').replace(',', '').strip()
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_date(date_str):
    """將 '1/5/2026' 轉為 date 物件"""
    try:
        return datetime.strptime(date_str, '%m/%d/%Y').date()
    except ValueError:
        # 嘗試其他可能格式
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None

def extract_account_id(filename):
    """從檔名 (如 MA_XXXX024...) 提取帳戶代碼"""
    basename = os.path.basename(filename)
    # 假設格式為 {ACCOUNT}_Balances_{DATE}.CSV
    match = re.match(r'^([^_]+_[^_]+)', basename)
    if match:
        return match.group(1)
    return basename.split('_')[0]

def import_csv_files():
    # 確保資料表已建立
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    csv_files = glob.glob(os.path.join(data_dir, '*.CSV'))
    
    if not csv_files:
        print(f"在 {data_dir} 中找不到 CSV 檔案。")
        return

    try:
        for file_path in csv_files:
            account_id = extract_account_id(file_path)
            print(f"正在處理檔案: {file_path}, 識別帳戶: {account_id}")
            
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # CSV 欄位名稱可能是 Date, Amount
                    raw_date = row.get('Date')
                    raw_amount = row.get('Amount')
                    
                    if not raw_date or not raw_amount:
                        continue
                        
                    date_obj = parse_date(raw_date)
                    balance = parse_amount(raw_amount)
                    
                    if date_obj is None:
                        continue

                    # 檢查是否已存在
                    existing = db.query(HistoricalBalance).filter(
                        HistoricalBalance.date == date_obj,
                        HistoricalBalance.account_id == account_id
                    ).first()

                    if existing:
                        existing.balance = balance
                    else:
                        new_entry = HistoricalBalance(
                            date=date_obj,
                            account_id=account_id,
                            balance=balance
                        )
                        db.add(new_entry)
                    count += 1
                
                print(f"已從 {os.path.basename(file_path)} 匯入/更新 {count} 筆紀錄。")
        
        db.commit()
        print("匯入完成！")
    except Exception as e:
        print(f"匯入過程中發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_files()
