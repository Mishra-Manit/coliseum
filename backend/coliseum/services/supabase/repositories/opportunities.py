"""DB repository for opportunity persistence."""

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import select, update

from coliseum.domain.mappers import db_to_opportunity, opportunity_to_db, to_float
from coliseum.domain.opportunity import OpportunitySignal
from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Opportunity, OpportunityAnalysis

logger = logging.getLogger(__name__)


def _map_trader_decision_to_action(trader_decision: str) -> str | None:
    """Map Trader decision enums to normalized opportunity action values."""
    if trader_decision == "EXECUTE_BUY_YES":
        return "BUY_YES"
    if trader_decision == "EXECUTE_BUY_NO":
        return "BUY_NO"
    if trader_decision == "REJECT":
        return "ABSTAIN"
    return None


async def save_opportunity_to_db(
    opportunity: OpportunitySignal,
    *,
    paper: bool = False,
) -> None:
    """Upsert an Opportunity and its OpportunityAnalysis in a single transaction."""
    opp_row, analysis_row = opportunity_to_db(opportunity, paper=paper)

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
    action = _map_trader_decision_to_action(trader_decision)
    if action is not None:
        opp_values["action"] = action
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


async def load_opportunity_from_db(opportunity_id: str) -> OpportunitySignal:
    """Load a single opportunity and its analysis by ID, raising if absent."""
    async with get_db_session() as session:
        opp_result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opp = opp_result.scalar_one_or_none()
        if opp is None:
            raise ValueError(f"Opportunity {opportunity_id} not found in DB")

        analysis_result = await session.execute(
            select(OpportunityAnalysis).where(
                OpportunityAnalysis.opportunity_id == opportunity_id
            )
        )
        analysis = analysis_result.scalar_one_or_none()

    return db_to_opportunity(opp, analysis)


async def load_opportunity_by_ticker_from_db(market_ticker: str) -> OpportunitySignal | None:
    """Load the most recently discovered opportunity for a market ticker, or None."""
    async with get_db_session() as session:
        opp_result = await session.execute(
            select(Opportunity)
            .where(Opportunity.market_ticker == market_ticker)
            .order_by(Opportunity.discovered_at.desc())
            .limit(1)
        )
        opp = opp_result.scalar_one_or_none()
        if opp is None:
            return None

        analysis_result = await session.execute(
            select(OpportunityAnalysis).where(
                OpportunityAnalysis.opportunity_id == opp.id
            )
        )
        analysis = analysis_result.scalar_one_or_none()

    return db_to_opportunity(opp, analysis)


async def get_opportunity_body_from_db(opportunity_id: str) -> str:
    """Reconstruct a markdown prompt body for an opportunity from DB rows."""
    async with get_db_session() as session:
        opp_result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opp = opp_result.scalar_one_or_none()
        if opp is None:
            return ""

        analysis_result = await session.execute(
            select(OpportunityAnalysis).where(
                OpportunityAnalysis.opportunity_id == opportunity_id
            )
        )
        analysis = analysis_result.scalar_one_or_none()

    yes_price = to_float(opp.yes_price)
    no_price = to_float(opp.no_price)

    if opp.event_title:
        event_line = f"**Event**: {opp.event_title}\n"
    else:
        event_line = ""
    if opp.subtitle:
        subtitle_section = f"\n**Outcome**: {opp.subtitle}\n"
    else:
        subtitle_section = ""

    if analysis:
        rationale = analysis.rationale
        resolution_source = analysis.resolution_source or ""
        evidence_bullets = analysis.evidence_bullets
        remaining_risks = analysis.remaining_risks
        scout_sources = analysis.scout_sources
    else:
        rationale = ""
        resolution_source = ""
        evidence_bullets = []
        remaining_risks = []
        scout_sources = []

    if opp.outcome_status:
        verdict_line = f"**{opp.outcome_status}**  ·  **{opp.risk_level} RISK**"
    else:
        verdict_line = f"**Rationale**: {rationale}"

    if evidence_bullets:
        evidence_lines = "\n".join(f"- {b}" for b in evidence_bullets)
    else:
        evidence_lines = "- See rationale"

    if remaining_risks:
        risks_lines = "\n".join(f"- {r}" for r in remaining_risks)
    else:
        risks_lines = "- None identified"

    sources_section = ""
    if scout_sources:
        sources_lines = "\n".join(f"- {s}" for s in scout_sources)
        sources_section = f"\n**Sources**\n{sources_lines}\n"

    scout_section = f"""## Scout Assessment

{verdict_line}

{rationale}

**Evidence**
{evidence_lines}

**Resolution**
{resolution_source}

**Risks**
{risks_lines}
{sources_section}"""

    close_formatted = opp.close_time.strftime("%Y-%m-%d %I:%M %p")

    body = f"""# {opp.market_title}
{event_line}{subtitle_section}
{scout_section}
## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | {yes_price * 100:.0f}¢ (${yes_price:.2f}) |
| No Price | {no_price * 100:.0f}¢ (${no_price:.2f}) |
| Closes | {close_formatted} |"""

    if analysis:
        research_synthesis = analysis.research_synthesis
    else:
        research_synthesis = None
    if research_synthesis is not None:
        body += f"\n\n---\n\n## Research Synthesis\n\n{research_synthesis}"

    return body


async def get_entry_rationale_from_db(opportunity_id: str) -> str | None:
    """Fetch only the rationale field for an opportunity, or None if absent."""
    async with get_db_session() as session:
        result = await session.execute(
            select(OpportunityAnalysis.rationale).where(
                OpportunityAnalysis.opportunity_id == opportunity_id
            )
        )
        row = result.scalar_one_or_none()

    return row


async def list_opportunities_from_db(
    start_date: date | None = None,
) -> list[OpportunitySignal]:
    """List all opportunities with analysis, newest first, with optional date filter."""
    async with get_db_session() as session:
        stmt = (
            select(Opportunity, OpportunityAnalysis)
            .outerjoin(OpportunityAnalysis, Opportunity.id == OpportunityAnalysis.opportunity_id)
            .order_by(Opportunity.discovered_at.desc())
        )
        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(Opportunity.discovered_at >= start_dt)
        rows = (await session.execute(stmt)).all()

    return [db_to_opportunity(opp, analysis) for opp, analysis in rows]


async def append_x_sentiment_to_research(
    opportunity_id: str,
    x_sentiment_markdown: str,
) -> None:
    """Append X sentiment markdown to the existing research synthesis."""
    x_section = f"\n\n---\n\n## X (Twitter) Sentiment\n\n{x_sentiment_markdown}"

    async with get_db_session() as session:
        result = await session.execute(
            select(OpportunityAnalysis.research_synthesis).where(
                OpportunityAnalysis.opportunity_id == opportunity_id
            )
        )
        current = result.scalar_one_or_none()
        new_synthesis = f"{current}{x_section}" if current else x_section.lstrip()

        result = await session.execute(
            update(OpportunityAnalysis)
            .where(OpportunityAnalysis.opportunity_id == opportunity_id)
            .values(research_synthesis=new_synthesis)
        )
        if result.rowcount == 0:
            logger.warning("No analysis row found for %s — X sentiment not persisted", opportunity_id)
        await session.commit()

    logger.info("Appended X sentiment to research for opportunity %s", opportunity_id)
