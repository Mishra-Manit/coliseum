"""DB repository for portfolio state and position persistence."""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, select

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import (
    ClosedPosition as DBClosedPosition,
    OpenPosition,
    PortfolioState as DBPortfolioState,
)
from coliseum.storage.state import (
    ClosedPosition as LocalClosedPosition,
    Position,
    PortfolioState as LocalPortfolioState,
    PortfolioStats,
)

logger = logging.getLogger(__name__)


async def load_state_from_db() -> LocalPortfolioState:
    """Load full portfolio state from the database."""
    async with get_db_session() as session:
        portfolio_result = await session.execute(
            select(DBPortfolioState).where(DBPortfolioState.id == 1)
        )
        portfolio_row = portfolio_result.scalar_one_or_none()

        open_result = await session.execute(select(OpenPosition))
        open_rows = open_result.scalars().all()

        closed_result = await session.execute(select(DBClosedPosition))
        closed_rows = closed_result.scalars().all()

    if portfolio_row is None:
        return LocalPortfolioState(
            portfolio=PortfolioStats(total_value=0.0, cash_balance=0.0, positions_value=0.0),
            open_positions=[],
            closed_positions=[],
            seen_tickers=[],
        )

    stats = PortfolioStats(
        cash_balance=float(portfolio_row.cash_balance),
        positions_value=float(portfolio_row.positions_value),
        total_value=float(portfolio_row.total_value),
    )

    open_positions = [
        Position(
            id=row.id,
            market_ticker=row.market_ticker,
            side=row.side,
            contracts=row.contracts,
            average_entry=float(row.average_entry),
            current_price=float(row.current_price),
            opportunity_id=row.opportunity_id,
        )
        for row in open_rows
    ]

    closed_positions = [
        LocalClosedPosition(
            market_ticker=row.market_ticker,
            side=row.side,
            contracts=row.contracts,
            entry_price=float(row.entry_price),
            exit_price=float(row.exit_price),
            pnl=float(row.pnl),
            opportunity_id=row.opportunity_id,
            closed_at=row.closed_at,
            entry_rationale=row.entry_rationale,
        )
        for row in closed_rows
    ]

    return LocalPortfolioState(
        portfolio=stats,
        open_positions=open_positions,
        closed_positions=closed_positions,
        seen_tickers=[],
    )


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
