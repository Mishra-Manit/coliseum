"""Shared utilities for Analyst sub-agents (Researcher + Recommender)."""

import logging

from coliseum.services.supabase.repositories.opportunities import load_opportunity_from_db
from coliseum.domain.opportunity import OpportunitySignal

logger = logging.getLogger(__name__)


async def load_opportunity(opportunity_id: str) -> OpportunitySignal:
    """Load an opportunity from the database by ID."""
    return await load_opportunity_from_db(opportunity_id)


def format_opportunity_header(opportunity: OpportunitySignal) -> str:
    """Format the common opportunity details block used in agent prompts."""
    subtitle_info = (
        f"**Specific Outcome**: {opportunity.subtitle}\n"
        if opportunity.subtitle
        else ""
    )
    event_title_line = (
        f"**Event**: {opportunity.event_title}\n"
        if opportunity.event_title
        else ""
    )

    if opportunity.close_time:
        close_time_display = opportunity.close_time.isoformat()
    else:
        close_time_display = 'N/A'

    return f"""**ID**: {opportunity.id}
**Event Ticker**: {opportunity.event_ticker}
{event_title_line}**Market Ticker**: {opportunity.market_ticker}
**Market**: {opportunity.market_title}
{subtitle_info}**Current YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**Current NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)
**Market Closes**: {close_time_display}
**Status**: {opportunity.status}
**Discovered**: {opportunity.discovered_at.isoformat()}"""
