"""Ticker-to-category-key matching for market type context."""

from __future__ import annotations

from coliseum.agents.analyst.markets_context.market_type_context import (
    MARKET_TYPES,
    _ALIASES,
)


def match_category_key(event_ticker: str) -> str | None:
    """Map an uppercased event ticker to its category key. Returns None if no match."""
    event = event_ticker.upper()
    for key in MARKET_TYPES:
        if key in event:
            return key
    for alias, canonical in _ALIASES.items():
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


def slug_from_ticker(market_ticker: str) -> str:
    """Extract the trailing slug from a hyphenated ticker."""
    parts = market_ticker.split("-")
    if len(parts) > 1:
        return parts[-1]
    return "unknown"
