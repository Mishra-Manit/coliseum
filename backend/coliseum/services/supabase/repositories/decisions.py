"""DB repository for trading decision persistence."""

import logging
from decimal import Decimal

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
        outcome=entry.outcome,
    )

    async with get_db_session() as session:
        session.add(decision_row)
        await session.commit()

    logger.info("Saved decision for ticker %s (opportunity_id=%s) to DB", entry.ticker, entry.opportunity_id)
