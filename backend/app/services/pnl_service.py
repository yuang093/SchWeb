from sqlalchemy.orm import Session
from app.models.persistence import Dividend, TradeHistory
from sqlalchemy import func

class PNLService:
    @staticmethod
    def calculate_realized_pnl(db: Session, account_hash: str = None, year: int = None):
        """
        計算已實現損益 (可過濾帳戶與年份)
        """
        query = db.query(func.sum(TradeHistory.realized_pnl))
        if account_hash:
            query = query.filter(TradeHistory.account_hash == account_hash)
        if year:
            from datetime import date
            query = query.filter(TradeHistory.date >= date(year, 1, 1))
        
        result = query.scalar()
        return float(result) if result else 0.0

    @staticmethod
    def calculate_total_dividends(db: Session, account_hash: str = None, year: int = None):
        """
        計算總股息收入 (可過濾帳戶與年份)
        """
        query = db.query(func.sum(Dividend.amount))
        if account_hash:
            query = query.filter(Dividend.account_hash == account_hash)
        if year:
            from datetime import date
            query = query.filter(Dividend.date >= date(year, 1, 1))
            
        result = query.scalar()
        return float(result) if result else 0.0

    @staticmethod
    def record_sale(db: Session, account_hash: str, symbol: str, quantity: float, price: float, average_cost: float, date=None):
        """
        記錄一筆賣出操作並計算已實現損益
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().date()
            
        realized_pnl = (price - average_cost) * quantity
        
        trade = TradeHistory(
            account_hash=account_hash,
            date=date,
            symbol=symbol,
            side='SELL',
            quantity=quantity,
            price=price,
            average_cost=average_cost,
            realized_pnl=realized_pnl
        )
        db.add(trade)
        db.commit()
        return trade

pnl_service = PNLService()
