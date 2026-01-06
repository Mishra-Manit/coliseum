"""
Base document classes and mixins for Beanie ODM.

This module provides:
- TimestampMixin: Automatic created_at/updated_at fields
- BaseDocument: Base class combining Document with common functionality
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


class TimestampMixin:
    """Mixin that adds created_at and updated_at fields."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    async def save(self, *args, **kwargs):
        """Override save to update updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
        return await super().save(*args, **kwargs)


class BaseDocument(TimestampMixin, Document):
    """
    Base document class for all Coliseum models.

    Provides:
    - Automatic timestamps (created_at, updated_at)
    - Common configuration settings
    """

    class Settings:
        # Use the class name as collection name by default
        # Override in subclasses if needed
        use_state_management = True
