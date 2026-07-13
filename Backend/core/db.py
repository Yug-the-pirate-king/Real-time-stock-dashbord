"""Database setup and lightweight migration runner."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url

if DATABASE_URL:
    # SQLAlchemy requires `postgresql://`, not `postgres://`.
    fixed_url = DATABASE_URL
    if fixed_url.startswith("postgres://"):
        fixed_url = fixed_url.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in fixed_url:
        sep = "&" if "?" in fixed_url else "?"
        fixed_url = f"{fixed_url}{sep}sslmode=require"

    engine = create_engine(fixed_url, pool_pre_ping=True, echo=settings.debug)
else:
    # Local SQLite fallback — used by default Docker setup.
    engine = create_engine(
        "sqlite:///./simulator.db",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _column_exists(table_name: str, column_name: str) -> bool:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return any(row[1] == column_name for row in rows)


def _add_column(table_name: str, column_name: str, dtype: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {dtype}"))


def _migrate_portfolio() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("portfolios"):
        return

    additions = {
        "currency": "VARCHAR",
        "country": "VARCHAR",
        "original_avg_buy_price": "FLOAT",
        "last_exchange_rate": "FLOAT",
        "total_cost_basis_usd": "FLOAT",
        "exchange": "VARCHAR",
        "sector": "VARCHAR",
        "industry": "VARCHAR",
    }
    for col, dtype in additions.items():
        if not _column_exists("portfolios", col):
            _add_column("portfolios", col, dtype)


def _migrate_transaction_history() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("transaction_history"):
        return

    additions = {
        "currency": "VARCHAR",
        "country": "VARCHAR",
        "original_price_per_share": "FLOAT",
        "exchange_rate_used": "FLOAT",
        "total_value_usd": "FLOAT",
        "exchange": "VARCHAR",
    }
    for col, dtype in additions.items():
        if not _column_exists("transaction_history", col):
            _add_column("transaction_history", col, dtype)


def _migrate_options_tables() -> None:
    """Create options tables if they don't exist (SQLite fallback path)."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "option_positions" not in tables or "options_strategy_records" not in tables:
        try:
            from models.options import OptionPosition, OptionsStrategyRecord  # noqa: F401
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger = getLogger(__name__)
            logger.warning(f"Options table creation skipped: {exc}")


def run_migrations() -> None:
    """Run forward-only lightweight migrations."""
    _migrate_portfolio()
    _migrate_transaction_history()
    _migrate_options_tables()


def init_db() -> None:
    """Create tables and run migrations."""
    Base.metadata.create_all(bind=engine)
    run_migrations()
