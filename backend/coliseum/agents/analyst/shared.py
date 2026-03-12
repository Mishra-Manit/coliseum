"""Shared utilities for Analyst sub-agents (Researcher + Recommender)."""

import logging
from pathlib import Path

from coliseum.storage.files import (
    OpportunitySignal,
    find_opportunity_file_by_id,
    load_opportunity_from_file,
)

logger = logging.getLogger(__name__)


def load_opportunity(opportunity_id: str, paper: bool = False) -> tuple[Path, OpportunitySignal]:
    """Load an opportunity file by ID."""
    opp_file = find_opportunity_file_by_id(opportunity_id, paper=paper)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    opportunity = load_opportunity_from_file(opp_file)
    return opp_file, opportunity


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

    return f"""**ID**: {opportunity.id}
**Event Ticker**: {opportunity.event_ticker}
{event_title_line}**Market Ticker**: {opportunity.market_ticker}
**Market**: {opportunity.title}
{subtitle_info}**Current YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**Current NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)
**Market Closes**: {opportunity.close_time.isoformat() if opportunity.close_time else 'N/A'}
**Status**: {opportunity.status}
**Discovered**: {opportunity.discovered_at.isoformat()}"""
