# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Updated through**: Apr 14, 2026
**Scope**: 3,922 completed trades from 4,239 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 4,239 |
| Completed trades | 4,148 |
| Wins (`close_price=100`) | 3,922 |
| Losses (`close_price=0`) | 226 |
| Overall win rate | 94.6% |

---

## Where the 226 Losses Come From

### By Category

| Category | W | L | n | Win Rate |
|----------|---|---|---|----------|
| Climate and Weather | 1,379 | 78 | 1,457 | 94.7% |
| Crypto | 1,427 | 67 | 1,494 | 95.5% |
| Financials | 427 | 40 | 467 | 91.4% |
| Mentions | 356 | 27 | 383 | 92.9% |
| Sports | 64 | 1 | 65 | 98.5% |
| Science and Technology | 23 | 2 | 25 | 92.0% |
| Entertainment | 93 | 4 | 97 | 95.9% |
| Politics | 38 | 5 | 43 | 88.4% |
| Economics | 106 | 1 | 107 | 99.1% |
| Elections | 8 | 0 | 8 | 100.0% |

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXBTCD` | 930 | 39 | BTC directional — broken at every gate including 96c (2L) |
| `KXWTI` | 176 | 23 | Daily WTI structurally unsafe at every gate |
| `KXBTC` | 200 | 13 | BTC range fails at every gate |
| `KXHIGHNY` | 78 | 9 | Fully rejected |
| `KXHIGHDEN` | 78 | 8 | Denver highs remain unusable |
| `KXETHD` | 132 | 7 | ETH directional safe at 96c (29W/0L) |
| `KXHIGHTBOS` | 56 | 7 | Lossy at every gate through 96c |
| `KXHIGHAUS` | 74 | 6 | Broken at all gates |
| `KXINX` | 45 | 5 | Index gap risk |
| `KXINXU` | 51 | 5 | Index gap risk |

---

## Deep Findings

### Event diversity matters more than trade count

A "trade" is one contract. An "event" is one distinct `event_ticker`. Multiple trades from the same event are correlated — they resolve together. Always check both.

### Economics lost its 100% category status

`KXCH11-26APR03-T800` (US commercial Chapter 11 filings for March 2026) resolved as a loss. Economics is now 106W/1L (99.1%). The blanket `Economics` safe category rule has been removed. Individual Economics prefixes that independently meet the minimum thresholds (trades >= 8, events >= 5) are added as explicit prefix entries instead.

### Weather volatility confirmed

Since the Apr 6 refresh, three more weather prefixes broke:
- `KXHIGHLAX` — now 93W/4L, no zero-loss gate at any threshold
- `KXHIGHTDC` — now 47W/2L, no zero-loss gate
- `KXLOWTAUS` — now 32W/2L

Weather is capped at 3 tickers maximum per policy. All must be price-gated.

### KXSURVIVORMENTION broke

Previously 100% win rate. Now 43W/2L/6 events. Removed from safe prefixes.

---

## 1. Category rules — none remain safe

| Category | W | L | n | Events | Status |
|----------|---|---|---|--------|--------|
| `Economics` | 106 | 1 | 107 | 53 | **Removed** — KXCH11 loss |
| `Elections` | 8 | 0 | 8 | 3 | Too few events (3) |

No category qualifies for blanket inclusion.

---

## 2. Crypto

### Directional crypto

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXBTCD` (any gate) | 930 | 39 | 969 | 300 | Rejected — 2L even at 96c |
| `KXETHD` all | 132 | 7 | 139 | 61 | — |
| `KXETHD` @ `96+` | 29 | 0 | 29 | 22 | Kept at 96c gate |

### 15-minute crypto

| Prefix | W | L | n | Events | Gate | Status |
|--------|---|---|---|--------|------|--------|
| `KXBTC15M` all | 23 | 2 | 25 | 25 | — | — |
| `KXBTC15M` @ `94+` | 14 | 0 | 14 | 14 | 94c | Unchanged |
| `KXETH15M` all | 22 | 0 | 22 | 22 | unconditional | Unchanged |
| `KXSOL15M` all | 17 | 0 | 17 | 17 | unconditional | Unchanged |
| `KXXRP15M` all | 11 | 0 | 11 | 11 | unconditional | Unchanged |

---

## 3. Weather (capped at 3 tickers)

### Current 3 weather tickers (all price-gated)

| Prefix | Gate | W@Gate | L@Gate | Events@Gate | Status |
|--------|------|--------|--------|-------------|--------|
| `KXHIGHMIA` | 96c | 80 | 0 | 32 | Unchanged |
| `KXHIGHTDAL` | 96c | 53 | 0 | 25 | Unchanged |
| `KXLOWTMIA` | 96c | 33 | 0 | 22 | Unchanged |

### Removed / broken weather (not backfilled per policy)

| Prefix | Reason |
|--------|--------|
| `KXHIGHLAX` | 93W/4L, no zero-loss gate at any threshold |
| `KXHIGHTDC` | 47W/2L, no zero-loss gate |
| `KXLOWTAUS` | 32W/2L |
| `KXHIGHPHIL` | Loss; no qualifying gate |
| `KXHIGHAUS` | Losses at all gates |
| `KXHIGHTATL` | Gate broken; @96c only 7W |

### Still reject

`KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL`, `KXHIGHNY` — lossy at every reasonable gate.

---

## 4. Mentions

### Safe without gate

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXPRESMENTION` | 13 | 0 | 13 | 5 |

### Safe with gate

| Prefix | Gate | W | L | n | Events | Status |
|--------|------|---|---|---|--------|--------|
| `KXTRUMPMENTION` | 94c | 25 | 0 | 25 | 8 | Unchanged |
| `KXTRUMPSAY` | 94c | 23 | 0 | 23 | 5 | Unchanged |

### Removed

| Prefix | Reason |
|--------|--------|
| `KXSURVIVORMENTION` | 43W/2L — losses appeared |
| `KXHEGSETHMENTION` | 16W/0L but only 4 events — below 5-event minimum |

---

## 5. Sports

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXMLBSTGAME` (unconditional) | 22 | 0 | 22 | 12 | Unchanged |
| `KXWBCGAME` (unconditional) | 8 | 0 | 8 | 5 | Unchanged |

---

## 6. Commodities

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXGOLDD` (unconditional) | 14 | 0 | 14 | 7 | Unchanged |
| `KXWTIW` @ 94c | 45 | 0 | 45 | 5 | Unchanged (now meets event minimum) |

---

## 7. Economics (prefix-level, no longer category-level)

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXJOBLESSCLAIMS` (unconditional) | 10 | 0 | 10 | 5 | **NEW** — promoted after Economics category removal |

---

## 8. Entertainment

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXRT` (unconditional) | 9 | 0 | 9 | 5 | **NEW** — Rotten Tomatoes, meets all thresholds |

---

## Recommended Scout Filter Set

### Core 100% filter set

| Rule Type | Rule | W@Rule | Events |
|-----------|------|--------|--------|
| Crypto 15-min | `KXETH15M` (unconditional) | 22 | 22 |
| Crypto 15-min | `KXSOL15M` (unconditional) | 17 | 17 |
| Crypto 15-min | `KXXRP15M` (unconditional) | 11 | 11 |
| Crypto 15-min | `KXBTC15M` and `entry_price >= 94` | 14 | 14 |
| Crypto directional | `KXETHD` and `entry_price >= 96` | 29 | 22 |
| Commodities | `KXGOLDD` (unconditional) | 14 | 7 |
| Commodities | `KXWTIW` and `entry_price >= 94` | 45 | 5 |
| Weather | `KXHIGHMIA` and `entry_price >= 96` | 80 | 32 |
| Weather | `KXHIGHTDAL` and `entry_price >= 96` | 53 | 25 |
| Weather | `KXLOWTMIA` and `entry_price >= 96` | 33 | 22 |
| Sports | `KXMLBSTGAME` (unconditional) | 22 | 12 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` | 25 | 8 |
| Mentions | `KXTRUMPSAY` and `entry_price >= 94` | 23 | 5 |
| Economics | `KXJOBLESSCLAIMS` (unconditional) | 10 | 5 |
| Entertainment | `KXRT` (unconditional) | 9 | 5 |

---

## Performance of the Updated Core Filter

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | ~427 |
| Losses | 0 |
| Coverage of completed trades | ~10.3% |
| Previous qualifying trades | ~646 |
| Previous coverage | ~20.6% |

Coverage dropped significantly due to Economics category removal (was a blanket pass for 75+ trades), KXBTCD removal (was passing hundreds of trades at 94c gate despite losses), and KXSURVIVORMENTION removal. The filter is now strictly 100% win rate across all included entries.

**Filter composition**: Weather is 3 of 17 entries (17.6%). Non-weather dominates at 14 entries across Crypto, Commodities, Sports, Mentions, Economics, and Entertainment.

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTCD` | No safe gate; 39 losses, 2 even at 96c |
| `KXBTC` | BTC range fails at every gate |
| `KXETH` | 96c gate only 6 trades; below minimum |
| `KXWTI` | Daily oil structurally unsafe at every gate |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | Index gap risk, lossy at every gate |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | Weather variability too high |
| `KXHIGHTBOS` | Lossy through 96c |
| `KXHIGHNY` | Fully rejected |
| `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | Lossy or borderline at tight gates |
| `KXHIGHPHIL` | Loss; no qualifying gate |
| `KXHIGHAUS` | Losses at all gates |
| `KXHIGHTATL` | Gate broken; @96c only 7W |
| `KXHIGHLAX` | 4 losses; no zero-loss gate at any threshold |
| `KXHIGHTDC` | 2 losses; no zero-loss gate |
| `KXLOWTAUS` | 2 losses |
| `KXSURVIVORMENTION` | 43W/2L; losses appeared |
| `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION` | Wording variance or losses |

---

## Re-qualification Watchlist

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXHEGSETHMENTION` | 16 | 4 | 1 more distinct event (currently 4, minimum 5) |
| `KXWTIW >= 94c` | 45 | 5 | More event diversity (borderline at minimum) |
| `KXBRENTW` | 17 | 2 | More weekly events (only 2) |
| `KXHIGHTSEA >= 96c` | data growing | ~7 | More data (weather lean-away applies) |
| `KXLOWTDEN >= 96c` | 7 | 5 | More trades at gate |
| `KXSOLD >= 96c` | 4 | 4 | More trades (structural risk same as KXBTCD/KXETHD) |
| `KXNASCARRACE` | 13 | 2 | More distinct race events |
| `KXALBUMSALES >= 95c` | 13 | 6 | Confidence on category stability |
| `KXPOLITICSMENTION` | 8 | 4 | 1 more event |
| `KXAAAGASW` | 12 | 4 | 1 more event |
| `KXGOLDW` | 11 | 2 | More weekly events |
| `KXFEDMENTION` | 8 | 1 | More Fed meetings |
| `KXTRUMPSAY >= 94c` | 23 | 5 | Exactly meets minimum; watch for event growth |
| `KXHIGHTSATX >= 95c` | 10 | 8 | Qualifies on thresholds but weather cap applies |

---

## Bottom Line

Key changes from the previous refresh (Apr 6, 2026 → Apr 14, 2026):

1. **Economics category removed** — KXCH11-26APR03 loss breaks the blanket 100% category pass. `KXJOBLESSCLAIMS` added as explicit prefix entry to preserve coverage of the strongest Economics sub-market.
2. **KXBTCD fully removed** — now 930W/39L total. Even the 96c gate has 2 losses. No safe bucket exists at any price level.
3. **KXSURVIVORMENTION removed** — 43W/2L. Two losses appeared since last refresh.
4. **KXHEGSETHMENTION removed** — 16W/0L but only 4 distinct events. Below the 5-event diversity minimum.
5. **KXRT added unconditional** — 9W/0L/5 events. Rotten Tomatoes scores. New non-weather diversification.
6. **KXJOBLESSCLAIMS added unconditional** — 10W/0L/5 events. Jobless claims data, previously covered by Economics blanket rule.
7. **3 more weather prefixes confirmed broken** — KXHIGHLAX (4L, no gate), KXHIGHTDC (2L, no gate), KXLOWTAUS (2L). Validates the 3-ticker weather cap policy.
8. Net filter entries: 19 → 17. All 17 have strictly 100% win rate with verified event diversity.
