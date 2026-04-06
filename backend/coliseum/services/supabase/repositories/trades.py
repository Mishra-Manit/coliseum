"""DB repository for trade execution and trade closure persistence."""

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import select

from coliseum.domain.mappers import trade_close_to_db, trade_to_db
from coliseum.domain.trade import TradeClose, TradeExecution
from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Trade as DBTrade, TradeClose as DBTradeClose

logger = logging.getLogger(__name__)


async def save_trade_to_db(trade: TradeExecution) -> None:
    """Persist a trade execution record to the database."""
    trade_row = trade_to_db(trade)

    async with get_db_session() as session:
        await session.merge(trade_row)
        await session.commit()

    logger.info("Saved trade %s to DB", trade.id)


async def save_trade_close_to_db(close: TradeClose) -> None:
    """Persist a trade closure record to the database."""
    close_row = trade_close_to_db(close)

    async with get_db_session() as session:
        await session.merge(close_row)
        await session.commit()

    logger.info("Saved trade close %s to DB", close.id)


async def list_trades_from_db(
    start_date: date | None = None,
    limit: int = 100,
) -> list[dict]:
    """List buy trades and trade closes merged, sorted newest-first."""
    async with get_db_session() as session:
        buy_stmt = select(DBTrade).order_by(DBTrade.executed_at.desc())
        close_stmt = select(DBTradeClose).order_by(DBTradeClose.closed_at.desc())

        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            buy_stmt = buy_stmt.where(DBTrade.executed_at >= start_dt)
            close_stmt = close_stmt.where(DBTradeClose.closed_at >= start_dt)

        buy_rows = (await session.execute(buy_stmt)).scalars().all()
        close_rows = (await session.execute(close_stmt)).scalars().all()

    buy_records: list[dict] = [
        {
            "type": "buy",
            "id": t.id,
            "market_ticker": t.market_ticker,
            "side": t.side,
            "contracts": t.contracts,
            "price": float(t.price),
            "pnl": None,
            "opportunity_id": t.opportunity_id,
            "paper": t.paper,
            "timestamp": t.executed_at.isoformat(),
        }
        for t in buy_rows
    ]

    close_records: list[dict] = [
        {
            "type": "close",
            "id": c.id,
            "market_ticker": c.market_ticker,
            "side": c.side,
            "contracts": c.contracts,
            "price": float(c.exit_price),
            "pnl": float(c.pnl),
            "opportunity_id": c.opportunity_id,
            "paper": True,
            "timestamp": c.closed_at.isoformat(),
        }
        for c in close_rows
    ]

    merged = sorted(buy_records + close_records, key=lambda r: r["timestamp"], reverse=True)
    return merged[:limit]


async def list_trade_closes_from_db(
    start_date: date | None = None,
) -> list[dict]:
    """List trade closes for chart data."""
    async with get_db_session() as session:
        stmt = select(DBTradeClose).order_by(DBTradeClose.closed_at.asc())

        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(DBTradeClose.closed_at >= start_dt)

        rows = (await session.execute(stmt)).scalars().all()

    return [
        {
            "pnl": float(c.pnl),
            "closed_at": c.closed_at.isoformat(),
        }
        for c in rows
    ]
