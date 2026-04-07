"""DB repository for trading decision persistence."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from coliseum.memory.decisions import DecisionEntry
from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Decision

logger = logging.getLogger(__name__)


async def save_decision_to_db(entry: DecisionEntry) -> None:
    """Persist a trading decision to the database."""
    decision_row = Decision(
        ts=entry.ts,
        opportunity_id=entry.opportunity_id if entry.opportunity_id else None,
        ticker=entry.ticker,
        action=entry.action,
        price=Decimal(str(entry.price)) if entry.price is not None else Decimal("0"),
        contracts=entry.contracts,
        confidence=Decimal(str(entry.confidence)),
        reasoning=entry.reasoning,
        tldr=entry.tldr if entry.tldr else None,
        execution_status=entry.execution_status,
    )

    async with get_db_session() as session:
        session.add(decision_row)
        await session.commit()

    logger.info("Saved decision for ticker %s (opportunity_id=%s) to DB", entry.ticker, entry.opportunity_id)


async def load_recent_decisions_from_db(hours: int = 24) -> list[DecisionEntry]:
    """Load decisions recorded within the last `hours` hours, newest first."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with get_db_session() as session:
        result = await session.execute(
            select(Decision).where(Decision.ts >= cutoff).order_by(Decision.ts.desc())
        )
        rows = result.scalars().all()

    return [
        DecisionEntry(
            ts=row.ts,
            opportunity_id=row.opportunity_id or "",
            ticker=row.ticker,
            action=row.action,
            price=float(row.price),
            contracts=row.contracts,
            confidence=float(row.confidence),
            reasoning=row.reasoning,
            tldr=row.tldr or "",
            execution_status=row.execution_status,
        )
        for row in rows
    ]
