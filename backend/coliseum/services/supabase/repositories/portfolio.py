"""DB repository for portfolio state and position persistence."""

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from coliseum.domain.mappers import (
    closed_position_to_db,
    db_to_portfolio_state,
    portfolio_stats_to_db,
    to_decimal,
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


def _build_open_position_values(position: Position, *, updated_at: datetime) -> dict[str, object]:
    """Convert a domain Position to insert values for open_positions upserts."""
    return {
        "id": position.id,
        "market_ticker": position.market_ticker,
        "side": position.side,
        "contracts": position.contracts,
        "average_entry": to_decimal(position.average_entry),
        "current_price": to_decimal(position.current_price),
        "opportunity_id": position.opportunity_id,
        "updated_at": updated_at,
    }


async def _upsert_open_positions(
    session: AsyncSession,
    positions: list[Position],
) -> None:
    """Upsert open positions by id while preserving created_at."""
    if not positions:
        return

    updated_at = datetime.now(timezone.utc)
    values = [
        _build_open_position_values(position, updated_at=updated_at)
        for position in positions
    ]
    stmt = pg_insert(DBOpenPosition).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[DBOpenPosition.id],
        set_={
            "market_ticker": stmt.excluded.market_ticker,
            "side": stmt.excluded.side,
            "contracts": stmt.excluded.contracts,
            "average_entry": stmt.excluded.average_entry,
            "current_price": stmt.excluded.current_price,
            "opportunity_id": stmt.excluded.opportunity_id,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    await session.execute(stmt)


async def sync_portfolio_to_db(
    cash_balance: float,
    positions_value: float,
    total_value: float,
    open_positions: list[Position],
) -> None:
    """Upsert live open positions, prune stale rows, and update portfolio singleton."""
    portfolio_row = portfolio_stats_to_db(cash_balance, positions_value, total_value)
    open_position_ids = [position.id for position in open_positions]

    async with get_db_session() as session:
        await _upsert_open_positions(session, open_positions)

        if open_position_ids:
            await session.execute(
                delete(DBOpenPosition).where(~DBOpenPosition.id.in_(open_position_ids))
            )
        else:
            await session.execute(delete(DBOpenPosition))

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
    """Upsert a traded position and update portfolio balances after a trade."""
    portfolio_row = portfolio_stats_to_db(cash_balance, positions_value, total_value)

    async with get_db_session() as session:
        await _upsert_open_positions(session, [position])
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
