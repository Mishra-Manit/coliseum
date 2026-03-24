# Markets Data Dive: Finding 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv` (tracked via `track.py`)
**Period**: Mar 7 - Mar 23, 2026 (17 days of data collection)
**Scope**: 1,184 completed trades (82 pending and 1 voided excluded)

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total completed | 1,184 |
| Wins (close_price=100) | 1,122 |
| Losses (close_price=0) | 62 |
| Overall win rate | 94.8% |
| Average entry price | ~94c |

The system already performs well, but 62 losses at 92-96c entry means losing the full entry on each. A single loss wipes out ~16-24 wins worth of profit. Eliminating losses entirely is critical.

---

## Where the 62 Losses Come From

### By Category

| Category | W | L | Win Rate | n |
|----------|---|---|----------|---|
| Economics | 32 | 0 | 100.0% | 32 |
| Entertainment | 24 | 0 | 100.0% | 24 |
| Sports | 53 | 1 | 98.1% | 54 |
| Crypto | 363 | 17 | 95.5% | 380 |
| Mentions | 138 | 7 | 95.2% | 145 |
| Climate and Weather | 430 | 24 | 94.7% | 454 |
| Financials | 73 | 9 | 89.0% | 82 |
| Politics | 5 | 2 | 71.4% | 7 |
| Science and Technology | 4 | 1 | 80.0% | 5 |

**Economics and Entertainment have never lost a single trade.**

### Loss Breakdown by Event Type

| Event Type | Losses | Common Pattern |
|------------|--------|----------------|
| Bitcoin price | 13 | Volatile, price can swing 2-5% in hours |
| High temperature | 18 | Weather forecasts off by 1-3 degrees |
| Low temperature | 7 | Same forecast volatility |
| WTI oil price | 4 | Commodity volatility |
| S&P 500 / Nasdaq | 5 | Index can gap on news |
| Ethereum price | 3 | Crypto volatility |
| NBA announcer mentions | 3 | Unpredictable word choice in commentary |
| SOL price | 1 | Crypto volatility |
| Various other | 8 | SNL, NASCAR, Politics, etc. |

---

## Deep Analysis: What Makes Events Win or Lose?

### Entry Price Effect

| Entry Price | W | L | Win Rate |
|-------------|---|---|----------|
| 92 | 181 | 13 | 93.3% |
| 93 | 200 | 15 | 93.0% |
| 94 | 196 | 10 | 95.1% |
| 95 | 270 | 13 | 95.4% |
| 96 | 275 | 11 | 96.2% |

Higher entry price = slightly better win rate, but the effect is moderate. Price alone is not enough to filter.

### Crypto: Entry Price is the Key

| Filter | W | L | Win Rate | n |
|--------|---|---|----------|---|
| All Crypto | 363 | 17 | 95.5% | 380 |
| Crypto @ 94+ | 227 | 8 | 96.6% | 235 |
| Crypto @ 95+ | 171 | 6 | 96.6% | 177 |
| **Crypto @ 96** | **85** | **0** | **100.0%** | **85** |

At 96c entry, crypto has resolved correctly every single time (n=85). This includes Bitcoin (68), Ethereum (15), SOL (1), XRP (1). The 4c spread to resolution is narrow enough that even volatile crypto doesn't swing back.

### Weather: City Matters Enormously

**Cities with 0 losses (all n >= 5):**

| City | W | L | Win Rate | n |
|------|---|---|----------|---|
| Los Angeles | 57 | 0 | 100.0% | 57 |
| Miami | 49 | 0 | 100.0% | 49 |
| Atlanta | 19 | 0 | 100.0% | 19 |
| Phoenix | 17 | 0 | 100.0% | 17 |
| Minneapolis | 13 | 0 | 100.0% | 13 |
| Dallas | 13 | 0 | 100.0% | 13 |
| Oklahoma City | 9 | 0 | 100.0% | 9 |
| Houston | 8 | 0 | 100.0% | 8 |
| San Antonio | 5 | 0 | 100.0% | 5 |

**Cities with losses:**

| City | W | L | Win Rate | n | Note |
|------|---|---|----------|---|------|
| NYC | 38 | 8 | 82.6% | 46 | Worst performer |
| Denver | 35 | 7 | 83.3% | 42 | High altitude = unstable |
| San Francisco | 16 | 2 | 88.9% | 18 | Microclimates |
| Las Vegas | 16 | 2 | 88.9% | 18 | Desert temp swings |
| Austin | 32 | 1 | 97.0% | 33 | 1 outlier loss |
| Chicago | 35 | 1 | 97.2% | 36 | 1 outlier loss |

**Why safe cities win**: Los Angeles, Miami, Phoenix, Houston, Dallas, and Atlanta have stable, predictable temperature patterns. When forecasts put them at 92-96% probability, the weather rarely surprises. Denver, NYC, and San Francisco have much more volatile microclimates.

The corresponding **safe city ticker prefixes** are:
`KXHIGHLAX`, `KXLOWTLAX`, `KXHIGHMIA`, `KXLOWTMIA`, `KXHIGHTATL`, `KXHIGHTPHX`, `KXHIGHTMIN`, `KXLOWTMIN`, `KXHIGHTDAL`, `KXLOWTDAL`, `KXHIGHTOKC`, `KXHIGHTHOU`, `KXHIGHTSATX`

### Sports: Almost Perfect

| Filter | W | L | Win Rate | n |
|--------|---|---|----------|---|
| All Sports | 53 | 1 | 98.1% | 54 |
| Sports @ 94+ | 36 | 0 | 100.0% | 36 |
| Sports YES side | 19 | 0 | 100.0% | 19 |

The single Sports loss: NASCAR top-10 finish at 93c entry. At 94c+ entry, Sports is perfect. The completed events are mostly definitive (race winners, game results) -- outcomes that don't reverse once determined.

### Mentions: Sub-Type Matters

**100% win rate mention types (n >= 5):**

| Mention Type | W | L | n | Ticker Prefix |
|--------------|---|---|---|---------------|
| Press Mention | 13 | 0 | 13 | KXPRESMENTION |
| Survivor TV | 11 | 0 | 11 | KXSURVIVORMENTION |
| Fed/Powell | 8 | 0 | 8 | KXFEDMENTION |
| Trump Mention | 6 | 0 | 6 | KXTRUMPMENTION |
| Jensen Huang | 5 | 0 | 5 | KXJENSENMENTION |
| Entertainment | 3 | 0 | 3 | KXENTMENTION |
| SCOTUS | 3 | 0 | 3 | KXSCOTUSMENTION |

**Lossy mention types:**

| Mention Type | W | L | Win Rate | n | Why Losses |
|--------------|---|---|----------|---|------------|
| NBA Announcer | 40 | 3 | 93.0% | 43 | Unpredictable commentary (lost on "Playoff", "American Airlines") |
| Trump Say | 20 | 1 | 95.2% | 21 | Unpredictable phrase usage |
| MMA/Fight | 8 | 1 | 88.9% | 9 | Niche commentary hard to predict |
| SNL | 3 | 1 | 75.0% | 4 | Comedy is inherently unpredictable |

### Financials: Avoid Entirely or Be Very Selective

| Sub-Type | W | L | Win Rate | n |
|----------|---|---|----------|---|
| WTI Weekly (KXWTIW) | 26 | 1 | 96.3% | 27 |
| WTI Daily (KXWTI) | 25 | 3 | 89.3% | 28 |
| S&P Range (KXINX) | 11 | 2 | 84.6% | 13 |
| S&P Above (KXINXU) | 10 | 2 | 83.3% | 12 |
| Nasdaq (KXNASDAQ) | 1 | 1 | 50.0% | 2 |

Stock indices and oil are too volatile for reliable near-decided trading. The losses are from intraday price swings.

### Politics: Too Small and Too Risky

Only 7 trades, 2 losses (71.4%). Avoid entirely.

---

## The 100% Win-Rate Strategy

### Filter Rules (416W / 0L = 100.0%)

Apply these filters to the Scout agent's market selection:

#### Tier 1: Always Allow (unconditional pass)

| Rule | Win Rate | Sample Size |
|------|----------|-------------|
| Category = `Economics` | 100% | 32 |
| Category = `Entertainment` | 100% | 24 |

#### Tier 2: Allow with Price Gate

| Rule | Win Rate | Sample Size |
|------|----------|-------------|
| Category = `Crypto` AND entry_price >= 96 | 100% | 85 |
| Category = `Sports` AND entry_price >= 94 | 100% | 36 |

#### Tier 3: Allow by Event Ticker Prefix

| Rule | Win Rate | Sample Size |
|------|----------|-------------|
| Weather in perfect cities (see list below) | 100% | 190 |
| Safe mention types (see list below) | 100% | 49 |

**Perfect weather city ticker prefixes:**
- `KXHIGHLAX`, `KXLOWTLAX` (Los Angeles)
- `KXHIGHMIA`, `KXLOWTMIA` (Miami)
- `KXHIGHTATL` (Atlanta)
- `KXHIGHTPHX` (Phoenix)
- `KXHIGHTMIN`, `KXLOWTMIN` (Minneapolis)
- `KXHIGHTDAL`, `KXLOWTDAL` (Dallas)
- `KXHIGHTOKC` (Oklahoma City)
- `KXHIGHTHOU` (Houston)
- `KXHIGHTSATX` (San Antonio)

**Safe mention ticker prefixes:**
- `KXPRESMENTION` (Press Conference)
- `KXSURVIVORMENTION` (Survivor TV)
- `KXFEDMENTION` (Federal Reserve)
- `KXJENSENMENTION` (Jensen Huang/NVIDIA)
- `KXENTMENTION` (Entertainment)
- `KXSCOTUSMENTION` (Supreme Court)
- `KXTRUMPMENTION` (Trump -- not `KXTRUMPSAY`, which has losses)

### What This Strategy Rejects

| Rejected | Why |
|----------|-----|
| Financials (all) | S&P/Nasdaq/WTI too volatile (89% win rate) |
| Politics (all) | Too few trades, 71% win rate |
| Science and Technology | 80% win rate, tiny sample |
| Crypto at 92-95c | 17 losses across BTC/ETH at these prices |
| Sports at 92-93c | 1 loss in NASCAR at 93c |
| Weather in risky cities | Denver, NYC, San Francisco, Las Vegas, etc. (83-89% win rates) |
| NBA/Fight/SNL mentions | Unpredictable commentary |
| Trump Say (KXTRUMPSAY) | Unpredictable phrase usage |

### Strategy Performance Summary

| Metric | Value |
|--------|-------|
| **Win rate** | **100.0%** |
| Total qualifying trades | 416 |
| Losses | 0 |
| Coverage of all trades | 35.1% (416/1184) |
| Avg entry price | 94.6c |
| Avg profit per trade | 5.4c (5.4%) |
| Avg qualifying trades/day | ~24.5 |

---

## Implementation Notes for Scout Agent

### How to Apply These Filters

The Scout agent currently receives a pre-fetched market list with `event_ticker`, `category`, `yes_ask`, and `no_ask` fields. The filter logic should be:

```python
PERFECT_WEATHER_PREFIXES = {
    "KXHIGHLAX", "KXLOWTLAX", "KXHIGHMIA", "KXLOWTMIA",
    "KXHIGHTATL", "KXHIGHTPHX", "KXHIGHTMIN", "KXLOWTMIN",
    "KXHIGHTDAL", "KXLOWTDAL", "KXHIGHTOKC", "KXHIGHTHOU",
    "KXHIGHTSATX",
}

SAFE_MENTION_PREFIXES = {
    "KXPRESMENTION", "KXSURVIVORMENTION", "KXFEDMENTION",
    "KXJENSENMENTION", "KXENTMENTION", "KXSCOTUSMENTION",
    "KXTRUMPMENTION",
}

ALWAYS_ALLOW_CATEGORIES = {"Economics", "Entertainment"}


def passes_filter(market: dict) -> bool:
    category = market.get("category", "")
    event_ticker = market.get("event_ticker", "")
    entry_price = max(
        market.get("yes_ask") or 0,
        market.get("no_ask") or 0,
    )

    # Tier 1: Always allow
    if category in ALWAYS_ALLOW_CATEGORIES:
        return True

    # Tier 2: Price-gated
    if category == "Crypto" and entry_price >= 96:
        return True
    if category == "Sports" and entry_price >= 94:
        return True

    # Tier 3: Ticker-prefix based
    ticker_prefix = re.match(r"(KX[A-Z]+)-", event_ticker)
    if ticker_prefix:
        prefix = ticker_prefix.group(1)
        if prefix in PERFECT_WEATHER_PREFIXES:
            return True
        if prefix in SAFE_MENTION_PREFIXES:
            return True

    return False
```

### Trade-offs

- **Strictness vs volume**: This filter passes 35% of markets. That is ~24 qualifying markets/day from 17 days of data. More than enough for a system that selects 1 trade per cycle.
- **Overfitting risk**: The weather city list is based on 17 days of data. Cities like Chicago (35W/1L) and Austin (32W/1L) were excluded to maintain the 0-loss guarantee, but could be added if the strategy needs more volume. Monitor and potentially expand the safe-city list as more data accumulates.
- **Crypto at 96c**: The profit margin is only 4c per trade vs 6-8c for other categories. But 85 trades with 0 losses is strong signal.
- **New event types**: As Kalshi adds new categories or events, default to REJECT until data proves them safe.
