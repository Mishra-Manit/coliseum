"""DB repository for portfolio state and position persistence."""

import logging

from sqlalchemy import delete, select

from coliseum.domain.mappers import (
    closed_position_to_db,
    db_to_portfolio_state,
    portfolio_stats_to_db,
    position_to_db,
)
from coliseum.domain.portfolio import ClosedPosition, PortfolioState, Position
from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import (
    ClosedPosition as DBClosedPosition,
    OpenPosition as DBOpenPosition,
    PortfolioState as DBPortfolioState,
)

logger = logging.getLogger(__name__)


async def load_state_from_db() -> PortfolioState:
    """Load full portfolio state from the database."""
    async with get_db_session() as session:
        portfolio_result = await session.execute(
            select(DBPortfolioState).where(DBPortfolioState.id == 1)
        )
        portfolio_row = portfolio_result.scalar_one_or_none()

        open_result = await session.execute(select(DBOpenPosition))
        open_rows = list(open_result.scalars().all())

        closed_result = await session.execute(select(DBClosedPosition))
        closed_rows = list(closed_result.scalars().all())

    return db_to_portfolio_state(portfolio_row, open_rows, closed_rows)


async def sync_portfolio_to_db(
    cash_balance: float,
    positions_value: float,
    total_value: float,
    open_positions: list[Position],
) -> None:
    """Bulk-replace open positions and update portfolio state singleton."""
    portfolio_row = portfolio_stats_to_db(cash_balance, positions_value, total_value)
    position_rows = [position_to_db(pos) for pos in open_positions]

    async with get_db_session() as session:
        await session.execute(delete(DBOpenPosition))
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
    position_row = position_to_db(position)
    portfolio_row = portfolio_stats_to_db(cash_balance, positions_value, total_value)

    async with get_db_session() as session:
        await session.merge(position_row)
        await session.merge(portfolio_row)
        await session.commit()

    logger.info(
        "Updated portfolio after trade: position=%s, total_value=%.2f",
        position.id,
        total_value,
    )


async def save_closed_position_to_db(closed_pos: ClosedPosition) -> None:
    """Persist a closed position record to the database."""
    closed_row = closed_position_to_db(closed_pos)

    async with get_db_session() as session:
        session.add(closed_row)
        await session.commit()

    logger.info(
        "Saved closed position for ticker=%s, pnl=%.2f",
        closed_pos.market_ticker,
        closed_pos.pnl,
    )
