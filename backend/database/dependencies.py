"""FastAPI dependency injection for database access."""

from typing import Generator
from sqlalchemy.orm import Session

from database.base import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items

    The session is automatically closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
