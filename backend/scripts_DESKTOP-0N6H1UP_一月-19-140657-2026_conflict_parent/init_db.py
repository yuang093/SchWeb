import json
import os
import sys
from datetime import datetime, timedelta
import random

# 將專案根目錄加入 sys.path 以便匯入 backend 模組
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal, engine, Base
from app.models.persistence import AssetHistory, HoldingSnapshot, Dividend, TradeHistory

def init_db():
    # 建立資料表
    print("正在清理舊資料表...")
    Base.metadata.drop_all(bind=engine)
    print("正在建立資料表...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 清除舊數據 (可選，這裡為了確保 Mock Data 一致性)
        # db.query(Dividend).delete()
        # db.query(TradeHistory).delete()

        # 讀取 mock_data/account.json
        mock_data_path = os.path.join(os.path.dirname(__file__), '../mock_data/account.json')
        with open(mock_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        account = data['accounts'][0]
        
        # 1. 寫入歷史數據 (AssetHistory)
        print("正在寫入 AssetHistory (動態日期)...")
        history_count = 0
        mock_history = account['history']
        num_days = len(mock_history)
        today = datetime.now().date()
        
        for i, entry in enumerate(mock_history):
            date_obj = today - timedelta(days=(num_days - 1 - i))
            existing = db.query(AssetHistory).filter(AssetHistory.date == date_obj).first()
            if existing:
                existing.total_value = entry['value']
                existing.cash_balance = account['cash_balance']
            else:
                asset_history = AssetHistory(
                    date=date_obj,
                    total_value=entry['value'],
                    cash_balance=account['cash_balance'],
                    daily_profit_loss=0.0
                )
                db.add(asset_history)
            history_count += 1
        
        # 2. 寫入持倉快照 (HoldingSnapshot)
        print("正在寫入 HoldingSnapshot...")
        holding_count = 0
        for holding in account['holdings']:
            existing = db.query(HoldingSnapshot).filter(
                HoldingSnapshot.date == today,
                HoldingSnapshot.symbol == holding['symbol']
            ).first()
            if not existing:
                snapshot = HoldingSnapshot(
                    date=today,
                    symbol=holding['symbol'],
                    name=holding['name'],
                    quantity=holding['quantity'],
                    market_value=holding['market_value'],
                    cost_basis=holding['average_cost'] * holding['quantity'],
                    gain_loss=holding['unrealized_pl'],
                    gain_loss_percent=holding['return_percent'],
                    industry=holding['sector'],
                    asset_class='Equity'
                )
                db.add(snapshot)
                holding_count += 1

        # 3. 寫入模擬股息 (Dividends)
        print("正在寫入模擬股息紀錄...")
        div_count = 0
        symbols = [h['symbol'] for h in account['holdings']]
        for _ in range(5):
            div_date = today - timedelta(days=random.randint(1, 90))
            symbol = random.choice(symbols)
            # 檢查是否已存在
            existing = db.query(Dividend).filter(Dividend.date == div_date, Dividend.symbol == symbol).first()
            if not existing:
                div = Dividend(
                    account_hash=account.get('hash_value', 'mock_hash_123'),
                    date=div_date,
                    symbol=symbol,
                    amount=round(random.uniform(10, 100), 2),
                    description=f"Cash Dividend from {symbol}"
                )
                db.add(div)
                div_count += 1

        # 4. 寫入模擬交易紀錄 (TradeHistory) 以產生已實現損益
        print("正在寫入模擬已實現損益紀錄...")
        trade_count = 0
        for _ in range(3):
            trade_date = today - timedelta(days=random.randint(5, 60))
            symbol = random.choice(symbols)
            qty = random.randint(10, 50)
            avg_cost = random.uniform(100, 200)
            sell_price = avg_cost + random.uniform(-10, 30) # 有賺有賠
            
            existing = db.query(TradeHistory).filter(TradeHistory.date == trade_date, TradeHistory.symbol == symbol).first()
            if not existing:
                trade = TradeHistory(
                    account_hash=account.get('hash_value', 'mock_hash_123'),
                    date=trade_date,
                    symbol=symbol,
                    side='SELL',
                    quantity=float(qty),
                    price=float(sell_price),
                    average_cost=float(avg_cost),
                    realized_pnl=float((sell_price - avg_cost) * qty)
                )
                db.add(trade)
                trade_count += 1

        db.commit()
        print(f"資料初始化完成！歷史:{history_count}, 持倉:{holding_count}, 股息:{div_count}, 交易:{trade_count}")

    except Exception as e:
        print(f"發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
