import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Ensure the URL uses the postgresql:// scheme for psycopg2 / SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Append sslmode=require if not already present (required by Supabase)
    if "sslmode" not in DATABASE_URL:
        sep = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,   # detect stale connections automatically
        echo=False,
    )
else:
    # Local fallback file architecture
    SQLALCHEMY_DATABASE_URL = "sqlite:///./simulator.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    run_migrations()


def _sqlite_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a SQLite table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        rows = result.fetchall()
        return any(row[1] == column_name for row in rows)


def run_migrations():
    """ lightweight migration runner: adds columns that are missing from older db files."""
    inspector = inspect(engine)

    # Portfolio migrations
    if inspector.has_table("portfolios"):
        portfolio_cols = [c["name"] for c in inspector.get_columns("portfolios")]
        additions = {
            "currency": "VARCHAR",
            "country": "VARCHAR",
            "original_avg_buy_price": "FLOAT",
            "last_exchange_rate": "FLOAT",
            "total_cost_basis_usd": "FLOAT",
            "exchange": "VARCHAR",
        }
        for col, dtype in additions.items():
            if col not in portfolio_cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE portfolios ADD COLUMN {col} {dtype}"))

    # Transaction history migrations
    if inspector.has_table("transaction_history"):
        txn_cols = [c["name"] for c in inspector.get_columns("transaction_history")]
        additions = {
            "currency": "VARCHAR",
            "country": "VARCHAR",
            "original_price_per_share": "FLOAT",
            "exchange_rate_used": "FLOAT",
            "total_value_usd": "FLOAT",
            "exchange": "VARCHAR",
        }
        for col, dtype in additions.items():
            if col not in txn_cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE transaction_history ADD COLUMN {col} {dtype}"))
