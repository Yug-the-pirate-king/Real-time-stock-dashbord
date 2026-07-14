"""Database setup and lightweight migration runner."""

from logging import getLogger

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import get_settings

logger = getLogger(__name__)
settings = get_settings()

DATABASE_URL = settings.database_url


def _normalize_postgres_url(url: str) -> str:
    """Return a SQLAlchemy-safe PostgreSQL URL.

    Handles the common Supabase pooler format and ensures `sslmode=require`.
    """
    fixed = url
    if fixed.startswith("postgres://"):
        fixed = fixed.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in fixed:
        sep = "&" if "?" in fixed else "?"
        fixed = f"{fixed}{sep}sslmode=require"
    return fixed


def _create_engine_from_url(url: str | None) -> object:
    """Create a SQLAlchemy engine from a database URL.

    Returns a PostgreSQL engine when a URL is provided, otherwise a local
    SQLite database.  The caller is responsible for handling connection errors.
    """
    if url:
        fixed_url = _normalize_postgres_url(url)
        return create_engine(fixed_url, pool_pre_ping=True, echo=settings.debug)

    return create_engine(
        "sqlite:///./simulator.db",
        connect_args={"check_same_thread": False},
    )


engine = _create_engine_from_url(DATABASE_URL)

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
    """Return True if a column exists on a table, for SQLite or PostgreSQL."""
    dialect = engine.dialect.name
    with engine.connect() as conn:
        if dialect == "sqlite":
            rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            return any(row[1] == column_name for row in rows)

        # PostgreSQL path
        result = conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :table_name AND column_name = :column_name"
            ),
            {"table_name": table_name, "column_name": column_name},
        ).fetchone()
        return result is not None


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
            logger.warning(f"Options table creation skipped: {exc}")


def run_migrations() -> None:
    """Run forward-only lightweight migrations."""
    _migrate_portfolio()
    _migrate_transaction_history()
    _migrate_options_tables()


def _try_create_tables() -> None:
    """Create all mapped tables; raises on connection failure."""
    Base.metadata.create_all(bind=engine)


def _switch_to_sqlite_fallback(reason: str) -> None:
    """Reconfigure the global engine/session to use local SQLite."""
    global engine, SessionLocal
    logger.warning(f"{reason} Falling back to local SQLite.")
    engine.dispose(close=True)
    engine = create_engine(
        "sqlite:///./simulator.db",
        connect_args={"check_same_thread": False},
    )
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)


def init_db() -> None:
    """Create tables and run migrations.

    If a PostgreSQL DATABASE_URL is configured but the server rejects the
    credentials (e.g. Supabase tenant not found), the app logs the error and
    falls back to a local SQLite database so the service can still start.
    """
    try:
        _try_create_tables()
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        error_text = str(exc).lower()
        is_postgres_url = bool(DATABASE_URL and "postgresql://" in _normalize_postgres_url(DATABASE_URL))
        is_connection_failure = any(
            keyword in error_text
            for keyword in [
                "tenant/user",
                "not found",
                "could not connect",
                "connection refused",
                "authentication failed",
                "password authentication",
                "timeout",
            ]
        )

        if is_postgres_url and is_connection_failure:
            _switch_to_sqlite_fallback(f"PostgreSQL connection failed: {exc}")
            run_migrations()
        else:
            raise
