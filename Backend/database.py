"""Compatibility shim — existing imports continue to work while we migrate to `core.db`."""

from __future__ import annotations

from typing import Any

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db", "run_migrations"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        import core.db as _core_db
    except Exception as exc:
        raise ImportError(f"failed to import compatibility target 'core.db': {exc}") from exc
    return getattr(_core_db, name)


def __dir__() -> list[str]:
    return list(__all__)