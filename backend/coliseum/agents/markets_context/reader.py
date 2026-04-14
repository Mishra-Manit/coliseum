"""Async market type context reader. Reads exclusively from DB."""

from __future__ import annotations

import logging

from coliseum.agents.markets_context.seed_data import ALIASES, MARKET_TYPES
from coliseum.domain.opportunity import OpportunitySignal
from coliseum.services.supabase.models import MarketCategoryContext
from coliseum.services.supabase.repositories.market_context import load_category_context

logger = logging.getLogger(__name__)

_UNKNOWN_CONTEXT = (
    "**Unknown Market Type** — Research what specifically triggers YES resolution "
    "and whether any current conditions threaten that outcome.\n\n"
    "No encyclopedia entry exists for this market category yet. "
    "Focus your research on: (1) exact resolution criteria and data source, "
    "(2) any disputes or edge cases, (3) strongest argument against YES."
)


def _match_category_key(event_ticker: str) -> str | None:
    """Map an uppercased event ticker to its category key. Returns None if no match."""
    event = event_ticker.upper()
    for key in MARKET_TYPES:
        if key in event:
            return key
    for alias, canonical in ALIASES.items():
        if alias in event:
            return canonical
    if "MENTION" in event and "BERNIE" in event:
        return "BERNIEMENTION"
    if "OUT" in event and any(x in event for x in ("LEADER", "PRES")):
        return "KHAMENEI"
    if "MLB" in event and "GAME" in event:
        return "MLBSTGAME"
    if "HOCKEY" in event and "OLYMPIC" in event:
        return "WOHOCKEY"
    return None


def _slug_from_ticker(market_ticker: str) -> str:
    """Extract the trailing slug from a hyphenated ticker."""
    parts = market_ticker.split("-")
    if len(parts) > 1:
        return parts[-1]
    return "unknown"


def _format_db_context(row: MarketCategoryContext, slug: str) -> str:
    """Format a DB row into the prompt text injected for the Researcher."""
    desc = row.resolution_desc_template.format(slug=slug)
    sections = [f"**{row.label}** — {desc}"]

    if row.resolution_rules:
        sections.append(f"\n### Resolution Mechanics\n{row.resolution_rules}")

    if row.known_disputes:
        sections.append(f"\n### Known Disputes & Precedents\n{row.known_disputes}")

    if row.edge_cases:
        sections.append(f"\n### Edge Cases\n{row.edge_cases}")

    if row.risk_questions:
        questions = "\n".join(f"- {q.format(slug=slug)}" for q in row.risk_questions)
        sections.append(
            f"\n### Key Risk Questions (use as context, not as separate search tasks)\n{questions}"
        )

    return "\n".join(sections)


async def get_market_type_context(opportunity: OpportunitySignal) -> str:
    """Return market-type-specific research guidance from the DB."""
    event = opportunity.event_ticker.upper()
    category_key = _match_category_key(event)

    if category_key is None:
        logger.info("No category match for event ticker %s", event)
        return _UNKNOWN_CONTEXT

    try:
        row = await load_category_context(category_key)
    except Exception as e:
        logger.error("DB read failed for %s: %s", category_key, e)
        return _UNKNOWN_CONTEXT

    if row is None:
        logger.warning("No DB entry for category %s — run refresh-context", category_key)
        return _UNKNOWN_CONTEXT

    slug = _slug_from_ticker(opportunity.market_ticker.upper()) if row.uses_slug else ""
    return _format_db_context(row, slug)
