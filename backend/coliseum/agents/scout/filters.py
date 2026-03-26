"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = {"Economics", "Entertainment"}

SAFE_EVENT_PREFIXES: set[str] = {
    "KXHIGHMIA",
    "KXLOWTLAX",
    "KXLOWTMIA",
    "KXHIGHTPHX",
    "KXHIGHTMIN",
    "KXLOWTMIN",
    "KXHIGHTDAL",
    "KXHIGHTOKC",
    "KXHIGHTHOU",
    "KXHIGHTSATX",
    "KXPRESMENTION",
    "KXSURVIVORMENTION",
    "KXFEDMENTION",
    "KXJENSENMENTION",
    "KXENTMENTION",
    "KXSCOTUSMENTION",
    "KXBTC15M",
    "KXETH15M",
}

PRICE_GATED_EVENT_PREFIXES: dict[str, int] = {
    "KXBTCD": 96,
    "KXETHD": 96,
    "KXETH": 96,
    "KXMLBSTGAME": 94,
    "KXNASCARRACE": 94,
    "KXHIGHCHI": 93,
    "KXHIGHAUS": 93,
    "KXHIGHTATL": 94,
    "KXHIGHNY": 95,
    "KXLOWTCHI": 94,
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
