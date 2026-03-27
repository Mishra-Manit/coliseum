# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`  
**Updated through**: Mar 27, 2026  
**Scope**: 1,720 completed trades from 1,907 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 1,907 |
| Completed trades | 1,720 |
| Wins (`close_price=100`) | 1,635 |
| Losses (`close_price=0`) | 85 |
| Overall win rate | 95.1% |
| Average entry price | ~94.5c |

The shortlist still works, but the new data reinforces one key lesson: crypto directional markets are only safe at the very top of the book, and only if Scout treats long-horizon BTC contracts as structurally risky even when they print `96¢`.

---

## Where the 85 Losses Come From

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXWTI` | 53 | 10 | Daily WTI remains the worst repeat offender |
| `KXBTCD` | 366 | 9 | BTC directional still safe only at `96c+` |
| `KXBTC` | 98 | 7 | BTC range still fails even at `96c` |
| `KXHIGHDEN` | 36 | 5 | Denver highs remain unusable |
| `KXHIGHNY` | 35 | 5 | NYC highs still need the tight `95c+` gate |
| `KXETHD` | 51 | 3 | ETH directional still needs `96c+` |
| `KXNBAMENTION` | 42 | 3 | announcer wording remains noisy |
| `KXLOWTNYC` | 26 | 3 | NYC lows are not safe |
| `KXTRUMPMENTION` | 16 | 2 | still only safe with `94c+` |

The loss concentration is the same as before: intraday market families with late flip risk, noisy wording markets, and weather prefixes with unstable local conditions.

---

## Deep Findings

## 1. Category rules are still only safe for two buckets

Only these broad categories remain unconditional:

- `Economics`
- `Entertainment`

Everything else is safer as exact prefix logic with price gates.

## 2. Crypto needs a harder distinction between directional, range, and holding horizon

### Directional crypto

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXBTCD` all | 366 | 9 | 375 |
| `KXBTCD` @ `96+` | 91 | 0 | 91 |
| `KXETHD` @ `96+` | 11 | 0 | 11 |
| `KXETH` @ `94+` | 9 | 0 | 9 |
| `KXETH` @ `96+` | 4 | 0 | 4 |

### Range / short-term crypto

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXBTC15M` all | 9 | 0 | 9 |
| `KXETH15M` all | 9 | 0 | 9 |
| `KXBTC` all | 98 | 7 | 105 |
| `KXBTC` @ `96+` | 22 | 1 | 23 |

`KXBTC` range contracts should remain fully blocked. They still lose at `96¢`, including a fresh loss on `KXBTC-26MAR2417-B70025` at `96¢`.

### The Mar 27 Bitcoin stop-loss matters operationally

Your realized loss was:

- `KXBTCD-26MAR2717-T65899.99`
- bought Mar 25 at `96¢ YES`
- closed Mar 27 at `67¢`
- PnL `-0.87` across 3 contracts

That contract did eventually resolve safely for the historical dataset, so it is **not** evidence that `KXBTCD >= 96` is suddenly lossy at resolution. But it is evidence that the current Scout allowlist is missing an important operational distinction:

- the historical shortlist measures **hold-to-resolution**
- your real trade was exposed to a **48-hour BTC path**, not just the final print
- a large intraday drawdown can force an early stop-loss exit even when the contract later wins

The opportunity file for that trade explicitly noted a roughly **48-hour** holding window and only a **7.7% spot cushion** at discovery. That is too much path risk for a supposedly “near-decided” bucket, especially in BTC around options-expiry week.

So the filter conclusion is:

- keep `KXBTCD >= 96` in the zero-loss historical shortlist
- but treat long-dated BTC directional contracts as operationally unsafe for live trading unless a separate horizon/cushion rule is added upstream

### BTC loss anatomy

The actual historical BTC directional losses all occurred below the `96¢` gate:

| Event | Losing contract | Entry |
|------|------------------|-------|
| `KXBTCD-26MAR0901` | YES `$67,250+` | `92¢` |
| `KXBTCD-26MAR1011` | NO `$70,500+` | `95¢` |
| `KXBTCD-26MAR1119` | YES `$70,500+` | `92¢` |
| `KXBTCD-26MAR1515` | YES `$71,500+` | `94¢` |
| `KXBTCD-26MAR1817` | YES `$71,600+` | `93¢` |
| `KXBTCD-26MAR2120` | YES `$70,000+` | `95¢` |
| `KXBTCD-26MAR2208` | YES `$68,300+` | `93¢` |
| `KXBTCD-26MAR2223` | NO `$68,300+` | `95¢` |
| `KXBTCD-26MAR2317` | NO `$70,800+` | `93¢` |

That means the historical filter itself is still correct, but live execution should not blindly extrapolate it to multi-day BTC holds.

## 3. Weather remains mostly the same, with the gated cities still valid

### Unconditional-safe weather prefixes

| Prefix | W | L | n |
|--------|---|---|---|
| `KXHIGHMIA` | 47 | 0 | 47 |
| `KXLOWTLAX` | 26 | 0 | 26 |
| `KXLOWTMIA` | 16 | 0 | 16 |
| `KXHIGHTPHX` | 23 | 0 | 23 |
| `KXHIGHTMIN` | 20 | 0 | 20 |
| `KXLOWTMIN` | 5 | 0 | 5 |
| `KXHIGHTDAL` | 19 | 0 | 19 |
| `KXHIGHTOKC` | 11 | 0 | 11 |
| `KXHIGHTHOU` | 11 | 0 | 11 |
| `KXHIGHTSATX` | 9 | 0 | 9 |

### Safe with price gates

| Prefix | Safe Rule | W | L | n |
|--------|-----------|---|---|---|
| `KXHIGHCHI` | `entry_price >= 93` | 33 | 0 | 33 |
| `KXHIGHAUS` | `entry_price >= 93` | 31 | 0 | 31 |
| `KXHIGHTATL` | `entry_price >= 94` | 16 | 0 | 16 |
| `KXHIGHNY` | `entry_price >= 95` | 14 | 0 | 14 |
| `KXLOWTCHI` | `entry_price >= 94` | 15 | 0 | 15 |

### Still reject

`KXHIGHDEN`, `KXLOWTDEN`, `KXHIGHTSFO`, `KXHIGHTLV`, `KXHIGHTBOS`, and `KXLOWTNYC` still fail the zero-loss bar.

## 4. Mentions still need a precise allowlist

### Safe without a gate

| Prefix | W | L | n |
|--------|---|---|---|
| `KXPRESMENTION` | 13 | 0 | 13 |
| `KXSURVIVORMENTION` | 18 | 0 | 18 |
| `KXFEDMENTION` | 8 | 0 | 8 |
| `KXJENSENMENTION` | 5 | 0 | 5 |
| `KXENTMENTION` | 3 | 0 | 3 |
| `KXSCOTUSMENTION` | 4 | 0 | 4 |

### Safe only with a gate

| Prefix | Safe Rule | W | L | n |
|--------|-----------|---|---|---|
| `KXTRUMPMENTION` | `entry_price >= 94` | 11 | 0 | 11 |

Previously safe buckets did **not** newly break beyond that existing change. The important stale bucket remains `KXTRUMPMENTION` below `94¢`, which is still unsafe.

## 5. Sports are still only safe for definitive winner contracts

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXMLBSTGAME` @ `94+` | 12 | 0 | 12 |
| `KXNASCARRACE` @ `94+` | 12 | 0 | 12 |

Use exact winner-style prefixes, not broad sports category logic.

## 6. Financials are still not default-safe

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXWTIW` @ `94+` | 21 | 0 | 21 |

`KXWTIW >= 94` still qualifies as an optional expansion, but daily WTI and index families remain too lossy.

---

## Recommended Scout Filter Set

### Core 100% filter set: 592W / 0L

| Rule Type | Rule |
|-----------|------|
| Category | `Economics` |
| Category | `Entertainment` |
| Crypto | `KXBTCD` and `entry_price >= 96` |
| Crypto | `KXETHD` and `entry_price >= 96` |
| Crypto | `KXETH` and `entry_price >= 96` |
| Sports | `KXMLBSTGAME` and `entry_price >= 94` |
| Sports | `KXNASCARRACE` and `entry_price >= 94` |
| Weather | `KXHIGHMIA`, `KXLOWTLAX`, `KXLOWTMIA`, `KXHIGHTPHX`, `KXHIGHTMIN`, `KXLOWTMIN`, `KXHIGHTDAL`, `KXHIGHTOKC`, `KXHIGHTHOU`, `KXHIGHTSATX` |
| Weather | `KXHIGHCHI` and `entry_price >= 93` |
| Weather | `KXHIGHAUS` and `entry_price >= 93` |
| Weather | `KXHIGHTATL` and `entry_price >= 94` |
| Weather | `KXHIGHNY` and `entry_price >= 95` |
| Weather | `KXLOWTCHI` and `entry_price >= 94` |
| Mentions | `KXPRESMENTION`, `KXSURVIVORMENTION`, `KXFEDMENTION`, `KXJENSENMENTION`, `KXENTMENTION`, `KXSCOTUSMENTION` |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` |
| Other | `KXBTC15M`, `KXETH15M` |

### Optional expansion: 602W / 0L

Add:

- `KXWTIW` and `entry_price >= 94`

---

## Performance of the Updated Core Filter

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 592 |
| Losses | 0 |
| Coverage of completed trades | 34.4% |
| Average entry price | 94.73c |

### Core + optional `KXWTIW >= 94`

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 613 |
| Losses | 0 |
| Coverage of completed trades | 35.6% |
| Average entry price | 94.70c |

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTC` | still loses at `96c` |
| long-horizon `KXBTCD` live trades | path risk can trigger stop losses before a winning final print |
| `KXWTI` | daily oil remains structurally unsafe |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | index gap risk |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | weather variability remains too high |
| `KXHIGHTSFO`, `KXHIGHTLV`, `KXHIGHTBOS` | microclimate / range-snap behavior |
| `KXNBAMENTION`, `KXTRUMPSAY`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION` | wording variance |

---

## Scout Implementation Guidance

The Scout prefilter should still be an auditable allowlist:

1. derive `prefix = event_ticker.partition("-")[0]`
2. compute the actionable Scout entry price for the selected side
3. allow only exact category/prefix rules with explicit price gates

Implementation shape:

```python
SAFE_CATEGORIES = {"Economics", "Entertainment"}

SAFE_EVENT_PREFIXES = {
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

PRICE_GATED_EVENT_PREFIXES = {
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
```

The extra BTC lesson from the Mar 27 stop-loss should be implemented outside this file: add a separate live-trading guard for long holding windows or weak strike cushion on crypto directional markets.

---

## Bottom Line

The historical shortlist is still valid and actually grew from `560` to `592` qualifying zero-loss trades. No new core bucket became unsafe beyond the already-known `KXTRUMPMENTION < 94` issue, and no new core bucket needed removal.

The most important new refinement is operational rather than statistical:

1. keep `KXBTCD >= 96` in the historical zero-loss allowlist
2. keep rejecting `KXBTC` range contracts outright
3. treat multi-day BTC directional holds as a separate live-risk problem, because stop-losses can turn a historical winner into a realized loser before settlement
