"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min - unconditional
    "KXETH15M",
    "KXSOL15M",
    "KXXRP15M",
    # Commodities - unconditional
    "KXGOLDD",
    "KXGOLDW",    # 16W/0L
    "KXBRENTW",   # 19W/0L
    # Sports - unconditional
    "KXWBCGAME",
    "KXMLBSTGAME",
    "KXNASCARRACE",  # 13W/0L
    # Mentions - unconditional
    "KXPRESMENTION",
    # Economics - unconditional
    "KXJOBLESSCLAIMS",
    "KXAAAGASW",  # 15W/0L weekly gas prices
    "KXAAAGASD",  # 11W/0L daily gas prices
    # Entertainment - unconditional
    "KXRT",
    # Weather - losses only below new min_price floor (94)
    "KXLOWTLAX",  # 69W/1L, loss at 92 only
    "KXLOWTCHI",  # 55W/1L, loss at 93 only
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto directional
    "KXETHD": 96,
    "KXBTCD": 95,  # 498W/13L at 95+
    "KXETH": 94,   # 25W/0L at 94+
    # Crypto 15-min (gate added after 1 loss at < 94c)
    "KXBTC15M": 94,
    # Crude oil weekly
    "KXWTIW": 94,
    # Weather (3 gates only)
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
