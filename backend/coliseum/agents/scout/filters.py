"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Crypto 15-min ranges - unconditional (range-resolved, 0 losses ever)
    "KXETH15M",   # 34W/0L, 34 events
    "KXSOL15M",   # 20W/0L, 20 events
    "KXXRP15M",   # 15W/0L, 15 events
    # Sports - unconditional (game-resolved, no price-stop exposure)
    "KXMLBSTGAME",  # 22W/0L, 12 events
    "KXWBCGAME",    # 8W/0L, 5 events
    # Mentions counters - unconditional (low intraday volatility)
    "KXPRESMENTION",      # 13W/0L, 5 events
    "KXPOLITICSMENTION",  # 10W/0L, 6 events
    # Economics weekly/release prints - unconditional (point-in-time data)
    "KXJOBLESSCLAIMS",  # 14W/0L, 8 events
    "KXAAAGASW",        # 20W/0L, 6 events (weekly gas - daily KXAAAGASD removed)
    "KXTSAW",           # 10W/0L, 6 events
    # Entertainment - unconditional (deterministic releases)
    "KXRT",                # 14W/0L, 8 events (Rotten Tomatoes)
    "KXARTISTSTREAMSU",    # 8W/0L, 8 events (Luminate weekly streams)
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    # Crude oil weekly - only commodity that has survived live trading
    "KXWTIW": 94,    # 54W/0L/7 events at gate (4W/0L live in April)
    # ETH threshold (NOT directional) - tightened from 94c → 95c
    "KXETH": 95,     # 32W/0L/19 events at >=95c gate
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
