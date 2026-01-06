"""
MongoDB connection and Beanie ODM initialization.

This module provides:
- MongoDB client connection via Motor (async driver)
- Beanie ODM initialization
- Health check utilities
"""

from typing import Optional, List, Type

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError

from config import settings

# Global MongoDB client instance
_client: Optional[AsyncIOMotorClient] = None

# Document models will be imported and registered during init_db()
# This avoids circular imports
_document_models: List[Type[Document]] = []


def register_models(models: List[Type[Document]]) -> None:
    """
    Register document models for Beanie initialization.
    """
    global _document_models
    _document_models = models


async def init_db() -> None:
    """
    Initialize MongoDB connection and Beanie ODM.
    Document models are registered via register_models() before this is called.
    """
    global _client

    _client = AsyncIOMotorClient(settings.mongodb_url)

    # Import models here to get the registered list
    # This import triggers models/__init__.py which calls register_models()
    from models import get_document_models

    await init_beanie(
        database=_client[settings.mongodb_database],
        document_models=get_document_models(),
    )


async def close_db() -> None:
    """
    Close MongoDB connection.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_client() -> AsyncIOMotorClient:
    """
    Get the MongoDB client instance.
    """
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.
    """
    return get_client()[settings.mongodb_database]


async def check_db_connection() -> bool:
    """
    Check if MongoDB connection is healthy.
    """
    if _client is None:
        return False

    try:
        await _client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False
    except Exception:
        return False


def get_db_info() -> dict:
    """
    Get database connection information and status.
    """
    # Sanitize MongoDB URL to hide credentials
    sanitized_url = _sanitize_mongodb_url(settings.mongodb_url)

    return {
        "status": "connected" if _client is not None else "disconnected",
        "url": sanitized_url,
        "database": settings.mongodb_database,
        "environment": settings.environment,
    }


def _sanitize_mongodb_url(url: str) -> str:
    """
    Hide password in MongoDB URL for safe logging.
    """
    if "@" not in url:
        return url

    try:
        # Handle mongodb+srv:// or mongodb://
        if "://" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                credentials, host = rest.split("@", 1)
                if ":" in credentials:
                    username = credentials.split(":", 1)[0]
                    return f"{protocol}://{username}:***@{host}"
        return url
    except ValueError:
        return url
