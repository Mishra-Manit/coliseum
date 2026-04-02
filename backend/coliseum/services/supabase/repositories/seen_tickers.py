"""DB repository for seen ticker persistence."""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import SeenTicker

logger = logging.getLogger(__name__)


async def get_seen_tickers_from_db() -> list[str]:
    """Return all tickers previously discovered by Scout."""
    async with get_db_session() as session:
        result = await session.execute(select(SeenTicker.ticker))
        return list(result.scalars().all())


async def add_seen_ticker_to_db(ticker: str) -> None:
    """Insert a seen ticker, ignoring if it already exists."""
    stmt = pg_insert(SeenTicker).values(ticker=ticker).on_conflict_do_nothing(
        index_elements=["ticker"]
    )
    async with get_db_session() as session:
        await session.execute(stmt)
        await session.commit()

    logger.info("Added seen ticker %s", ticker)
