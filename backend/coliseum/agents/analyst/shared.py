"""Shared utilities for Analyst sub-agents (Researcher + Recommender)."""

import logging
from pathlib import Path
from typing import Literal

from coliseum.config import Settings
from coliseum.storage.files import (
    OpportunitySignal,
    find_opportunity_file_by_id,
    load_opportunity_from_file,
)

logger = logging.getLogger(__name__)


def load_and_validate_opportunity(
    opportunity_id: str,
    strategy: Literal["edge", "sure_thing"] | None,
) -> tuple[Path, OpportunitySignal, str]:
    """Load opportunity file and validate strategy matches.

    Returns (file_path, opportunity, resolved_strategy).
    """
    opp_file = find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    opportunity = load_opportunity_from_file(opp_file)
    resolved_strategy = strategy or opportunity.strategy
    if strategy and opportunity.strategy != strategy:
        raise ValueError(
            f"Strategy mismatch for {opportunity_id}: "
            f"expected {strategy}, found {opportunity.strategy}"
        )

    return opp_file, opportunity, resolved_strategy


def format_opportunity_header(opportunity: OpportunitySignal) -> str:
    """Format the common opportunity details block used in agent prompts."""
    subtitle_info = (
        f"**Specific Outcome**: {opportunity.subtitle}\n"
        if opportunity.subtitle
        else ""
    )

    return f"""**ID**: {opportunity.id}
**Event Ticker**: {opportunity.event_ticker}
**Market Ticker**: {opportunity.market_ticker}
**Market**: {opportunity.title}
{subtitle_info}**Current YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**Current NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)
**Market Closes**: {opportunity.close_time.isoformat() if opportunity.close_time else 'N/A'}
**Status**: {opportunity.status}
**Discovered**: {opportunity.discovered_at.isoformat()}"""
