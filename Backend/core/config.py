"""Centralised application configuration.

Values are read from environment variables (and an optional `.env` file) so the
same code can run locally, in Docker, or on a hosted platform without changes.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration."""

    # Ignore unknown env vars and force UTF-8 encoding when a `.env` file is read.
    # The `.env` file itself is loaded only when it exists (see `__init__`).
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server identity
    app_name: str = Field(default="StockPulse Trading Engine", min_length=1)
    debug: bool = Field(default=False)

    # Database connection string (optional; the app degrades gracefully when unset)
    database_url: str | None = Field(default=None)

    # API keys (optional; the app degrades gracefully when missing)
    finnhub_api_key: str = Field(
        default="d87v551r01qmhakhgmd0d87v551r01qmhakhgmdg"
    )
    exchange_rate_api_key: str = Field(default="")

    # CORS origins stored as a comma-separated string.
    # The validator below strips whitespace and drops empty entries.
    cors_origins: str = Field(
        default=(
            "http://localhost,"
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "https://stock-simulator-predictor.vercel.app"
        )
    )

    # Cache TTLs (seconds). All TTLs must be positive to avoid stale/invalid data.
    price_cache_ttl: int = Field(default=30, gt=0)
    search_cache_ttl: int = Field(default=60, gt=0)
    news_cache_ttl: int = Field(default=600, gt=0)
    brief_cache_ttl: int = Field(default=300, gt=0)
    alerts_cache_ttl: int = Field(default=120, gt=0)
    info_cache_ttl: int = Field(default=300, gt=0)
    rate_cache_ttl: int = Field(default=3600, gt=0)

    # WebSocket / realtime settings
    websocket_tick_seconds: float = Field(default=5.0, gt=0.0)
    max_websocket_subscriptions: int = Field(default=50, ge=0)

    # Feature flags
    enable_ai_chat: bool = Field(default=False)
    enable_paper_competitions: bool = Field(default=False)
    enable_options: bool = Field(default=False)

    # Paper trading defaults (cannot be negative)
    starting_balance: float = Field(default=100_000.0, ge=0.0)

    def __init__(self, **data: Any) -> None:
        """Load `.env` only when it exists, avoiding crashes in env-only deployments.

        If a caller explicitly passes `_env_file`, that value is respected.
        """
        if "_env_file" not in data:
            data["_env_file"] = ".env" if Path(".env").is_file() else None
        super().__init__(**data)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _clean_cors_origins(cls, value: object) -> str:
        """Normalize a comma-separated origin list by trimming and removing empties.

        Also accepts a list of strings for programmatic convenience.
        """
        if value is None:
            return ""

        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
            return ",".join(origins)

        if isinstance(value, list):
            origins = [str(origin).strip() for origin in value if str(origin).strip()]
            return ",".join(origins)

        raise ValueError("cors_origins must be a comma-separated string or a list of strings")

    @field_validator("database_url", mode="before")
    @classmethod
    def _empty_database_url_to_none(cls, value: object) -> str | None:
        """Treat an empty DATABASE_URL env value as unset."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        if not isinstance(value, str):
            raise ValueError("database_url must be a string or unset")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a clean list of non-empty strings."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance.

    The instance is cached for the process lifetime so env lookups happen once.
    """
    return Settings()