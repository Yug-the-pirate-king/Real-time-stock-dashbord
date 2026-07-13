"""Compatibility shim — existing imports continue to work while we migrate to `core.db`."""

from core.db import Base, SessionLocal, engine, get_db, init_db, run_migrations

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db", "run_migrations"]
