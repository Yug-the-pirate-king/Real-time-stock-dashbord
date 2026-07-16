"""Database setup and lightweight migration runner."""

from logging import getLogger

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import get_settings

logger = getLogger(__name__)
settings = get_settings()

DATABASE_URL = settings.database_url


def _normalize_postgres_url(url: str) -> str:
    """Return a SQLAlchemy-safe PostgreSQL URL.

    Handles the common Supabase pooler format and ensures `sslmode=require`.
    """
    if not isinstance(url, str):
        raise TypeError("Database URL must be a string")
    normalized_url = url.strip()
    if not normalized_url:
        raise ValueError("Database URL cannot be empty")

    if normalized_url.startswith("postgres://"):
        normalized_url = "postgresql://" + normalized_url.removeprefix("postgres://")
    if "sslmode" not in normalized_url:
        query_separator = "&" if "?" in normalized_url else "?"
        normalized_url = f"{normalized_url}{query_separator}sslmode=require"
    return normalized_url


def _create_engine_from_url(url: str | None) -> Engine:
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


_ALLOWED_COLUMN_TYPES = frozenset(
    {"VARCHAR", "FLOAT", "INTEGER", "BOOLEAN", "TEXT", "DATE", "DATETIME", "NUMERIC"}
)


def _is_valid_sql_identifier(name: str) -> bool:
    """Return True if *name* is a safe SQL identifier."""
    if not name or not isinstance(name, str):
        return False
    return all(char.isalnum() or char == "_" for char in name) and not name[0].isdigit()


def _is_valid_column_type(column_type: str) -> bool:
    """Return True if *column_type* is a supported, safe column type."""
    return isinstance(column_type, str) and column_type.upper() in _ALLOWED_COLUMN_TYPES


def _column_exists(table_name: str, column_name: str) -> bool:
    """Return True if a column exists on a table, for SQLite or PostgreSQL."""
    if not _is_valid_sql_identifier(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")
    if not _is_valid_sql_identifier(column_name):
        raise ValueError(f"Invalid column name: {column_name!r}")

    dialect = engine.dialect.name
    with engine.connect() as conn:
        if dialect == "sqlite":
            rows = conn.execute(text(f'PRAGMA table_info("{table_name}")')).fetchall()
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


def _add_column(table_name: str, column_name: str, column_type: str) -> None:
    """Add a column to an existing table."""
    if not _is_valid_sql_identifier(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")
    if not _is_valid_sql_identifier(column_name):
        raise ValueError(f"Invalid column name: {column_name!r}")
    if not _is_valid_column_type(column_type):
        raise ValueError(f"Unsupported column type: {column_type!r}")

    with engine.begin() as conn:
        conn.execute(
            text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}')
        )


def _migrate_portfolio() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("portfolios"):
        return

    columns_to_add = {
        "currency": "VARCHAR",
        "country": "VARCHAR",
        "original_avg_buy_price": "FLOAT",
        "last_exchange_rate": "FLOAT",
        "total_cost_basis_usd": "FLOAT",
        "exchange": "VARCHAR",
        "sector": "VARCHAR",
        "industry": "VARCHAR",
    }
    for column_name, column_type in columns_to_add.items():
        if not _column_exists("portfolios", column_name):
            _add_column("portfolios", column_name, column_type)


def _migrate_transaction_history() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("transaction_history"):
        return

    columns_to_add = {
        "currency": "VARCHAR",
        "country": "VARCHAR",
        "original_price_per_share": "FLOAT",
        "exchange_rate_used": "FLOAT",
        "total_value_usd": "FLOAT",
        "exchange": "VARCHAR",
    }
    for column_name, column_type in columns_to_add.items():
        if not _column_exists("transaction_history", column_name):
            _add_column("transaction_history", column_name, column_type)


def _migrate_options_tables() -> None:
    """Create options tables if they don't exist (SQLite fallback path)."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "option_positions" not in table_names or "options_strategy_records" not in table_names:
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


_CONNECTION_FAILURE_KEYWORDS = (
    "tenant/user",
    "not found",
    "could not connect",
    "connection refused",
    "authentication failed",
    "password authentication",
    "timeout",
)


def init_db() -> None:
    """Create tables and run migrations.

    If a PostgreSQL DATABASE_URL is configured but the server rejects the
    credentials (e.g. Supabase tenant not found), the app logs the error and
    falls back to a local SQLite database so the service can still start.
    """
    try:
        _try_create_tables()
        run_migrations()
    except Exception as exc:
        error_text = str(exc).lower()

        try:
            is_postgres_url = bool(
                DATABASE_URL and "postgresql://" in _normalize_postgres_url(DATABASE_URL)
            )
        except (TypeError, ValueError):
            is_postgres_url = False

        is_connection_failure = any(
            keyword in error_text for keyword in _CONNECTION_FAILURE_KEYWORDS
        )

        if is_postgres_url and is_connection_failure:
            _switch_to_sqlite_fallback(f"PostgreSQL connection failed: {exc}")
            run_migrations()
        else:
            raise