# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Updated through**: Mar 30, 2026
**Scope**: 1,910 completed trades from 1,997 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 1,997 |
| Completed trades | 1,910 |
| Wins (`close_price=100`) | 1,815 |
| Losses (`close_price=0`) | 95 |
| Overall win rate | 95.0% |
| Average entry price | ~94.2c |

---

## Where the 95 Losses Come From

### By Category

| Category | W | L | n | Win Rate |
|----------|---|---|---|----------|
| Climate and Weather | 674 | 33 | 707 | 95.3% |
| Crypto | 658 | 27 | 685 | 96.1% |
| Financials | 147 | 17 | 164 | 89.6% |
| Mentions | 189 | 12 | 201 | 94.0% |
| Politics | 11 | 3 | 14 | 78.6% |
| Sports | 53 | 1 | 54 | 98.1% |
| Science and Technology | 5 | 1 | 6 | 83.3% |
| Economics | 35 | 0 | 35 | 100.0% |
| Entertainment | 43 | 0 | 43 | 100.0% |

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXBTCD` | 394 | 13 | BTC directional still safe only at `96c+` |
| `KXWTI` | 60 | 10 | Daily WTI remains the worst repeat offender |
| `KXBTC` | 115 | 8 | BTC range still fails even at `96c` |
| `KXHIGHDEN` | 39 | 5 | Denver highs remain unusable (lossy even at `96c`) |
| `KXHIGHNY` | 39 | 5 | NYC highs still need the tight `95c+` gate |
| `KXHIGHTBOS` | 26 | 4 | Boston still lossy at every gate through `96c` |
| `KXETHD` | 62 | 4 | ETH directional still needs `96c+` |
| `KXHIGHTLV` | 21 | 3 | Las Vegas still too risky |
| `KXNBAMENTION` | 42 | 3 | announcer wording remains noisy at every gate |
| `KXLOWTNYC` | 29 | 3 | NYC lows are not safe (lossy even at `96c`) |
| `KXLOWTDEN` | 17 | 3 | Denver lows still fail |
| `KXINX` | 26 | 3 | Index gap risk, lossy at every gate |

---

## Deep Findings

### Event diversity matters more than trade count

This refresh introduced an event diversity audit. A prefix with 18 trades from 2 events is not 18 independent observations — it is 2 observations with 9 correlated contracts each. Several prefixes from the previous filter had misleadingly high trade counts:

| Prefix | Trades | Events | Status |
|--------|--------|--------|--------|
| `KXSURVIVORMENTION` | 18 | 2 | Removed (2 TV episodes) |
| `KXFEDMENTION` | 8 | 1 | Removed (1 Fed press conference) |
| `KXJENSENMENTION` | 5 | 1 | Removed (1 appearance) |
| `KXSCOTUSMENTION` | 4 | 2 | Removed |
| `KXENTMENTION` | 3 | 3 | Removed (insufficient trades) |
| `KXLOWTMIN` | 0 | 0 | Removed (no evidence) |

These may re-qualify as they accumulate more distinct events.

## 1. Category rules are still only safe for two buckets

Only these broad categories remain unconditional:

- `Economics` (35W, 0L)
- `Entertainment` (43W, 0L)

Everything else is safer as exact prefix logic with price gates.

## 2. Crypto needs a hard distinction between directional, range, and 15-min families

### Directional crypto

| Prefix / Rule | W | L | n | Events |
|---------------|---|---|---|--------|
| `KXBTCD` all | 394 | 13 | 407 | — |
| `KXBTCD` @ `96+` | 102 | 0 | 102 | 60 |
| `KXETHD` all | 62 | 4 | 66 | — |
| `KXETHD` @ `96+` | 12 | 0 | 12 | 10 |
| `KXETH` all | 25 | 1 | 26 | — |
| `KXETH` @ `96+` | 5 | 0 | 5 | 5 |

`KXETH` is kept at the conservative `96c` gate. While `94c+` shows 12W/0L, the tighter gate provides a larger margin of safety consistent with `KXBTCD` and `KXETHD`.

`KXSOLD` (10W/0L/3 events) was considered but rejected: structurally similar to `KXBTCD`/`KXETHD` (which need a `96c` gate), and insufficient event diversity to confidently allow it without one.

### Range / short-term crypto

| Prefix / Rule | W | L | n | Events |
|---------------|---|---|---|--------|
| `KXBTC15M` all | 9 | 0 | 9 | 9 |
| `KXETH15M` all | 10 | 0 | 10 | 10 |
| `KXBTC` all | 115 | 8 | 123 | — |
| `KXBTC` @ `96+` | 29 | 2 | 31 | — |

`KXBTC` range contracts remain fully blocked. They still lose at `96c`.

15-minute crypto families resolve too quickly for meaningful flip risk. Each trade is a distinct event. `KXBTC15M` and `KXETH15M` remain in the filter.

`KXSOL15M` (8W/0L/8 events) and `KXXRP15M` (7W/0L/7 events) are structurally identical to the proven 15-min families but excluded for conservatism pending more data.

### BTC path-risk caveat

The Mar 27 stop-loss lesson remains valid: the historical filter measures hold-to-resolution, but live trades on multi-day BTC directional contracts can be forced out by drawdowns before settlement. Treat long-dated BTC directional contracts as operationally unsafe unless a separate horizon/cushion rule exists upstream.

## 3. Weather: two strong cities added, six unchanged

### Unconditional-safe weather prefixes

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXHIGHLAX` | 51 | 0 | 51 | 21 |
| `KXHIGHMIA` | 51 | 0 | 51 | 20 |
| `KXLOWTLAX` | 30 | 0 | 30 | 15 |
| `KXHIGHPHIL` | 26 | 0 | 26 | 15 |
| `KXHIGHTPHX` | 26 | 0 | 26 | 15 |
| `KXHIGHTMIN` | 24 | 0 | 24 | 16 |
| `KXHIGHTDAL` | 24 | 0 | 24 | 12 |
| `KXLOWTMIA` | 20 | 0 | 20 | 13 |
| `KXHIGHTOKC` | 16 | 0 | 16 | 12 |
| `KXHIGHTHOU` | 14 | 0 | 14 | 7 |
| `KXHIGHTSATX` | 10 | 0 | 10 | 8 |

`KXHIGHLAX` (51W, 21 events) and `KXHIGHPHIL` (26W, 15 events) are strong new additions. `KXLOWTMIN` (0 trades) was removed — no evidence to keep it.

`KXLOWTAUS` (9W/0L/6 events) was considered but excluded for conservatism.

### Safe with price gates

| Prefix | Safe Rule | W | L | n | Events |
|--------|-----------|---|---|---|--------|
| `KXHIGHCHI` | `entry_price >= 93` | 35 | 0 | 35 | 19 |
| `KXHIGHAUS` | `entry_price >= 93` | 32 | 0 | 32 | 19 |
| `KXHIGHNY` | `entry_price >= 95` | 17 | 0 | 17 | 12 |
| `KXHIGHTATL` | `entry_price >= 94` | 16 | 0 | 16 | 11 |
| `KXLOWTCHI` | `entry_price >= 94` | 16 | 0 | 16 | 9 |

### Considered but not added

| Prefix | Gate | W | L | Events | Reason excluded |
|--------|------|---|---|--------|-----------------|
| `KXHIGHTSFO` | `>= 94` | 15 | 0 | 11 | Previously rejected for microclimate risk |
| `KXHIGHTLV` | `>= 96` | 9 | 0 | 7 | Previously rejected, thin sample at tight gate |
| `KXHIGHTDC` | `>= 96` | 9 | 0 | 7 | Northeast corridor risk, thin sample |

### Still reject

`KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` still fail the zero-loss bar at any reasonable gate.

## 4. Mentions: tightened to one proven prefix

### Safe without a gate

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXPRESMENTION` | 13 | 0 | 13 | 5 |

### Safe only with a gate

| Prefix | Safe Rule | W | L | n | Events |
|--------|-----------|---|---|---|--------|
| `KXTRUMPMENTION` | `entry_price >= 94` | 11 | 0 | 11 | 5 |

### Removed from previous filter

| Prefix | Trades | Events | Reason |
|--------|--------|--------|--------|
| `KXSURVIVORMENTION` | 18 | 2 | Only 2 TV episodes — misleading n |
| `KXFEDMENTION` | 8 | 1 | Only 1 Fed press conference |
| `KXJENSENMENTION` | 5 | 1 | Only 1 appearance |
| `KXSCOTUSMENTION` | 4 | 2 | Too thin |
| `KXENTMENTION` | 3 | 3 | Too thin |

### Considered but not added

| Prefix | Gate | W | L | Events | Reason excluded |
|--------|------|---|---|--------|-----------------|
| `KXTRUMPSAY` | `>= 93` | 14 | 0 | 3 | Only 3 event periods, Trump-adjacent noise |
| `KXTRUMPMENTIONB` | `>= 94` | 6 | 0 | 3 | Thin |

## 5. Sports unchanged

| Prefix / Rule | W | L | n | Events |
|---------------|---|---|---|--------|
| `KXMLBSTGAME` @ `94+` | 12 | 0 | 12 | 10 |
| `KXNASCARRACE` @ `94+` | 12 | 0 | 12 | 2 |

`KXNASCARRACE` has only 2 distinct race events. Retained from the original filter but flagged as thin — will strengthen or break as more races are tracked.

`KXWBCGAME` (8W/0L/5 events) was considered but excluded for conservatism.

## 6. Financials not added

| Prefix / Rule | W | L | n | Events | Reason excluded |
|---------------|---|---|---|--------|-----------------|
| `KXWTIW` @ `94+` | 28 | 0 | 28 | 3 | Only 3 weekly events — misleading n |

`KXWTIW >= 94` was previously listed as optional. Despite 28 winning trades, all come from only 3 distinct weeks. This is 3 observations, not 28. Daily WTI (`KXWTI`) remains structurally unsafe at every gate.

---

## Recommended Scout Filter Set

### Core 100% filter set: 672W / 0L

| Rule Type | Rule |
|-----------|------|
| Category | `Economics` |
| Category | `Entertainment` |
| Crypto | `KXBTCD` and `entry_price >= 96` |
| Crypto | `KXETHD` and `entry_price >= 96` |
| Crypto | `KXETH` and `entry_price >= 96` |
| Crypto | `KXBTC15M`, `KXETH15M` |
| Sports | `KXMLBSTGAME` and `entry_price >= 94` |
| Sports | `KXNASCARRACE` and `entry_price >= 94` |
| Weather | `KXHIGHLAX`, `KXHIGHMIA`, `KXHIGHPHIL`, `KXLOWTLAX`, `KXLOWTMIA`, `KXHIGHTPHX`, `KXHIGHTMIN`, `KXHIGHTDAL`, `KXHIGHTOKC`, `KXHIGHTHOU`, `KXHIGHTSATX` |
| Weather | `KXHIGHCHI` and `entry_price >= 93` |
| Weather | `KXHIGHAUS` and `entry_price >= 93` |
| Weather | `KXHIGHTATL` and `entry_price >= 94` |
| Weather | `KXHIGHNY` and `entry_price >= 95` |
| Weather | `KXLOWTCHI` and `entry_price >= 94` |
| Mentions | `KXPRESMENTION` |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` |

---

## Performance of the Updated Core Filter

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 672 |
| Losses | 0 |
| Coverage of completed trades | 35.2% |
| Average entry price | 94.7c |

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTC` | still loses at `96c` (29W/2L) |
| long-horizon `KXBTCD` live trades | path risk triggers stop losses before winning final print |
| `KXWTI` | daily oil remains structurally unsafe at every gate |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | index gap risk, lossy at every gate |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | weather variability remains too high |
| `KXHIGHTBOS` | lossy at every gate through `96c` (7W/2L) |
| `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | insufficient safe sample or lossy at tight gates |
| `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION` | wording variance |

---

## Re-qualification Watchlist

These prefixes have 100% win rates but were excluded for thin event diversity. They may re-qualify with more data:

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXSURVIVORMENTION` | 18 | 2 | More episodes |
| `KXWTIW >= 94` | 28 | 3 | More weeks |
| `KXHIGHTSFO >= 94` | 15 | 11 | Confidence on microclimate |
| `KXTRUMPSAY >= 93` | 14 | 3 | More event periods |
| `KXSOLD` | 10 | 3 | More events + gate determination |
| `KXSOL15M` | 8 | 8 | More trades |
| `KXFEDMENTION` | 8 | 1 | More Fed meetings |
| `KXWBCGAME` | 8 | 5 | More games |
| `KXLOWTAUS` | 9 | 6 | More days |
| `KXXRP15M` | 7 | 7 | More trades |

---

## Scout Implementation Guidance

The Scout prefilter remains an auditable allowlist:

1. derive `prefix = event_ticker.partition("-")[0]`
2. compute the actionable Scout entry price for the selected side
3. allow only exact category/prefix rules with explicit price gates

Implementation shape:

```python
SAFE_CATEGORIES = {"Economics", "Entertainment"}

SAFE_EVENT_PREFIXES = {
    "KXHIGHLAX",
    "KXHIGHMIA",
    "KXHIGHPHIL",
    "KXLOWTLAX",
    "KXLOWTMIA",
    "KXHIGHTPHX",
    "KXHIGHTMIN",
    "KXHIGHTDAL",
    "KXHIGHTOKC",
    "KXHIGHTHOU",
    "KXHIGHTSATX",
    "KXPRESMENTION",
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

The BTC path-risk lesson should be implemented outside this file: add a separate live-trading guard for long holding windows or weak strike cushion on crypto directional markets.

---

## Bottom Line

The historical shortlist was tightened from the previous iteration. Key changes:

1. **6 prefixes removed** for insufficient event diversity — `KXSURVIVORMENTION` (2 events), `KXFEDMENTION` (1 event), `KXJENSENMENTION` (1 event), `KXSCOTUSMENTION` (2 events), `KXENTMENTION` (3 trades), `KXLOWTMIN` (0 trades)
2. **2 strong weather prefixes added** — `KXHIGHLAX` (51W/21 events), `KXHIGHPHIL` (26W/15 events)
3. **No previously safe bucket broke** (all still 100% win rate)
4. **Event diversity** is now tracked alongside trade count to prevent misleading confidence from correlated contracts
5. Qualifying trades: **672W / 0L** at 35.2% coverage
