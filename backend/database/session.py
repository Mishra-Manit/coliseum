"""
Database session context managers for use in Celery tasks and other async contexts.

With Beanie ODM, we don't need traditional database sessions like SQLAlchemy.
Beanie operates directly on Document classes after initialization.

However, for Celery tasks that run in separate processes, we need to ensure
the database connection is initialized before performing operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorDatabase

from database.connection import init_db, close_db, get_database, _client


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Async context manager for database access in Celery tasks.

    Ensures database connection is initialized and provides access to the database.
    For Celery tasks running in separate processes, this handles initialization.

    Usage in Celery tasks:
        @celery_app.task
        def my_task():
            import asyncio

            async def _run():
                async with get_db_session() as db:
                    # Beanie operations work here
                    user = await User.find_one(User.email == "test@example.com")
                    await user.save()

            return asyncio.run(_run())

    Note: With Beanie, most operations don't need the db object directly.
    The context manager ensures Beanie is initialized, then you can use
    Document classes directly.
    """
    # Initialize if not already done (handles Celery worker processes)
    if _client is None:
        await init_db()

    try:
        yield get_database()
    finally:
        # Don't close in context manager - connection is shared
        # Connection is closed on application shutdown
        pass
