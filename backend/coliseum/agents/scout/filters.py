"""Data-driven market filters for Scout pre-filtering.

Filters are derived from historical trade data analysis. Only markets
belonging to proven-safe buckets reach the Scout agent.

See markets_data_dive.md for the full analysis backing these rules.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Tier 1: Categories with 100% win rate at any entry price
ALLOWED_CATEGORIES: set[str] = {"Economics", "Entertainment"}

# Tier 2: Categories that require a minimum entry price (in cents)
PRICE_GATED_CATEGORIES: dict[str, int] = {
    "Crypto": 96,
    "Sports": 94,
}

# Tier 3: Mention ticker prefixes with 100% historical win rate
ALLOWED_MENTION_PREFIXES: set[str] = {
    "KXPRESMENTION",
    "KXSURVIVORMENTION",
    "KXFEDMENTION",
    "KXJENSENMENTION",
    "KXENTMENTION",
    "KXSCOTUSMENTION",
    "KXTRUMPMENTION",
}

# Future: Weather city ticker prefixes (not yet enabled)
# ALLOWED_WEATHER_PREFIXES: set[str] = {
#     "KXHIGHLAX", "KXLOWTLAX", "KXHIGHMIA", "KXLOWTMIA",
#     "KXHIGHTATL", "KXHIGHTPHX", "KXHIGHTMIN", "KXLOWTMIN",
#     "KXHIGHTDAL", "KXLOWTDAL", "KXHIGHTOKC", "KXHIGHTHOU",
#     "KXHIGHTSATX",
# }

_TICKER_PREFIX_RE = re.compile(r"(KX[A-Z]+)-")


def _extract_ticker_prefix(event_ticker: str) -> str | None:
    """Extract the KX prefix from an event ticker like 'KXPRESMENTION-26MAR25'."""
    match = _TICKER_PREFIX_RE.match(event_ticker)
    return match.group(1) if match else None


def _entry_price(market: dict) -> int:
    """Return the effective entry price (max of yes_ask and no_ask)."""
    return max(market.get("yes_ask") or 0, market.get("no_ask") or 0)


def passes_filter(market: dict) -> bool:
    """Return True only for markets in proven-safe buckets."""
    category = market.get("category", "")

    if category in ALLOWED_CATEGORIES:
        return True

    min_price = PRICE_GATED_CATEGORIES.get(category)
    if min_price is not None and _entry_price(market) >= min_price:
        return True

    prefix = _extract_ticker_prefix(market.get("event_ticker", ""))
    if prefix and prefix in ALLOWED_MENTION_PREFIXES:
        return True

    return False
