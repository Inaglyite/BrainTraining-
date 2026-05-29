"""Compatibility shim — delegates to db_store which supports SQLite and PostgreSQL."""

from app.services.db_store import DBStore as SQLiteStore  # noqa: F401
from app.services.db_store import UserCounters  # noqa: F401
from app.services.db_store import db_store as sqlite_store  # noqa: F401
