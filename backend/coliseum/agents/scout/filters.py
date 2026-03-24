"""Historical safety rules for Scout market prefiltering."""

SAFE_CATEGORIES: set[str] = {"Economics", "Entertainment"}

PRICE_GATED_CATEGORIES: dict[str, int] = {
    "Crypto": 96,
    "Sports": 94,
}

SAFE_EVENT_PREFIXES: set[str] = {
    "KXPRESMENTION",
    "KXSURVIVORMENTION",
    "KXFEDMENTION",
    "KXJENSENMENTION",
    "KXENTMENTION",
    "KXSCOTUSMENTION",
    "KXTRUMPMENTION",
}


def _event_prefix(event_ticker: str) -> str:
    """Return the event prefix before the first dash, if present."""
    return event_ticker.partition("-")[0]


def passes_filter(category: str, event_ticker: str, entry_price_cents: int) -> bool:
    """Return True only for historically safe market buckets."""
    if category in SAFE_CATEGORIES:
        return True

    min_price = PRICE_GATED_CATEGORIES.get(category)
    if min_price is not None and entry_price_cents >= min_price:
        return True

    return _event_prefix(event_ticker) in SAFE_EVENT_PREFIXES
