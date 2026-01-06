"""
Database module initialization.
Exports database components for use throughout the application.
"""

from database.connection import (
    init_db,
    close_db,
    get_client,
    get_database,
    check_db_connection,
    get_db_info,
)
from database.dependencies import get_db
from database.session import get_db_session
from database.base import BaseDocument, TimestampMixin

__all__ = [
    # Connection management
    "init_db",
    "close_db",
    "get_client",
    "get_database",
    # Dependencies
    "get_db",
    "get_db_session",
    # Base classes
    "BaseDocument",
    "TimestampMixin",
    # Utilities
    "check_db_connection",
    "get_db_info",
]
