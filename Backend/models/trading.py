from sqlalchemy import Column, String, Float, DateTime, ForeignKey, BigInteger
from datetime import datetime
from database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    # Updated to BigInteger to handle 64-bit IDs safely
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    shares_owned = Column(Float, default=0.0)
    average_buy_price = Column(Float, default=0.0)

class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    # Updated to BigInteger to handle 64-bit IDs safely
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    action = Column(String, nullable=False) # "BUY" or "SELL"
    shares = Column(Float, nullable=False)
    price_per_share = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)