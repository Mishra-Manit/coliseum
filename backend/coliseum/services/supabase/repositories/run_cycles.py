"""DB repository for pipeline run cycle persistence."""

import logging
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import select

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import RunCycle

logger = logging.getLogger(__name__)


async def save_run_cycle_to_db(
    *,
    cycle_at: datetime,
    duration_seconds: float,
    guardian_synced: int = 0,
    guardian_closed: int = 0,
    scout_scanned: int = 0,
    scout_found: int = 0,
    analyst_results: dict | None = None,
    trader_results: dict | None = None,
    cash_balance: float = 0.0,
    positions_value: float = 0.0,
    total_value: float = 0.0,
    open_positions: int = 0,
    errors: list[str] | None = None,
) -> None:
    """Persist a pipeline cycle's structured metrics to the run_cycles table."""
    row = RunCycle(
        cycle_at=cycle_at,
        duration_seconds=int(duration_seconds),
        guardian_synced=guardian_synced,
        guardian_closed=guardian_closed,
        scout_scanned=scout_scanned,
        scout_found=scout_found,
        analyst_results=analyst_results,
        trader_results=trader_results,
        cash_balance=Decimal(str(cash_balance)),
        positions_value=Decimal(str(positions_value)),
        total_value=Decimal(str(total_value)),
        open_positions=open_positions,
        errors=errors if errors else [],
    )

    async with get_db_session() as session:
        session.add(row)
        await session.commit()

    logger.info("Saved run cycle to DB (cycle_at=%s)", cycle_at.isoformat())


async def list_run_cycles_from_db(
    start_date: date | None = None,
) -> list[dict]:
    """Return run cycle NAV snapshots ordered by time, for charting."""
    async with get_db_session() as session:
        stmt = (
            select(
                RunCycle.cycle_at,
                RunCycle.total_value,
                RunCycle.cash_balance,
                RunCycle.positions_value,
                RunCycle.open_positions,
            )
            .where(RunCycle.total_value.isnot(None))
            .order_by(RunCycle.cycle_at.asc())
        )

        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(RunCycle.cycle_at >= start_dt)

        rows = (await session.execute(stmt)).all()

    return [
        {
            "cycle_at": row.cycle_at.isoformat(),
            "total_value": float(row.total_value),
            "cash_balance": float(row.cash_balance),
            "positions_value": float(row.positions_value),
            "open_positions": row.open_positions,
        }
        for row in rows
    ]
