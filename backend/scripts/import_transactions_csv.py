import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.persistence import Dividend, TradeHistory
from app.services.schwab_client import schwab_client

def parse_amount(amount_str):
    if not amount_str:
        return 0.0
    clean_str = amount_str.replace('$', '').replace(',', '').strip()
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_date(date_str):
    try:
        clean_date = date_str.split(' as of ')[0].strip()
        return datetime.strptime(clean_date, '%m/%d/%Y').date()
    except ValueError:
        return None

def get_account_mapping():
    """獲取帳戶 hash 映射"""
    try:
        accs = schwab_client.get_linked_accounts()
        mapping = {}
        for acc in accs:
            num_suffix = acc['account_number'][-3:]
            mapping[num_suffix] = acc['hash_value']
        return mapping
    except Exception as e:
        print(f"Error getting account mapping: {e}")
        return {"323": "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"} # Fallback for this specific task

def import_transactions_csv(file_path):
    db = SessionLocal()
    mapping = get_account_mapping()
    
    filename = os.path.basename(file_path)
    account_hash = None
    for suffix, a_hash in mapping.items():
        if suffix in filename:
            account_hash = a_hash
            break
    
    if not account_hash:
        # Hardcode fallback for the known file if mapping fails
        if "323" in filename:
             account_hash = "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"
        else:
            print(f"⚠️ 找不到匹配的帳戶 Hash，跳過檔案: {filename}")
            return

    print(f"Using account_hash: {account_hash[:10]}... for {filename}")

    div_keywords = ['qual div reinvest', 'qualified dividend', 'non-qualified div', 'reinvest dividend', 'pr yr div reinvest']
    
    div_count = 0
    trade_count = 0
    skipped_div = 0
    
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                action = row.get('Action', '').strip()
                action_lower = action.lower()
                symbol = row.get('Symbol', 'CASH').strip()
                raw_date = row.get('Date')
                raw_amount = row.get('Amount')
                description = row.get('Description', '').strip()
                
                date_obj = parse_date(raw_date)
                amount = parse_amount(raw_amount)
                
                if not date_obj:
                    continue

                # 股息處理 (正向金額)
                if any(kw in action_lower for kw in div_keywords) and amount > 0:
                    existing = db.query(Dividend).filter(
                        Dividend.account_hash == account_hash,
                        Dividend.date == date_obj,
                        Dividend.symbol == symbol,
                        Dividend.amount == amount
                    ).first()
                    
                    if not existing:
                        db.add(Dividend(
                            account_hash=account_hash,
                            date=date_obj,
                            symbol=symbol,
                            amount=amount,
                            description=f"{action}: {description}"
                        ))
                        div_count += 1
                    else:
                        skipped_div += 1
                
                # 交易處理
                else:
                    side = None
                    if action_lower == 'buy': side = 'BUY'
                    elif action_lower == 'sell': side = 'SELL'
                    elif action_lower == 'reinvest shares': side = 'BUY' # DRIP BUY
                    elif any(kw in action_lower for kw in ['deposit', 'credit interest']): side = 'DEPOSIT'
                    elif action_lower == 'withdrawal': side = 'WITHDRAWAL'
                    
                    if side:
                        qty = abs(parse_amount(row.get('Quantity', '0')))
                        price = abs(parse_amount(row.get('Price', '0')))
                        
                        # 唯一性檢查
                        existing = db.query(TradeHistory).filter(
                            TradeHistory.account_hash == account_hash,
                            TradeHistory.date == date_obj,
                            TradeHistory.symbol == symbol,
                            TradeHistory.side == side,
                            TradeHistory.quantity == qty,
                            TradeHistory.price == (price if price > 0 else 1.0)
                        ).first()
                        
                        if not existing:
                            db.add(TradeHistory(
                                account_hash=account_hash,
                                date=date_obj,
                                symbol=symbol,
                                side=side,
                                quantity=qty if side not in ['DEPOSIT', 'WITHDRAWAL'] else amount,
                                price=price if price > 0 else 1.0,
                                realized_pnl=0.0,
                                description=f"{action}: {description}"
                            ))
                            trade_count += 1

        db.commit()
        msg = f"✅ {filename}: 匯入 {div_count} 筆新股息 (已存在 {skipped_div}), {trade_count} 筆新交易。"
        print(msg)
        with open("import_log.txt", "a", encoding="utf-8") as log:
            log.write(msg + "\n")
    except Exception as e:
        msg = f"❌ {filename} 匯入失敗: {e}"
        print(msg)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent / "data"
    # 處理所有 Transactions CSV
    import glob
    transaction_files = glob.glob(str(data_dir / "*Transactions*.csv"))
    for f in transaction_files:
        import_transactions_csv(f)
