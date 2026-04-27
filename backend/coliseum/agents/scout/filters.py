"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min - unconditional (all zero-loss, event diversity >= 5)
    "KXETH15M",   # 33W/0L, 33 events
    "KXSOL15M",   # 20W/0L, 20 events
    "KXXRP15M",   # 15W/0L, 15 events
    # Sports - unconditional
    "KXMLBSTGAME",  # 22W/0L, 12 events
    "KXWBCGAME",    # 8W/0L, 5 events
    # Mentions - unconditional
    "KXPRESMENTION",      # 13W/0L, 5 events
    "KXPOLITICSMENTION",  # 10W/0L, 6 events
    # Economics - unconditional
    "KXJOBLESSCLAIMS",  # 13W/0L, 7 events
    "KXAAAGASW",        # 20W/0L, 6 events (weekly gas, distinct from daily)
    "KXTSAW",           # 10W/0L, 6 events (TSA weekly passengers)
    # Entertainment - unconditional
    "KXRT",                # 14W/0L, 8 events (Rotten Tomatoes)
    "KXARTISTSTREAMSU",    # 8W/0L, 8 events (weekly Luminate stream targets)
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto directional (structural family requires >= 96c)
    "KXETHD": 96,    # 46W/0L/33 events at gate
    # Crypto 15-min BTC (gate added after losses below 94c)
    "KXBTC15M": 94,  # 18W/0L/18 events at gate
    # Crypto ETH threshold
    "KXETH": 94,     # 32W/0L/17 events at gate
    # Crude oil weekly - only surviving commodity
    "KXWTIW": 94,    # 54W/0L/7 events at gate
    # Weather (capped at 3 per policy, all price-gated)
    "KXHIGHMIA": 96,   # 28W/0L/22 events at gate
    "KXHIGHTDAL": 96,  # 19W/0L/17 events at gate
    "KXLOWTMIA": 96,   # 15W/0L/13 events at gate (clean at all gates)
    # Mentions (Trump-adjacent structural family requires >= 94c)
    "KXTRUMPMENTION": 94,   # 27W/0L/9 events at gate
    "KXTRUMPMENTIONB": 95,  # 16W/0L/6 events at gate
    # Politics long-form approval rating
    "KXAPRPOTUS": 93,    # 15W/0L/6 events at gate
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
