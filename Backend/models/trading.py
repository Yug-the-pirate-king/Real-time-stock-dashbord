from sqlalchemy import Column, String, Float, DateTime, ForeignKey, BigInteger
from datetime import datetime
from core.db import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    shares_owned = Column(Float, default=0.0)

    # Core pricing in USD (converted at time of purchase for cost basis)
    average_buy_price = Column(Float, default=0.0)

    # Original market currency tracking
    currency = Column(String, default="USD")
    country = Column(String, default="US")

    # For precise multi-currency P&L tracking
    original_avg_buy_price = Column(Float, default=0.0, nullable=False)
    last_exchange_rate = Column(Float, default=1.0, nullable=False)

    total_cost_basis_usd = Column(Float, default=0.0)
    exchange = Column(String, default="Unknown")
    sector = Column(String, default="")
    industry = Column(String, default="")

class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    action = Column(String, nullable=False) # "BUY" or "SELL"
    shares = Column(Float, nullable=False)
    price_per_share = Column(Float, nullable=False)  # Stored in USD

    # Currency & nation metadata
    currency = Column(String, default="USD")
    country = Column(String, default="US")
    original_price_per_share = Column(Float, nullable=False)  # Price in native currency
    exchange_rate_used = Column(Float, default=1.0)
    total_value_usd = Column(Float, nullable=False)
    exchange = Column(String, default="Unknown")

    timestamp = Column(DateTime, default=datetime.utcnow)
