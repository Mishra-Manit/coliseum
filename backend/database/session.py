"""
Database session context managers.
Provides reusable database session management for non-FastAPI contexts.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from config import settings
from database.base import SessionLocal


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in Celery tasks or scripts.

    Usage:
        with get_db_context() as db:
            prediction = db.query(Prediction).filter_by(id=1).first()
            prediction.status = "resolved"
            db.commit()

    Yields:
        Session: SQLAlchemy database session

    Ensures:
        - Session is properly closed even on exceptions
        - Connection is returned to pool
        - Rollback on error
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Async engine and session factory
_async_engine = None
_async_session_factory = None


def _get_async_engine():
    """Get or create async engine."""
    global _async_engine
    if _async_engine is None:
        # Convert sync URL to async
        async_url = settings.database_url.replace(
            "postgresql+psycopg2://",
            "postgresql+asyncpg://"
        )
        _async_engine = create_async_engine(
            async_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _async_engine


def _get_async_session_factory():
    """Get or create async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_async_engine(),
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _async_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions in Celery tasks.

    Usage:
        async with get_db_session() as db:
            result = await db.execute(select(Model))
            await db.commit()

    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    factory = _get_async_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
