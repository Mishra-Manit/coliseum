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
    if opportunity.subtitle:
        subtitle = opportunity.subtitle
    else:
        subtitle = None

    opp_row = Opportunity(
        id=opportunity.id,
        market_ticker=opportunity.market_ticker,
        event_ticker=opportunity.event_ticker,
        event_title=opportunity.event_title,
        market_title=opportunity.market_title,
        subtitle=subtitle,
        yes_price=Decimal(str(opportunity.yes_price)),
        no_price=Decimal(str(opportunity.no_price)),
        close_time=opportunity.close_time,
        discovered_at=opportunity.discovered_at,
        status=opportunity.status,
        outcome_status=opportunity.outcome_status,
        risk_level=opportunity.risk_level,
        paper=paper,
    )

    if opportunity.resolution_source:
        resolution_source = opportunity.resolution_source
    else:
        resolution_source = None

    analysis_row = OpportunityAnalysis(
        opportunity_id=opportunity.id,
        rationale=opportunity.rationale,
        resolution_source=resolution_source,
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
    """Persist research synthesis, duration, and completion timestamp."""
    async with get_db_session() as session:
        analysis_result = await session.execute(
            update(OpportunityAnalysis)
            .where(OpportunityAnalysis.opportunity_id == opportunity_id)
            .values(
                research_synthesis=synthesis,
                research_duration_seconds=duration_seconds,
            )
        )
        opp_result = await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(research_completed_at=completed_at)
        )
        await session.commit()

    if analysis_result.rowcount == 0:
        logger.warning(
            "No OpportunityAnalysis row found for opportunity %s -- research synthesis update was a no-op",
            opportunity_id,
        )
    if opp_result.rowcount == 0:
        logger.warning(
            "No Opportunity row found for opportunity %s -- research_completed_at update was a no-op",
            opportunity_id,
        )
    if analysis_result.rowcount > 0 and opp_result.rowcount > 0:
        logger.info("Updated research for opportunity %s", opportunity_id)


async def update_opportunity_recommendation(
    opportunity_id: str,
    completed_at: datetime,
    action: str | None,
    status: str,
) -> None:
    """Persist recommendation action and status for an opportunity."""
    async with get_db_session() as session:
        result = await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(
                recommendation_completed_at=completed_at,
                action=action,
                status=status,
            )
        )
        await session.commit()

    if result.rowcount == 0:
        logger.warning(
            "No DB row found for opportunity %s -- recommendation update was a no-op",
            opportunity_id,
        )
    else:
        logger.info("Updated recommendation for opportunity %s", opportunity_id)


async def mark_opportunity_failed_in_db(
    opportunity_id: str,
    failed_stage: str,
    error_message: str,
) -> None:
    """Mark an opportunity as failed with stage and error details."""
    async with get_db_session() as session:
        result = await session.execute(
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

    if result.rowcount == 0:
        logger.warning(
            "No DB row found for opportunity %s -- failed-stage update was a no-op",
            opportunity_id,
        )
    else:
        logger.info("Marked opportunity %s as failed at stage '%s'", opportunity_id, failed_stage)


async def update_opportunity_trader_decision(
    opportunity_id: str,
    trader_decision: str,
    trader_tldr: str,
    status: str | None = None,
) -> None:
    """Persist trader decision and summary for an opportunity."""
    opp_values: dict[str, str] = {"trader_decision": trader_decision}
    if status is not None:
        opp_values["status"] = status

    async with get_db_session() as session:
        opp_result = await session.execute(
            update(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .values(**opp_values)
        )
        analysis_result = await session.execute(
            update(OpportunityAnalysis)
            .where(OpportunityAnalysis.opportunity_id == opportunity_id)
            .values(trader_tldr=trader_tldr)
        )
        await session.commit()

    if opp_result.rowcount == 0:
        logger.warning(
            "No Opportunity row found for opportunity %s -- trader_decision update was a no-op",
            opportunity_id,
        )
    if analysis_result.rowcount == 0:
        logger.warning(
            "No OpportunityAnalysis row found for opportunity %s -- trader_tldr update was a no-op",
            opportunity_id,
        )
    if opp_result.rowcount > 0 and analysis_result.rowcount > 0:
        logger.info("Updated trader decision for opportunity %s", opportunity_id)
