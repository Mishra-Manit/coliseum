# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Updated through**: Apr 6, 2026
**Scope**: 3,133 completed trades from 3,283 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 3,283 |
| Completed trades | 3,133 |
| Wins (`close_price=100`) | 2,970 |
| Losses (`close_price=0`) | 163 |
| Overall win rate | 94.8% |

---

## Where the 163 Losses Come From

### By Category

| Category | W | L | n | Win Rate |
|----------|---|---|---|----------|
| Climate and Weather | 1,084 | 62 | 1,146 | 94.6% |
| Crypto | 1,092 | 45 | 1,137 | 96.0% |
| Financials | 274 | 27 | 301 | 91.0% |
| Mentions | 274 | 19 | 293 | 93.5% |
| Sports | 53 | 1 | 54 | 98.2% |
| Science and Technology | 23 | 2 | 25 | 92.0% |
| Entertainment | 66 | 3 | 69 | 95.7% |
| Politics | 26 | 3 | 29 | 89.7% |
| Economics | 75 | 0 | 75 | 100.0% |

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXBTCD` | 700 | 24 | BTC directional — broken at 96c |
| `KXWTI` | 111 | 16 | Daily WTI structurally unsafe at every gate |
| `KXHIGHTMIN` | 37 | 4 | 96c gate holds (9W/0L) |
| `KXHIGHTLV` | 38 | 4 | 96c gate holds (13W/0L) |
| `KXHIGHAUS` | 60 | 4 | **Broken at all gates** — removed |
| `KXHIGHTATL` | 40 | 4 | **Gate broken**; @96c only 7W (below minimum) — removed |
| `KXHIGHTBOS` | 43 | 5 | Lossy at every gate through 96c |
| `KXHIGHDEN` | 60 | 6 | Denver highs remain unusable |
| `KXHIGHNY` | 62 | 8 | Fully rejected (prior refresh) |
| `KXETHD` | 103 | 6 | ETH directional safe at 96c (22W/0L) |

---

## Deep Findings

### Event diversity matters more than trade count

A "trade" is one contract. An "event" is one distinct `event_ticker`. Multiple trades from the same event are correlated — they resolve together. Always check both.

### KXHIGHLAX stop-loss today (Apr 6, 2026)

The stop-loss triggered on KXHIGHLAX-26APR06-B76.5 is a direct signal: the 93c gate for KXHIGHLAX is broken. New data confirms 75W/3L total. The only clean gate is now @96c (16W/0L/13 events). Gate raised accordingly. This is also motivation to actively thin the weather-heavy shortlist — weather now accounts for the majority of filter entries and the majority of losses.

---

## 1. Category rules — only Economics remains safe

| Category | W | L | n | Events | Status |
|----------|---|---|---|--------|--------|
| `Economics` | 75 | 0 | 75 | 36 | Safe (unconditional) |

---

## 2. Crypto

### Directional crypto

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXBTCD` (any gate) | 700 | 24 | 724 | 220 | Rejected — no safe gate |
| `KXETHD` all | 103 | 6 | 109 | 50 | — |
| `KXETHD` @ `96+` | 22 | 0 | 22 | 17 | Kept at 96c gate |
| `KXETH` @ `96+` | 6 | 0 | 6 | 6 | Below 8-trade minimum — remains removed |

### 15-minute crypto

| Prefix | W | L | n | Events | Gate | Status |
|--------|---|---|---|--------|------|--------|
| `KXBTC15M` all | 17 | 1 | 18 | 18 | — | — |
| `KXBTC15M` @ `94+` | 9 | 0 | 9 | 9 | 94c | Unchanged |
| `KXETH15M` all | 17 | 0 | 17 | 17 | unconditional | Unchanged |
| `KXSOL15M` all | 12 | 0 | 12 | 12 | unconditional | Unchanged |
| `KXXRP15M` all | 8 | 0 | 8 | 8 | unconditional | **NEW — promoted from watchlist** |

`KXXRP15M` had 7W/7 events at last refresh. Now 8W/0L/8 events — meets both minimum thresholds. Added as unconditional. Structurally similar to KXETH15M and KXSOL15M (15-min crypto, high event diversity per trade).

---

## 3. Weather

### Still unconditional

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXHIGHMIA` | 66 | 0 | 66 | 27 |
| `KXLOWTMIA` | 28 | 0 | 28 | 18 |
| `KXHIGHTDAL` | 41 | 0 | 41 | 20 |
| `KXHIGHTSATX` | 19 | 0 | 19 | 11 |
| `KXLOWTAUS` | 25 | 0 | 25 | 13 |

`KXHIGHPHIL` was unconditional (34W/0L at last refresh). New data: 1 loss added (36W/1L). The script finds no zero-loss gate with n≥3 at any threshold from 90–99c, meaning the loss occurred at a high entry price that eliminates every qualifying gate. **KXHIGHPHIL is removed.**

### Safe with price gates (gates unchanged)

| Prefix | Gate | W@Gate | L@Gate | Events@Gate | Change |
|--------|------|--------|--------|-------------|--------|
| `KXLOWTLAX` | 93c | 39 | 0 | 21 | Unchanged |
| `KXHIGHTPHX` | 94c | 27 | 0 | 17 | Unchanged |
| `KXHIGHTOKC` | 94c | 11 | 0 | 9 | Unchanged |
| `KXHIGHTMIN` | 96c | 9 | 0 | 8 | Unchanged |
| `KXHIGHTHOU` | 95c | 9 | 0 | 8 | Unchanged |
| `KXHIGHCHI` | 94c | 48 | 0 | 26 | Unchanged |
| `KXLOWTCHI` | 94c | 26 | 0 | 14 | Unchanged |
| `KXHIGHTLV` | 96c | 13 | 0 | 11 | Unchanged |
| `KXHIGHTDC` | 96c | 14 | 0 | 10 | Unchanged |
| `KXHIGHTSFO` | 94c | 30 | 0 | 17 | Unchanged |

### Gate raised

| Prefix | Old Gate | New Gate | W@Gate | L@Gate | Events@Gate | Reason |
|--------|----------|----------|--------|--------|-------------|--------|
| `KXHIGHLAX` | 93c | **96c** | 16 | 0 | 13 | Stop-loss triggered today; 93c gate broken |

### Removed

| Prefix | Reason |
|--------|--------|
| `KXHIGHPHIL` | 1 new loss; no zero-loss gate found with n≥3 |
| `KXHIGHAUS` | Losses at all gates from 90–99c; no safe bucket |
| `KXHIGHTATL` | Gate broken; @96c only 7W/0L (below 8-trade minimum) |

### Still reject

`KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL`, `KXHIGHNY` — lossy at every reasonable gate.

Note: `KXHIGHTSEA` shows 10W/0L/7 events at @96c in new data (up from rejected). Not added — weather lean-away policy and minimum thresholds are borderline; moved to watchlist.

---

## 4. Mentions

### Safe without gate

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXPRESMENTION` | 13 | 0 | 13 | 5 |

### Safe with gate

| Prefix | Gate | W | L | n | Events | Status |
|--------|------|---|---|---|--------|--------|
| `KXTRUMPMENTION` | 94c | 18 | 0 | 18 | 7 | Unchanged |
| `KXTRUMPSAY` | 94c | 21 | 0 | 21 | 5 | **NEW — promoted from watchlist** |

`KXTRUMPSAY` had 4 distinct events at last refresh. Now has 5 events at the 94c gate (21W/0L). Meets both thresholds (n≥8, events≥5). Trump-adjacent structural rule requires 94c+ minimum — gate is set at 94c accordingly.

---

## 5. Sports

| Prefix / Rule | W | L | n | Events | Status |
|---------------|---|---|---|--------|--------|
| `KXMLBSTGAME` (unconditional) | 22 | 0 | 22 | 12 | **Upgraded from 94c gate** |
| `KXWBCGAME` (unconditional) | 8 | 0 | 8 | 5 | Unchanged |

`KXMLBSTGAME` previously carried a 94c gate as a precaution. New data confirms 22W/0L/12 events at all entry prices (zero losses at any threshold 90–99c). Upgraded to unconditional. A key non-weather strengthening given the lean-away guidance.

---

## 6. Financials — still not added

| Prefix / Rule | W | L | n | Events | Reason excluded |
|---------------|---|---|---|--------|-----------------|
| `KXWTIW` @ 94c | 41 | 0 | 41 | 4 | Only 4 distinct weekly events — not 41 independent observations |

---

## Recommended Scout Filter Set

### Core 100% filter set: ~646W / 0L

| Rule Type | Rule | W@Rule | Events |
|-----------|------|--------|--------|
| Category | `Economics` | 75 | 36 |
| Weather | `KXHIGHMIA` (unconditional) | 66 | 27 |
| Weather | `KXLOWTMIA` (unconditional) | 28 | 18 |
| Weather | `KXHIGHTDAL` (unconditional) | 41 | 20 |
| Weather | `KXHIGHTSATX` (unconditional) | 19 | 11 |
| Weather | `KXLOWTAUS` (unconditional) | 25 | 13 |
| Weather | `KXHIGHLAX` and `entry_price >= 96` | 16 | 13 |
| Weather | `KXLOWTLAX` and `entry_price >= 93` | 39 | 21 |
| Weather | `KXHIGHTPHX` and `entry_price >= 94` | 27 | 17 |
| Weather | `KXHIGHTOKC` and `entry_price >= 94` | 11 | 9 |
| Weather | `KXHIGHTMIN` and `entry_price >= 96` | 9 | 8 |
| Weather | `KXHIGHTHOU` and `entry_price >= 95` | 9 | 8 |
| Weather | `KXHIGHCHI` and `entry_price >= 94` | 48 | 26 |
| Weather | `KXLOWTCHI` and `entry_price >= 94` | 26 | 14 |
| Weather | `KXHIGHTLV` and `entry_price >= 96` | 13 | 11 |
| Weather | `KXHIGHTDC` and `entry_price >= 96` | 14 | 10 |
| Weather | `KXHIGHTSFO` and `entry_price >= 94` | 30 | 17 |
| Crypto | `KXETHD` and `entry_price >= 96` | 22 | 17 |
| Crypto | `KXETH15M` (unconditional) | 17 | 17 |
| Crypto | `KXSOL15M` (unconditional) | 12 | 12 |
| Crypto | `KXXRP15M` (unconditional) | 8 | 8 |
| Crypto | `KXBTC15M` and `entry_price >= 94` | 9 | 9 |
| Sports | `KXMLBSTGAME` (unconditional) | 22 | 12 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` | 18 | 7 |
| Mentions | `KXTRUMPSAY` and `entry_price >= 94` | 21 | 5 |

---

## Performance of the Updated Core Filter

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | ~646 |
| Losses | 0 |
| Coverage of completed trades | ~20.6% |
| Previous qualifying trades | 688 |
| Previous coverage | 23.5% |

Coverage and qualifying count dropped due to three weather removals (KXHIGHPHIL, KXHIGHAUS, KXHIGHTATL) and the KXHIGHLAX gate raise from 93c to 96c. New additions (KXXRP15M, KXTRUMPSAY, KXMLBSTGAME upgrade) partially offset the loss.

**Filter composition shift**: Weather entries dropped from 19 to 16. Non-weather entries (Crypto, Sports, Mentions, Economics) grew from 9 to 11. Weather is now 59% of prefix entries versus 68% before — directional progress on lean-away guidance.

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTCD` | No safe gate; losses accumulating across all price levels |
| `KXBTC` | BTC range fails at every gate |
| `KXETH` | 96c gate only 6 trades; below minimum |
| `KXWTI` | Daily oil structurally unsafe at every gate |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | Index gap risk, lossy at every gate |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | Weather variability too high |
| `KXHIGHTBOS` | Lossy through 96c |
| `KXHIGHNY` | Fully rejected (prior refresh) |
| `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | Lossy or borderline at tight gates |
| `KXHIGHPHIL` | New loss; no qualifying gate found |
| `KXHIGHAUS` | Losses at all gates; no recovery gate |
| `KXHIGHTATL` | Gate broken; @96c only 7W (below minimum) |
| `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION` | Wording variance or losses |

---

## Re-qualification Watchlist

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXSURVIVORMENTION` | 29 | 4 | ≥5 distinct TV episodes |
| `KXWTIW >= 94c` | 41 | 4 | ≥5 distinct weekly events |
| `KXHIGHTSEA >= 96c` | 10 | 7 | More data (borderline; weather lean-away applies) |
| `KXLOWTDEN >= 96c` | 7 | 5 | ≥8 trades at gate |
| `KXSOLD >= 96c` | 0 | 0 | Trades at ≥96c (structural risk same as KXBTCD/KXETHD) |
| `KXNASCARRACE >= 94c` | 13 | 2 | ≥5 distinct race events |
| `KXALBUMSALES >= 95c` | 13 | 6 | Confidence on category stability (Entertainment not safe) |
| `KXHIGHTMIN >= 96c` | 9 | 8 | More data at minimum threshold |
| `KXHIGHTHOU >= 95c` | 9 | 8 | More data at minimum threshold |
| `KXHIGHTOKC >= 94c` | 11 | 9 | More data at minimum threshold |
| `KXBTC15M >= 94c` | 9 | 9 | More data at minimum threshold |
| `KXFEDMENTION` | 8 | 1 | More Fed meetings (still only 1 event) |
| `KXTRUMPSAY >= 94c` | 21 | 5 | Exactly meets minimum; watch for event growth |

---

## Bottom Line

Key changes from the previous refresh (Apr 4, 2026 → Apr 6, 2026):

1. **KXHIGHLAX gate raised 93c → 96c** — stop-loss triggered today on KXHIGHLAX. The 93c gate is broken by new data (3 total losses). Now 16W/0L/13 events at 96c.
2. **KXHIGHPHIL removed** — first loss appeared; no qualifying gate found at any threshold.
3. **KXHIGHAUS removed** — losses at every gate 90–99c. No safe bucket exists.
4. **KXHIGHTATL removed** — gate broken; @96c yields only 7W (below 8-trade minimum).
5. **KXMLBSTGAME upgraded to unconditional** — 22W/0L/12 events, zero losses at all prices. Key non-weather addition.
6. **KXXRP15M added unconditional** — promoted from watchlist; now 8W/0L/8 events.
7. **KXTRUMPSAY added @ 94c gate** — promoted from watchlist; now 21W/0L/5 events at 94c.
8. Net weather entries: 19 → 16. Non-weather entries: 9 → 11. Shortlist composition moving away from weather concentration.
