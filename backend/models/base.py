"""Base model utilities for SQLAlchemy."""

from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from database.base import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at fields to models."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="When the record was last updated"
    )


class UUIDMixin:
    """Mixin that adds UUID primary key."""

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier"
    )


class BaseModel(UUIDMixin, TimestampMixin, Base):
    """
    Base model class for all Coliseum models.

    Provides:
    - UUID primary key
    - Automatic timestamps (created_at, updated_at)
    """
    __abstract__ = True
