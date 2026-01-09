from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
import datetime

class AssetHistory(Base):
    """
    紀錄每日總資產歷史
    """
    __tablename__ = "asset_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    daily_profit_loss = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class HoldingSnapshot(Base):
    """
    紀錄每日持股快照
    """
    __tablename__ = "holding_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    name = Column(String)
    quantity = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    cost_basis = Column(Float)
    gain_loss = Column(Float)
    gain_loss_percent = Column(Float)
    industry = Column(String)
    asset_class = Column(String) # e.g., Equity, Cash
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Dividend(Base):
    """
    紀錄股息收入
    """
    __tablename__ = "dividends"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TradeHistory(Base):
    """
    紀錄交易歷史 (買入/賣出)
    """
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False) # 'BUY' or 'SELL'
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    average_cost = Column(Float) # 賣出時的平均成本，用於計算已實現損益
    realized_pnl = Column(Float) # 賣出時產生的損益
    commission = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class HistoricalBalance(Base):
    """
    紀錄從 CSV 匯入的歷史餘額數據
    """
    __tablename__ = "historical_balances"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    account_id = Column(String, index=True, nullable=False)
    balance = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 複合唯一約束在實作時透過 index 或程式邏輯處理，
    # 這裡我們確保 date + account_id 是唯一的。

class SystemSetting(Base):
    """
    系統設定 (Key-Value 存儲)
    """
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
