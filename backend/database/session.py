"""
Database session context managers.
Provides reusable database session management for non-FastAPI contexts.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
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
