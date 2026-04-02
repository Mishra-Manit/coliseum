"""DB repository for portfolio state and position persistence."""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import (
    ClosedPosition as DBClosedPosition,
    OpenPosition,
    PortfolioState as DBPortfolioState,
)
from coliseum.storage.state import ClosedPosition as LocalClosedPosition, Position

logger = logging.getLogger(__name__)


async def sync_portfolio_to_db(
    cash_balance: float,
    positions_value: float,
    total_value: float,
    open_positions: list[Position],
) -> None:
    """Bulk-replace open positions and update portfolio state singleton."""
    portfolio_row = DBPortfolioState(
        id=1,
        cash_balance=Decimal(str(cash_balance)),
        positions_value=Decimal(str(positions_value)),
        total_value=Decimal(str(total_value)),
        updated_at=datetime.now(timezone.utc),
    )

    position_rows = [
        OpenPosition(
            id=pos.id,
            market_ticker=pos.market_ticker,
            side=pos.side,
            contracts=pos.contracts,
            average_entry=Decimal(str(pos.average_entry)),
            current_price=Decimal(str(pos.current_price)),
            opportunity_id=pos.opportunity_id,
        )
        for pos in open_positions
    ]

    async with get_db_session() as session:
        await session.execute(delete(OpenPosition))
        for row in position_rows:
            session.add(row)
        await session.merge(portfolio_row)
        await session.commit()

    logger.info(
        "Synced portfolio to DB: %d open positions, total_value=%.2f",
        len(open_positions),
        total_value,
    )


async def update_portfolio_after_trade_in_db(
    position: Position,
    cash_balance: float,
    positions_value: float,
    total_value: float,
) -> None:
    """Add a new open position and update portfolio balances after a trade."""
    position_row = OpenPosition(
        id=position.id,
        market_ticker=position.market_ticker,
        side=position.side,
        contracts=position.contracts,
        average_entry=Decimal(str(position.average_entry)),
        current_price=Decimal(str(position.current_price)),
        opportunity_id=position.opportunity_id,
    )

    portfolio_row = DBPortfolioState(
        id=1,
        cash_balance=Decimal(str(cash_balance)),
        positions_value=Decimal(str(positions_value)),
        total_value=Decimal(str(total_value)),
        updated_at=datetime.now(timezone.utc),
    )

    async with get_db_session() as session:
        await session.merge(position_row)
        await session.merge(portfolio_row)
        await session.commit()

    logger.info(
        "Updated portfolio after trade: position=%s, total_value=%.2f",
        position.id,
        total_value,
    )


async def save_closed_position_to_db(closed_pos: LocalClosedPosition) -> None:
    """Persist a closed position record to the database."""
    closed_row = DBClosedPosition(
        market_ticker=closed_pos.market_ticker,
        side=closed_pos.side,
        contracts=closed_pos.contracts,
        entry_price=Decimal(str(closed_pos.entry_price)),
        exit_price=Decimal(str(closed_pos.exit_price)),
        pnl=Decimal(str(closed_pos.pnl)),
        opportunity_id=closed_pos.opportunity_id,
        closed_at=closed_pos.closed_at,
        entry_rationale=closed_pos.entry_rationale,
    )

    async with get_db_session() as session:
        session.add(closed_row)
        await session.commit()

    logger.info(
        "Saved closed position for ticker=%s, pnl=%.2f",
        closed_pos.market_ticker,
        closed_pos.pnl,
    )
