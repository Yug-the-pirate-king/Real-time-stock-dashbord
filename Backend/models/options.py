"""Database models for the Options Lab.

Stores paper option positions and strategy records. Real broker integrations
(phase 2) will reference these tables for shadow positions / order tracking.
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, BigInteger, Integer, Text
from core.db import Base


# SQLite requires INTEGER PRIMARY KEY (not BIGINT) for autoincrement behavior.
# We keep the Python field as int; SQLAlchemy will map it correctly per dialect.
PkType = Integer


class OptionPosition(Base):
    """A single option contract held by a user (paper or live)."""

    __tablename__ = "option_positions"

    id = Column(PkType, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # Underlying reference
    underlying = Column(String, nullable=False, index=True)
    expiry = Column(String, nullable=False)          # ISO date, e.g. "2025-07-18"
    strike = Column(Float, nullable=False)
    option_type = Column(String, nullable=False)       # "CE" or "PE"
    side = Column(String, nullable=False)              # "BUY" or "SELL"
    quantity = Column(Integer, nullable=False, default=1)

    # Pricing at time of entry (per contract / lot)
    premium = Column(Float, nullable=False)              # USD per unit
    premium_native = Column(Float, default=0.0)          # Original market currency
    currency = Column(String, default="USD")
    exchange_rate_used = Column(Float, default=1.0)

    # Lot / contract sizing
    lot_size = Column(Integer, default=1)

    # Strategy grouping
    strategy_name = Column(String, default="Single")
    strategy_record_id = Column(BigInteger, nullable=True)
    leg_index = Column(Integer, default=0)

    # Status
    status = Column(String, default="OPEN")              # OPEN / CLOSED
    closed_at = Column(DateTime, nullable=True)
    close_premium = Column(Float, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)


class OptionsStrategyRecord(Base):
    """A saved multi-leg option strategy entered by a user."""

    __tablename__ = "options_strategy_records"

    id = Column(PkType, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    underlying = Column(String, nullable=False)
    expiry = Column(String, nullable=False)

    # JSON snapshot of legs (for display even if individual legs are mutated)
    legs_json = Column(Text, default="[]")

    # Entry metrics
    total_premium = Column(Float, default=0.0)           # Net premium paid/received
    max_profit = Column(Float, nullable=True)
    max_loss = Column(Float, nullable=True)
    breakeven_upper = Column(Float, nullable=True)
    breakeven_lower = Column(Float, nullable=True)

    status = Column(String, default="OPEN")
    timestamp = Column(DateTime, default=datetime.utcnow)
