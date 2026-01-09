from sqlalchemy.orm import Session
from app.models.persistence import Dividend, TradeHistory
from sqlalchemy import func

class PNLService:
    @staticmethod
    def calculate_realized_pnl(db: Session):
        """
        計算總已實現損益
        """
        result = db.query(func.sum(TradeHistory.realized_pnl)).scalar()
        return float(result) if result else 0.0

    @staticmethod
    def calculate_total_dividends(db: Session):
        """
        計算總股息收入
        """
        result = db.query(func.sum(Dividend.amount)).scalar()
        return float(result) if result else 0.0

    @staticmethod
    def record_sale(db: Session, symbol: str, quantity: float, price: float, average_cost: float, date=None):
        """
        記錄一筆賣出操作並計算已實現損益
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().date()
            
        realized_pnl = (price - average_cost) * quantity
        
        trade = TradeHistory(
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
