"""DB repository for trade execution and trade closure persistence."""

import logging
from decimal import Decimal

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Trade, TradeClose as DBTradeClose
from coliseum.storage.files import TradeExecution, TradeClose

logger = logging.getLogger(__name__)


async def save_trade_to_db(trade: TradeExecution) -> None:
    """Persist a trade execution record to the database."""
    trade_row = Trade(
        id=trade.id,
        position_id=trade.position_id,
        opportunity_id=trade.opportunity_id,
        market_ticker=trade.market_ticker,
        side=trade.side,
        action=trade.action,
        contracts=trade.contracts,
        price=Decimal(str(trade.price)),
        total=Decimal(str(trade.total)),
        paper=trade.paper,
        executed_at=trade.executed_at,
    )

    async with get_db_session() as session:
        await session.merge(trade_row)
        await session.commit()

    logger.info("Saved trade %s to DB", trade.id)


async def save_trade_close_to_db(close: TradeClose) -> None:
    """Persist a trade closure record to the database."""
    close_row = DBTradeClose(
        id=close.id,
        opportunity_id=close.opportunity_id,
        market_ticker=close.market_ticker,
        side=close.side,
        contracts=close.contracts,
        entry_price=Decimal(str(close.entry_price)),
        exit_price=Decimal(str(close.exit_price)),
        pnl=Decimal(str(close.pnl)),
        entry_rationale=close.entry_rationale,
        closed_at=close.closed_at,
    )

    async with get_db_session() as session:
        await session.merge(close_row)
        await session.commit()

    logger.info("Saved trade close %s to DB", close.id)
