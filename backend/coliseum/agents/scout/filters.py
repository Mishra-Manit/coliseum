"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min - unconditional (all zero-loss, event diversity >= 5)
    "KXETH15M",   # 39W/0L, 39 events
    "KXSOL15M",   # 21W/0L, 21 events
    "KXXRP15M",   # 15W/0L, 15 events
    # Sports - unconditional
    "KXMLBSTGAME",  # 22W/0L, 12 events
    "KXWBCGAME",    # 8W/0L, 5 events
    # Mentions - unconditional
    "KXPRESMENTION",      # 13W/0L, 5 events
    "KXPOLITICSMENTION",  # 10W/0L, 6 events
    # Economics - unconditional
    "KXJOBLESSCLAIMS",  # 14W/0L, 8 events
    "KXAAAGASW",        # 24W/0L, 7 events (weekly gas, distinct from daily)
    "KXTSAW",           # 11W/0L, 7 events (TSA weekly passengers)
    # Entertainment - unconditional
    "KXRT",                # 16W/0L, 9 events (Rotten Tomatoes)
    "KXARTISTSTREAMSU",    # 8W/0L, 8 events (weekly Luminate stream targets)
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto ETH threshold - tightened after a 94c loss in refreshed data
    "KXETH": 95,     # 24W/0L/17 events at gate
    # Crude oil weekly - only surviving commodity
    "KXWTIW": 94,    # 57W/0L/8 events at gate
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
