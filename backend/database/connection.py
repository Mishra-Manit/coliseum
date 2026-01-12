"""PostgreSQL connection management for Neon."""

from sqlalchemy import text

from config import settings
from database.base import engine, SessionLocal

# Global initialization flag
_initialized = False


async def init_db() -> None:
    """Initialize database connection and verify connectivity."""
    global _initialized

    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _initialized = True
    except Exception as e:
        raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")


async def close_db() -> None:
    """Close database connections."""
    global _initialized
    engine.dispose()
    _initialized = False


def get_db() -> SessionLocal:
    """Get database session. Used as FastAPI dependency."""
    if not _initialized:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionLocal()


async def check_db_connection() -> bool:
    """Check if PostgreSQL connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_db_info() -> dict:
    """Get database connection information."""
    # Sanitize URL to hide credentials
    sanitized_url = settings.database_url
    if settings.db_password:
        sanitized_url = sanitized_url.replace(
            f":{settings.db_password}@", ":***@"
        )

    return {
        "status": "connected" if _initialized else "disconnected",
        "url": sanitized_url,
        "database": settings.db_name,
        "environment": settings.environment,
    }
