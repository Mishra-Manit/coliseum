"""
FastAPI dependency injection for database access.

With Beanie ODM, models are accessed directly through the Document classes
rather than through a session dependency. This module provides optional
utilities for dependency injection patterns.
"""

from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings
from database.connection import get_database


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Dependency that yields the MongoDB database instance.

    With Beanie, most operations are done directly on Document classes:
        user = await User.find_one(User.email == "test@example.com")
        await user.save()

    This dependency is provided for cases where direct database access is needed,
    such as raw MongoDB operations or aggregation pipelines.

    Usage in FastAPI routes:
        @router.get("/items")
        async def get_items(db: AsyncIOMotorDatabase = Depends(get_db)):
            # Use db for raw MongoDB operations if needed
            # Or just use Beanie Document classes directly
            pass
    """
    yield get_database()
