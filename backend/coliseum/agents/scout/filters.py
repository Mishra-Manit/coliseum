"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = {"Economics"}

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min - unconditional
    "KXETH15M",
    "KXSOL15M",
    "KXXRP15M",
    # Sports - unconditional
    "KXWBCGAME",
    "KXMLBSTGAME",
    # Mentions - unconditional
    "KXPRESMENTION",
    "KXSURVIVORMENTION",
    "KXHEGSETHMENTION",
    "KXGOLDD",
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto directional
    "KXETHD": 96,
    "KXBTCD": 94,
    # Crypto 15-min (gate added after 1 loss at < 94c)
    "KXBTC15M": 94,
    # Crude oil weekly
    "KXWTIW": 94,
    # Weather - only zero-loss prefixes kept, price-gated for safety
    "KXHIGHMIA": 96,
    "KXHIGHTDAL": 96,
    "KXLOWTMIA": 96,
    # Mentions
    "KXTRUMPMENTION": 94,
    "KXTRUMPSAY": 94,
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
