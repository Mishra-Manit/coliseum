"""DB repository for opportunity persistence."""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import update

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Opportunity, OpportunityAnalysis
from coliseum.storage.files import OpportunitySignal

logger = logging.getLogger(__name__)


async def save_opportunity_to_db(
    opportunity: OpportunitySignal,
    *,
    paper: bool = False,
) -> None:
    """Upsert an Opportunity and its OpportunityAnalysis in a single transaction."""
    opp_row = Opportunity(
        id=opportunity.id,
        market_ticker=opportunity.market_ticker,
        event_ticker=opportunity.event_ticker,
        event_title=opportunity.event_title,
        market_title=opportunity.market_title,
        subtitle=opportunity.subtitle if opportunity.subtitle else None,
        yes_price=Decimal(str(opportunity.yes_price)),
        no_price=Decimal(str(opportunity.no_price)),
        close_time=opportunity.close_time,
        discovered_at=opportunity.discovered_at,
        status=opportunity.status,
        outcome_status=opportunity.outcome_status,
        risk_level=opportunity.risk_level,
        paper=paper,
    )

    analysis_row = OpportunityAnalysis(
        opportunity_id=opportunity.id,
        rationale=opportunity.rationale,
        resolution_source=opportunity.resolution_source if opportunity.resolution_source else None,
        evidence_bullets=opportunity.evidence_bullets,
        remaining_risks=opportunity.remaining_risks,
        scout_sources=opportunity.scout_sources,
    )

    async with get_db_session() as session:
        await session.merge(opp_row)
        await session.merge(analysis_row)
        await session.commit()

    logger.info("Saved opportunity %s to DB", opportunity.id)


async def update_opportunity_research(
    opportunity_id: str,
    synthesis: str,
    completed_at: datetime,
    duration_seconds: int,
) -> None:
    """Persist research synthesis and completion timestamp for an opportunity."""
    async with get_db_session() as session:
        await session.execute(
            update(OpportunityAnalysis)
            .where(OpportunityAnalysis.opportunity_id == opportunity_id)
            .values(
                research_synthesis=synthesis,
                research_duration_seconds=duration_seconds,
            )
        )
        await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(research_completed_at=completed_at)
        )
        await session.commit()

    logger.info("Updated research for opportunity %s", opportunity_id)


async def update_opportunity_recommendation(
    opportunity_id: str,
    completed_at: datetime,
    action: str | None,
    status: str,
) -> None:
    """Persist recommendation action and status for an opportunity."""
    async with get_db_session() as session:
        await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(
                recommendation_completed_at=completed_at,
                action=action,
                status=status,
            )
        )
        await session.commit()

    logger.info("Updated recommendation for opportunity %s", opportunity_id)


async def mark_opportunity_failed_in_db(
    opportunity_id: str,
    failed_stage: str,
    error_message: str,
) -> None:
    """Mark an opportunity as failed with stage and error details."""
    async with get_db_session() as session:
        await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(
                status="failed",
                failed_stage=failed_stage,
                failure_error=error_message,
                failed_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    logger.info("Marked opportunity %s as failed at stage '%s'", opportunity_id, failed_stage)
