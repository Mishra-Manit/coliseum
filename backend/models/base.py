"""Base model utilities for Beanie documents."""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class TimestampMixin:
    """Mixin that adds created_at and updated_at fields to Beanie documents."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def update_timestamp(doc: Document) -> None:
    """Update the updated_at timestamp on a document before saving."""
    if hasattr(doc, "updated_at"):
        doc.updated_at = datetime.now(timezone.utc)
