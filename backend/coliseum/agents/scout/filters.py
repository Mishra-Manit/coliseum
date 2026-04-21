"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min - unconditional (all zero-loss, event diversity >= 5)
    "KXETH15M",   # 28W/0L, 28 events
    "KXSOL15M",   # 19W/0L, 19 events
    "KXXRP15M",   # 14W/0L, 14 events
    # Commodities - unconditional
    "KXGOLDD",    # 19W/0L, 9 events
    "KXBRENTD",   # 13W/0L, 5 events
    # Sports - unconditional
    "KXMLBSTGAME",  # 22W/0L, 12 events
    "KXWBCGAME",    # 8W/0L, 5 events
    # Mentions - unconditional
    "KXPRESMENTION",      # 13W/0L, 5 events
    "KXPOLITICSMENTION",  # 10W/0L, 6 events
    # Economics - unconditional
    "KXJOBLESSCLAIMS",  # 12W/0L, 6 events
    "KXAAAGASW",        # 15W/0L, 5 events
    "KXTSAW",           # 8W/0L, 5 events (TSA weekly passengers)
    # Entertainment - unconditional
    "KXRT",  # 10W/0L, 6 events (Rotten Tomatoes)
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crypto directional (structural family requires >= 96c)
    "KXETHD": 96,  # 39W/0L/28 events at gate
    # Crypto range (15-min gate added after losses below 94c)
    "KXBTC15M": 94,  # 17W/0L/17 events at gate
    # Crypto ETH threshold (promoted from 96c; CSV shows 25W/0L/15 events at 94c)
    "KXETH": 94,
    # Crude oil weekly
    "KXWTIW": 94,  # 50W/0L/6 events at gate
    # Weather (capped at 3 per policy, all price-gated)
    "KXHIGHMIA": 96,   # 25W/0L/19 events at gate (consistent with prior policy)
    "KXHIGHTDAL": 96,  # data clean at 96c
    "KXLOWTMIA": 96,   # data clean at 96c
    # Daily gas - demoted from unconditional after KXAAAGASD-26APR21-4.025 live loss
    "KXAAAGASD": 96,
    # Mentions (Trump-adjacent structural family requires >= 94c)
    "KXTRUMPMENTION": 94,   # 27W/0L/9 events at gate
    "KXTRUMPMENTIONB": 95,  # 16W/0L/6 events at gate
    "KXTRUMPSAY": 94,       # 25W/0L/6 events at gate
    # Politics / entertainment long-form
    "KXAPRPOTUS": 93,    # 13W/0L/5 events at gate
    "KXALBUMSALES": 95,  # 16W/0L/9 events at gate
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
