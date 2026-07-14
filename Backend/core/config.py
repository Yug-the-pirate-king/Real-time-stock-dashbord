"""Centralised application configuration.

Values are read from environment variables (and an optional `.env` file) so the
same code can run locally, in Docker, or on a hosted platform without changes.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    app_name: str = "StockPulse Trading Engine"
    debug: bool = False

    # Database
    database_url: str | None = None

    # API keys (all optional — the app degrades gracefully when missing)
    finnhub_api_key: str = "d87v551r01qmhakhgmd0d87v551r01qmhakhgmdg"
    exchange_rate_api_key: str = ""

    # CORS origins — comma-separated list of allowed frontend URLs
    cors_origins: str = "http://localhost,http://localhost:3000,http://127.0.0.1:3000"

    # Cache TTLs (seconds)
    price_cache_ttl: int = 30
    search_cache_ttl: int = 60
    news_cache_ttl: int = 600
    brief_cache_ttl: int = 300
    alerts_cache_ttl: int = 120
    info_cache_ttl: int = 300
    rate_cache_ttl: int = 3600

    # WebSocket / realtime
    websocket_tick_seconds: float = 5.0
    max_websocket_subscriptions: int = 50

    # Feature flags
    enable_ai_chat: bool = False
    enable_paper_competitions: bool = False
    enable_options: bool = False

    # Paper trading defaults
    starting_balance: float = 100_000.0

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings instance.

    The instance is cached for the process lifetime so env lookups happen once.
    """
    return Settings()
