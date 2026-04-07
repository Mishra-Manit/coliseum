"""DB repository for append-only portfolio snapshot persistence."""

import logging
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import func, select

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import ClosedPosition, PortfolioSnapshot

logger = logging.getLogger(__name__)


async def get_realized_pnl_from_db() -> float:
    """Return realized PnL as the sum of closed position pnl values."""
    async with get_db_session() as session:
        value = await session.scalar(
            select(func.coalesce(func.sum(ClosedPosition.pnl), 0))
        )

    if value is None:
        return 0.0
    return float(value)


async def save_portfolio_snapshot_to_db(
    *,
    cash_balance: float,
    positions_value: float,
    total_value: float,
    open_positions: int,
    realized_pnl: float,
    snapshot_at: datetime | None = None,
) -> None:
    """Persist one portfolio snapshot row for charting and operational history."""
    row = PortfolioSnapshot(
        total_value=Decimal(str(total_value)),
        cash_balance=Decimal(str(cash_balance)),
        positions_value=Decimal(str(positions_value)),
        open_positions=open_positions,
        realized_pnl=Decimal(str(realized_pnl)),
        snapshot_at=snapshot_at or datetime.now(timezone.utc),
    )

    async with get_db_session() as session:
        session.add(row)
        await session.commit()

    logger.info(
        "Saved portfolio snapshot to DB (snapshot_at=%s)",
        row.snapshot_at.isoformat(),
    )


async def list_portfolio_snapshots_from_db(
    start_date: date | None = None,
) -> list[dict]:
    """Return portfolio snapshots ordered by time, for charting."""
    async with get_db_session() as session:
        stmt = (
            select(
                PortfolioSnapshot.snapshot_at,
                PortfolioSnapshot.total_value,
                PortfolioSnapshot.cash_balance,
                PortfolioSnapshot.positions_value,
                PortfolioSnapshot.open_positions,
                PortfolioSnapshot.realized_pnl,
            )
            .order_by(PortfolioSnapshot.snapshot_at.asc())
        )

        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(PortfolioSnapshot.snapshot_at >= start_dt)

        rows = (await session.execute(stmt)).all()

    return [
        {
            "snapshot_at": row.snapshot_at.isoformat(),
            "total_value": float(row.total_value),
            "cash_balance": float(row.cash_balance),
            "positions_value": float(row.positions_value),
            "open_positions": row.open_positions,
            "realized_pnl": float(row.realized_pnl),
        }
        for row in rows
    ]
