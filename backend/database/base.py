"""Database configuration and SQLAlchemy setup for PostgreSQL (Neon)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from config import settings


def _create_engine():
    """
    Create SQLAlchemy engine for Neon PostgreSQL.

    Configuration:
    - NullPool: Prevents connection pooling conflicts with Neon's pooling
    - echo: Show SQL statements in development mode
    - sslmode=require: Required for Neon connections
    """
    return create_engine(
        settings.database_url,
        poolclass=NullPool,  # Neon best practice: disable app-side pooling
        echo=settings.is_development,
    )


# Create engine
engine = _create_engine()

# Create SessionLocal factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create declarative base for ORM models
Base = declarative_base()
