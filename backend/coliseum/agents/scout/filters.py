"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = {"Economics"}

SAFE_EVENT_PREFIXES: set[str] = {
    # Weather - unconditional
    "KXHIGHMIA",
    "KXHIGHPHIL",
    "KXLOWTMIA",
    "KXHIGHTDAL",
    "KXHIGHTSATX",
    "KXLOWTAUS",
    # Crypto 15-min - unconditional
    "KXETH15M",
    "KXSOL15M",
    # Sports - unconditional
    "KXWBCGAME",
    # Mentions - unconditional
    "KXPRESMENTION",
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto directional
    "KXETHD": 96,
    # Crypto 15-min (gate added after 1 loss at < 94c)
    "KXBTC15M": 94,
    # Weather - demoted from unconditional (losses added in latest data)
    "KXHIGHLAX": 93,
    "KXLOWTLAX": 93,
    "KXHIGHTPHX": 94,
    "KXHIGHTOKC": 94,
    "KXHIGHTMIN": 96,
    "KXHIGHTHOU": 95,
    # Weather - existing entries with gates raised
    "KXHIGHCHI": 94,
    "KXHIGHAUS": 95,
    # Weather - existing entries, gates unchanged
    "KXHIGHTATL": 94,
    "KXLOWTCHI": 94,
    # Weather - new additions (promoted from watchlist)
    "KXHIGHTLV": 96,
    "KXHIGHTDC": 96,
    "KXHIGHTSFO": 94,
    # Sports
    "KXMLBSTGAME": 94,
    # Mentions
    "KXTRUMPMENTION": 94,
}


def _event_prefix(event_ticker: str) -> str:
    """Return the event prefix before the first dash, if present."""
    return event_ticker.partition("-")[0]


def passes_filter(category: str, event_ticker: str, entry_price_cents: int) -> bool:
    """Return True only for historically safe market buckets."""
    if category in SAFE_CATEGORIES:
        return True

    prefix = _event_prefix(event_ticker)
    if prefix in SAFE_EVENT_PREFIXES:
        return True

    min_price = PRICE_GATED_EVENT_PREFIXES.get(prefix)
    return min_price is not None and entry_price_cents >= min_price
