# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Updated through**: Apr 4, 2026
**Scope**: 2,927 completed trades from 2,992 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 2,992 |
| Completed trades | 2,927 |
| Wins (`close_price=100`) | 2,775 |
| Losses (`close_price=0`) | 152 |
| Overall win rate | 94.8% |

---

## Where the 152 Losses Come From

### By Category

| Category | W | L | n | Win Rate |
|----------|---|---|---|----------|
| Climate and Weather | 986 | 53 | 1,039 | 94.9% |
| Crypto | 1,024 | 43 | 1,067 | 95.97% |
| Financials | 274 | 27 | 301 | 91.0% |
| Mentions | 259 | 19 | 278 | 93.2% |
| Sports | 53 | 1 | 54 | 98.2% |
| Science and Technology | 23 | 2 | 25 | 92.0% |
| Entertainment | 62 | 3 | 65 | 95.4% |
| Politics | 24 | 3 | 27 | 88.9% |
| Economics | 68 | 0 | 68 | 100.0% |

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXBTCD` | 648 | 22 | BTC directional — now loses at 96c (165W/1L) |
| `KXWTI` | 111 | 16 | Daily WTI structurally unsafe at every gate |
| `KXHIGHTMIN` | 34 | 4 | Needs 96c gate (8W/0L at 96c) |
| `KXHIGHTLV` | 33 | 4 | Needs 96c gate (12W/0L at 96c) |
| `KXBTC` | 151 | 11 | BTC range fails at every gate |
| `KXHIGHCHI` | 62 | 3 | Gate raised to 94c (43W/0L) |
| `KXETHD` | 97 | 6 | ETH directional still safe at 96c (21W/0L) |
| `KXHIGHTBOS` | 40 | 5 | Boston lossy at every gate through 96c |
| `KXHIGHDEN` | 56 | 6 | Denver highs remain unusable |
| `KXHIGHTDC` | 36 | 1 | Safe at 96c (12W/0L) |
| `KXHIGHNY` | 56 | 7 | NYC highs now lose at 95c and 96c — fully rejected |
| `KXNBAMENTION` | 42 | 3 | Wording variance; no safe gate |

---

## Deep Findings

### Event diversity matters more than trade count

A "trade" is one contract. An "event" is one distinct `event_ticker`. Multiple trades from the same event are correlated — they resolve together. Always check both.

### The KXBTCD break at 96c

The most critical change in this refresh: `KXBTCD` had 1 loss at `entry_price >= 96` (165W/1L/101 events). The prior safe bucket `KXBTCD @ 96c` (102W/0L at last refresh) is now broken. **KXBTCD is removed from the filter entirely.** There is no gate at which KXBTCD has zero losses with sufficient data.

---

## 1. Category rules — only Economics remains safe

`Entertainment` had 3 losses (65n/62W/3L). It is removed from the safe-category list.

| Category | W | L | n | Events | Status |
|----------|---|---|---|--------|--------|
| `Economics` | 68 | 0 | 68 | 34 | Safe (unconditional) |
| `Entertainment` | 62 | 3 | 65 | 37 | Removed |

---

## 2. Crypto

### Directional crypto

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXBTCD` @ `96+` | 165 | **1** | 166 | 101 | **REMOVED — 1 loss at gate** |
| `KXETHD` all | 97 | 6 | 103 | 46 | — |
| `KXETHD` @ `96+` | 21 | 0 | 21 | 16 | Kept at 96c gate |
| `KXETH` all | 34 | 1 | 35 | 22 | — |
| `KXETH` @ `96+` | 6 | 0 | 6 | 6 | Below 8-trade minimum — removed |

`KXETH` was carried at a 96c gate since it had 5W/0L at last refresh. It now has only 6 trades at 96c — below the 8-trade minimum. The gate cannot be relaxed (no compelling evidence at lower gates: 9W/0L at 95c and 15W/0L at 94c, neither reaching the 20-trade/10-event bar required to lower an existing crypto gate). **KXETH is removed.**

### 15-minute crypto

| Prefix | W | L | n | Events | Gate | Status |
|--------|---|---|---|--------|------|--------|
| `KXBTC15M` all | 15 | 1 | 16 | 16 | — | — |
| `KXBTC15M` @ `94+` | 8 | 0 | 8 | 8 | 94c | Demoted from unconditional |
| `KXETH15M` all | 15 | 0 | 15 | 15 | unconditional | Unchanged |
| `KXSOL15M` all | 12 | 0 | 12 | 12 | unconditional | **NEW (promoted from watchlist)** |

`KXBTC15M` had 1 loss at < 94c. Its unconditional status is revoked; a 94c gate applies (8W/0L/8 events — exactly meets minimum thresholds).

`KXSOL15M` now has 12W/0L across 12 distinct events, meeting both minimum thresholds. Added as unconditional.

### BTC path-risk caveat

The path-risk lesson remains valid: live trades on multi-day BTC directional contracts can be forced out by drawdowns before settlement, independent of final resolution price. With KXBTCD now failing even at 96c, no BTC directional market should be traded.

---

## 3. Weather

### Previously unconditional — now price-gated

Seven unconditional prefixes experienced losses in new data and require price gates:

| Prefix | Gate | W@Gate | L@Gate | Events@Gate | Was |
|--------|------|--------|--------|-------------|-----|
| `KXHIGHLAX` | 93c | 55 | 0 | 24 | unconditional (1 loss at < 93c) |
| `KXLOWTLAX` | 93c | 39 | 0 | 21 | unconditional (1 loss at < 93c) |
| `KXHIGHTPHX` | 94c | 25 | 0 | 15 | unconditional (1 loss at < 94c) |
| `KXHIGHTOKC` | 94c | 10 | 0 | 8 | unconditional (1 loss at < 94c) |
| `KXHIGHTMIN` | 96c | 8 | 0 | 7 | unconditional (4 losses below 96c) |
| `KXHIGHTHOU` | 95c | 8 | 0 | 7 | unconditional (1 loss at < 95c) |

### Price gates raised

| Prefix | Old Gate | New Gate | W@Gate | L@Gate | Events@Gate |
|--------|----------|----------|--------|--------|-------------|
| `KXHIGHCHI` | 93c | **94c** | 43 | 0 | 24 |
| `KXHIGHAUS` | 93c | **95c** | 27 | 0 | 19 |

Both had losses added in new data at their prior gates. `KXHIGHCHI @ 93c` now has 1 loss; `KXHIGHAUS @ 93c` has 1 loss. Gates raised accordingly.

### Still unconditional

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXHIGHMIA` | 62 | 0 | 62 | 25 |
| `KXHIGHPHIL` | 34 | 0 | 34 | 20 |
| `KXLOWTMIA` | 27 | 0 | 27 | 17 |
| `KXHIGHTDAL` | 38 | 0 | 38 | 18 |
| `KXHIGHTSATX` | 16 | 0 | 16 | 10 |
| `KXLOWTAUS` | 19 | 0 | 19 | 11 |

`KXLOWTAUS` promoted from watchlist — now 19W/0L/11 events.

### Safe with price gates (pre-existing, gates unchanged)

| Prefix | Gate | W | L | n | Events |
|--------|------|---|---|---|--------|
| `KXHIGHTATL` | 94c | 24 | 0 | 24 | 15 |
| `KXLOWTCHI` | 94c | 25 | 0 | 25 | 13 |
| `KXHIGHNY` | — | — | — | — | **REMOVED** |

### New weather additions

Previously on watchlist or "considered" — now qualify:

| Prefix | Gate | W | L | Events | Reason added |
|--------|------|---|---|--------|--------------|
| `KXHIGHTLV` | 96c | 12 | 0 | 10 | Had 9W/7 events at last refresh; now 12W/10 events |
| `KXHIGHTDC` | 96c | 12 | 0 | 9 | Had 9W/7 events at last refresh; now 12W/9 events |
| `KXHIGHTSFO` | 94c | 29 | 0 | 16 | Strong data; microclimate risk now overridden by evidence |

### KXHIGHNY removed

`KXHIGHNY` was at a 95c gate (17W/0L/12 events at last refresh). New data: losses now present at 95c (26W/1L) and 96c (17W/1L). Fully rejected.

### Still reject

`KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` still fail the zero-loss bar at any reasonable gate.

---

## 4. Mentions

### Safe without gate

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXPRESMENTION` | 13 | 0 | 13 | 5 |

### Safe with gate

| Prefix | Gate | W | L | n | Events |
|--------|------|---|---|---|--------|
| `KXTRUMPMENTION` | 94c | 18 | 0 | 18 | 7 |

Both unchanged from prior refresh.

---

## 5. Sports

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXMLBSTGAME` @ 94c | 12 | 0 | 12 | 10 | Unchanged |
| `KXWBCGAME` | 8 | 0 | 8 | 5 | **NEW** (promoted from watchlist) |
| `KXNASCARRACE` @ 94c | 13 | 0 | 13 | 2 | **REMOVED** (only 2 events) |

`KXNASCARRACE` has been at 2 distinct race events for two refreshes. It fails the 5-event minimum and is removed.

`KXWBCGAME` exactly meets the minimum thresholds (8 trades, 5 events). Added as unconditional.

---

## 6. Financials — still not added

| Prefix / Rule | W | L | n | Events | Reason excluded |
|---------------|---|---|---|--------|-----------------|
| `KXWTIW` @ 94c | 41 | 0 | 41 | 4 | Only 4 distinct weeks — not 41 independent observations |

`KXWTIW` grew to 41 winning trades at the 94c gate, but still only 4 distinct weekly events. This is 4 observations. Not added.

---

## Recommended Scout Filter Set

### Core 100% filter set: 688W / 0L

| Rule Type | Rule | W@Rule | Events |
|-----------|------|--------|--------|
| Category | `Economics` | 68 | 34 |
| Weather | `KXHIGHMIA` (unconditional) | 62 | 25 |
| Weather | `KXHIGHPHIL` (unconditional) | 34 | 20 |
| Weather | `KXLOWTMIA` (unconditional) | 27 | 17 |
| Weather | `KXHIGHTDAL` (unconditional) | 38 | 18 |
| Weather | `KXHIGHTSATX` (unconditional) | 16 | 10 |
| Weather | `KXLOWTAUS` (unconditional) | 19 | 11 |
| Weather | `KXHIGHLAX` and `entry_price >= 93` | 55 | 24 |
| Weather | `KXLOWTLAX` and `entry_price >= 93` | 39 | 21 |
| Weather | `KXHIGHTPHX` and `entry_price >= 94` | 25 | 15 |
| Weather | `KXHIGHTOKC` and `entry_price >= 94` | 10 | 8 |
| Weather | `KXHIGHTMIN` and `entry_price >= 96` | 8 | 7 |
| Weather | `KXHIGHTHOU` and `entry_price >= 95` | 8 | 7 |
| Weather | `KXHIGHCHI` and `entry_price >= 94` | 43 | 24 |
| Weather | `KXHIGHAUS` and `entry_price >= 95` | 27 | 19 |
| Weather | `KXHIGHTATL` and `entry_price >= 94` | 24 | 15 |
| Weather | `KXLOWTCHI` and `entry_price >= 94` | 25 | 13 |
| Weather | `KXHIGHTLV` and `entry_price >= 96` | 12 | 10 |
| Weather | `KXHIGHTDC` and `entry_price >= 96` | 12 | 9 |
| Weather | `KXHIGHTSFO` and `entry_price >= 94` | 29 | 16 |
| Crypto | `KXETHD` and `entry_price >= 96` | 21 | 16 |
| Crypto | `KXETH15M` (unconditional) | 15 | 15 |
| Crypto | `KXSOL15M` (unconditional) | 12 | 12 |
| Crypto | `KXBTC15M` and `entry_price >= 94` | 8 | 8 |
| Sports | `KXMLBSTGAME` and `entry_price >= 94` | 12 | 10 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` | 18 | 7 |

---

## Performance of the Updated Core Filter

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 688 |
| Losses | 0 |
| Coverage of completed trades | 23.5% |
| Previous qualifying trades | 672 |
| Previous coverage | 35.2% |

Coverage dropped because the dataset grew from 1,910 to 2,927 completed trades (+53%) while several previously-unconditional prefixes required gates. Absolute qualifying count increased slightly (+16).

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTCD` | 1 loss at 96c gate (165W/1L at ≥96c) — previously safe zone is now broken |
| `KXBTC` | BTC range fails at every gate |
| `KXETH` | 96c gate too thin (6 trades); cannot relax below 96c for crypto structural reasons |
| `KXWTI` | Daily oil structurally unsafe at every gate |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | Index gap risk, lossy at every gate |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | Weather variability too high |
| `KXHIGHTBOS` | Lossy through 96c |
| `KXHIGHNY` | New losses at 95c and 96c gates — fully rejected |
| `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | Lossy at tight gates |
| `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION` | Wording variance |

---

## Re-qualification Watchlist

These prefixes have 100% win rates but were excluded for thin event diversity or structural concerns. May re-qualify with more data:

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXSURVIVORMENTION` | 29 | 4 | ≥5 distinct TV episodes |
| `KXWTIW >= 94c` | 41 | 4 | ≥5 distinct weekly events |
| `KXTRUMPSAY >= 93c` | 17 | 4 | ≥5 event periods |
| `KXSOLD >= 96c` | 0 | 0 | Trades at ≥96c gate (structural risk same as KXBTCD/KXETHD) |
| `KXNASCARRACE >= 94c` | 13 | 2 | ≥5 distinct race events (removed this refresh) |
| `KXALBUMSALES >= 95c` | 13 | 6 | Confidence on category stability (Entertainment no longer safe) |
| `KXHIGHTMIN >= 96c` | 8 | 7 | More data at 96c gate (currently minimum-threshold) |
| `KXHIGHTHOU >= 95c` | 8 | 7 | More data at 95c gate (currently minimum-threshold) |
| `KXBTC15M >= 94c` | 8 | 8 | More data at 94c gate (currently minimum-threshold) |
| `KXHIGHTOKC >= 94c` | 10 | 8 | More data at 94c gate (currently minimum-threshold) |
| `KXFEDMENTION` | 8 | 1 | More Fed meetings (still only 1 event) |
| `KXXRP15M` | 7 | 7 | ≥8 trades |

---

## Scout Implementation Guidance

The Scout prefilter remains an auditable allowlist:

1. derive `prefix = event_ticker.partition("-")[0]`
2. compute the actionable Scout entry price for the selected side
3. allow only exact category/prefix rules with explicit price gates

Implementation shape:

```python
SAFE_CATEGORIES = {"Economics"}

SAFE_EVENT_PREFIXES = {
    # Weather
    "KXHIGHMIA",
    "KXHIGHPHIL",
    "KXLOWTMIA",
    "KXHIGHTDAL",
    "KXHIGHTSATX",
    "KXLOWTAUS",
    # Crypto 15-min
    "KXETH15M",
    "KXSOL15M",
    # Sports
    "KXWBCGAME",
    # Mentions
    "KXPRESMENTION",
}

PRICE_GATED_EVENT_PREFIXES = {
    # Crypto
    "KXETHD": 96,
    "KXBTC15M": 94,
    # Weather - demoted from unconditional
    "KXHIGHLAX": 93,
    "KXLOWTLAX": 93,
    "KXHIGHTPHX": 94,
    "KXHIGHTOKC": 94,
    "KXHIGHTMIN": 96,
    "KXHIGHTHOU": 95,
    # Weather - gates raised
    "KXHIGHCHI": 94,
    "KXHIGHAUS": 95,
    # Weather - unchanged gates
    "KXHIGHTATL": 94,
    "KXLOWTCHI": 94,
    # Weather - new additions
    "KXHIGHTLV": 96,
    "KXHIGHTDC": 96,
    "KXHIGHTSFO": 94,
    # Sports
    "KXMLBSTGAME": 94,
    # Mentions
    "KXTRUMPMENTION": 94,
}
```

---

## Bottom Line

Key changes from the previous refresh (Mar 30, 2026 → Apr 4, 2026):

1. **KXBTCD removed** — the 96c gate broke (165W/1L). Previously safe BTC directional is no longer safe at any gate.
2. **Entertainment category removed** — 3 losses accumulated (62W/3L).
3. **KXHIGHNY removed** — losses now appear at 95c and 96c gates.
4. **KXNASCARRACE removed** — only 2 distinct race events after two refreshes; fails 5-event minimum.
5. **KXETH removed** — 96c gate below 8-trade minimum; cannot relax gate per structural rule.
6. **7 unconditional prefixes demoted** to price-gated (KXHIGHLAX, KXLOWTLAX, KXHIGHTPHX, KXHIGHTOKC, KXHIGHTMIN, KXHIGHTHOU, KXBTC15M).
7. **2 price gates raised** (KXHIGHCHI: 93c→94c, KXHIGHAUS: 93c→95c).
8. **6 new entries added** — KXLOWTAUS, KXSOL15M, KXWBCGAME (unconditional) and KXHIGHTLV, KXHIGHTDC, KXHIGHTSFO (price-gated).
9. Qualifying trades: **688W / 0L** at 23.5% coverage (was 672W/0L at 35.2%).
