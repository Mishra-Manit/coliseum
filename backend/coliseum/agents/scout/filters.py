"""Historical safety rules for Scout market prefiltering.

Flat allowlist plus a single global price floor. A family is included only if it
clears all three thresholds on the combined record from every data source we have:

  >= 15 resolved trades at >= 94c entry
  >= 5 distinct events (an event, not a trade, is the independent unit)
  >= 97.5% accuracy

Sources combined per family:
  CSV   - backend/monitoring/markets.csv shadow tracker, entries >= 94c
  LIVE  - trade_closes in Supabase (real fills, Apr-Jun 2026)
  OOS   - post-2026-07-08 paper decisions resolved against Kalshi outcomes.
          This is the only forward-tested source; families carrying it are marked.

Break-even at a 95c entry is 95% accuracy, so the 97.5% bar leaves roughly
2.5 points of margin. Notation is (combined W/L, distinct events).
"""

MIN_ENTRY_PRICE_CENTS = 94
"""Global floor. The allowlist was fit on 94-96c entries and does not generalize
below that, so no family is tradable outside the band regardless of prefix."""

SAFE_CATEGORIES: set[str] = set()

SAFE_EVENT_PREFIXES: set[str] = {
    # Commodities - strongest category overall
    "KXWTIW",      # 130W/2L, 9 events   [OOS: 50W/1L]
    "KXBRENTW",    # 33W/0L, 6 events
    "KXAAAGASW",   # 50W/1L, 7 events    [OOS: 21W/0L]
    "KXGOLDW",     # 16W/0L, 5 events
    # Crypto 15-minute up/down - every trade is its own event
    "KXETH15M",    # 27W/0L, 26 events
    "KXBTC15M",    # 22W/0L, 22 events
    "KXSOL15M",    # 17W/0L, 17 events
    # Crypto spot ladder
    "KXETH",       # 51W/1L, 25 events   [OOS: 5W/0L]
    # Economics
    "KXJOBLESSCLAIMS",  # 32W/0L, 6 events   [OOS: 19W/0L]
    "KXTSAW",           # 15W/0L, 7 events   [OOS: 4W/0L]
    # Mentions
    "KXTRUMPMENTION",   # 29W/0L, 9 events
    # Entertainment
    "KXRT",             # 41W/1L, 7 events   [OOS: 22W/1L]
    # Weather - highest-diversity tickers only. These are correlated with each
    # other on any given day, so the count is deliberately kept small.
    "KXHIGHTPHX",  # 73W/0L, 39 events
    "KXHIGHTSFO",  # 74W/1L, 41 events
    "KXLOWTLAX",   # 64W/1L, 40 events
    "KXHIGHCHI",   # 129W/3L, 53 events
}


def _event_prefix(event_ticker: str) -> str:
    """Return the event prefix before the first dash, if present."""
    return event_ticker.partition("-")[0]


def passes_filter(category: str, event_ticker: str, entry_price_cents: int) -> bool:
    """Return True only for historically safe market buckets."""
    if entry_price_cents < MIN_ENTRY_PRICE_CENTS:
        return False

    if category in SAFE_CATEGORIES:
        return True

    return _event_prefix(event_ticker) in SAFE_EVENT_PREFIXES
