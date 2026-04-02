"""SQLAlchemy async engine and session factory for Supabase.

Reads SUPABASE_DB_URL from environment (set via .env).
Direct Postgres connection using asyncpg — not PostgREST.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from coliseum.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    url = settings.supabase_db_url
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set in environment")
    # Session pooler (port 5432, Supavisor session mode):
    # - Compatible with asyncpg prepared statements, unlike transaction pooler (port 6543)
    #   which breaks asyncpg's prepared statement cache.
    # - NullPool means no persistent idle connections between daemon heartbeat cycles
    #   (queries run every 15-60 min), so we don't hold open connections that count
    #   against Supabase's connection limit. The pooler handles server-side connection reuse.
    return create_async_engine(
        url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager yielding a database session with auto-rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
