"""
FastAPI dependency injection for database sessions.
Provides database session dependencies for API endpoints.
"""

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from database.base import SessionLocal
from database.session import _get_async_session_factory


def get_db_sync() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a sync database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Usage:
        @app.get("/predictions")
        async def get_predictions(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Prediction))
            predictions = result.scalars().all()
            return predictions

    Yields:
        AsyncSession: SQLAlchemy async database session

    Ensures:
        - Session is automatically closed after the request
        - Exceptions are properly handled
        - Connection is returned to the pool
    """
    factory = _get_async_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()
