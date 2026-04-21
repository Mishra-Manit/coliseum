# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Refreshed**: Apr 21, 2026
**Scope**: 5,058 completed trades across 2,037 distinct events

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 5,159 |
| Completed trades | 5,058 |
| Wins (`close_price=100`) | 4,786 |
| Losses (`close_price=0`) | 272 |
| Overall win rate | 94.6% |

---

## Where the 272 Losses Come From

### By Category

| Category | W | L | n | Events | Win Rate |
|----------|---|---|---|--------|----------|
| Climate and Weather | 1,694 | 88 | 1,782 | 861 | 95.1% |
| Crypto | 1,716 | 84 | 1,800 | 692 | 95.3% |
| Financials | 533 | 48 | 581 | 123 | 91.7% |
| Mentions | 408 | 27 | 435 | 136 | 93.8% |
| Economics | 126 | 5 | 131 | 66 | 96.2% |
| Sports | 75 | 2 | 77 | 33 | 97.4% |
| Entertainment | 113 | 4 | 117 | 72 | 96.6% |
| Politics | 46 | 6 | 52 | 27 | 88.5% |
| Commodities | 35 | 3 | 38 | 8 | 92.1% |
| Elections | 12 | 2 | 14 | 5 | 85.7% |
| Science and Technology | 23 | 2 | 25 | 14 | 92.0% |

### Biggest Losing Prefixes

| Prefix | W | L | Notes |
|--------|---|---|-------|
| `KXBTCD` | 1,133 | 53 | BTC directional — broken at every gate including 96c |
| `KXWTI` | 238 | 32 | Daily WTI structurally unsafe at every gate |
| `KXBTC` | 230 | 14 | BTC range fails at every gate |
| `KXHIGHNY` | 87 | 9 | Fully rejected |
| `KXHIGHDEN` | 88 | 8 | Denver highs remain unusable |
| `KXHIGHTBOS` | 68 | 8 | Lossy through 96c |
| `KXETHD` | 161 | 7 | ETH directional safe at 96c gate only |

---

## Deep Findings

### Live-trading loss audit (Apr 06–21)

Five Scout-executed positions closed at a loss in this window. CSV resolution tracking confirms the actual outcomes:

| Ticker | Side | Entry | Exit | CSV resolution | Real outcome |
|--------|------|-------|------|----------------|--------------|
| `KXHIGHLAX-26APR06-B76.5` | NO | 0.93 | 0.72 | `no` / 100 | Thesis correct — stop fired early |
| `KXHIGHLAX-26APR07-B68.5` | NO | 0.96 | 0.74 | `no` / 100 | Thesis correct — stop fired early |
| `KXTRUMPSAY-26APR20-ALLA` | NO | 0.95 | 0.71 | `no` / 100 | Thesis correct — stop fired early |
| `KXHIGHMIA-26APR20-T86` | NO | 0.96 | 0.66 | `no` / 100 | Thesis correct — stop fired early |
| `KXAAAGASD-26APR21-4.025` | YES | 0.94 | 0.00 | `no` / 100 | **Thesis wrong — real loss** |

**Filter implications:**
- Four of five "losses" were intraday stop-outs on trades whose market thesis was correct. These do not invalidate the prefix buckets they came from.
- `KXAAAGASD` is the only prefix that produced a genuine thesis failure: entry at 94¢ with only a 1.7¢ margin above the $4.025 trigger, followed by an AAA print at/below the trigger. The CSV-only analysis still shows 11W/0L, but the live loss is real. Demote from unconditional to price-gated at 96c.
- `KXHIGHLAX` CSV stats remain 115W/4L — no zero-loss gate at any threshold. Continues to be rejected per prior policy.

### Event diversity matters more than trade count

A "trade" is one contract. An "event" is one distinct `event_ticker`. Multiple trades from the same event are correlated — they resolve together. Always check both.

### Weather volatility stays high

`KXHIGHLAX`, `KXHIGHTDC`, `KXLOWTAUS` remain non-qualifying at every gate. `KXHIGHMIA`, `KXHIGHTDAL`, and `KXLOWTMIA` remain zero-loss across the 90c–96c range with strong event diversity; they fill the 3-ticker weather cap.

### New prefixes promoted off the watchlist

`KXBRENTD` (13W/0L/5 events), `KXPOLITICSMENTION` (10W/0L/6 events), `KXTSAW` (8W/0L/5 events), `KXAPRPOTUS` (13W/0L/5 events at 93c), `KXALBUMSALES` (16W/0L/9 events at 95c), and `KXTRUMPMENTIONB` (16W/0L/6 events at 95c) all clear the minimum thresholds and are added.

### KXETH restored at 94c gate

Previous refresh rejected `KXETH` because its 96c gate only had 6 trades. The current dataset shows 25W/0L/15 events at the 94c gate, which clears both minimums. Added at 94c.

---

## 1. Category rules — none remain safe

| Category | W | L | n | Events | Status |
|----------|---|---|---|--------|--------|
| `Economics` | 126 | 5 | 131 | 66 | Rejected — now 5 losses |
| `Elections` | 12 | 2 | 14 | 5 | Rejected — losses appeared |

No category qualifies for blanket inclusion.

---

## 2. Crypto

### Directional crypto

| Rule | W@Rule | L@Rule | Events@Rule | Status |
|------|--------|--------|-------------|--------|
| `KXBTCD` (any gate) | 1,133 | 53 | 372 | **Rejected** — losses at every gate |
| `KXETHD >= 96c` | 39 | 0 | 28 | Kept |

### 15-minute crypto

| Rule | W@Rule | L@Rule | Events@Rule | Status |
|------|--------|--------|-------------|--------|
| `KXETH15M` (unconditional) | 28 | 0 | 28 | Kept |
| `KXSOL15M` (unconditional) | 19 | 0 | 19 | Kept |
| `KXXRP15M` (unconditional) | 14 | 0 | 14 | Kept |
| `KXBTC15M >= 94c` | 17 | 0 | 17 | Kept |

### Crypto thresholds (non-directional)

| Rule | W@Rule | L@Rule | Events@Rule | Status |
|------|--------|--------|-------------|--------|
| `KXETH >= 94c` | 25 | 0 | 15 | **NEW** — meets minimums at 94c gate |

---

## 3. Weather (capped at 3 tickers)

### Current 3 weather tickers (all price-gated)

| Prefix | Gate | W@Gate | L@Gate | Events@Gate | Status |
|--------|------|--------|--------|-------------|--------|
| `KXHIGHMIA` | 96c | 25 | 0 | 19 | Kept |
| `KXHIGHTDAL` | 96c | data clean | 0 | 32 overall | Kept |
| `KXLOWTMIA` | 96c | data clean | 0 | 28 overall | Kept |

### Still rejected

`KXHIGHLAX` (115W/4L, no gate), `KXHIGHTDC`, `KXLOWTAUS`, `KXHIGHPHIL`, `KXHIGHAUS`, `KXHIGHTATL`, `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL`, `KXHIGHNY` — lossy at every qualifying gate, or fail minimums.

---

## 4. Mentions

### Safe without gate

| Prefix | W | L | n | Events |
|--------|---|---|---|--------|
| `KXPRESMENTION` | 13 | 0 | 13 | 5 |
| `KXPOLITICSMENTION` | 10 | 0 | 10 | 6 |

### Safe with gate

| Prefix | Gate | W@Gate | L@Gate | Events@Gate | Status |
|--------|------|--------|--------|-------------|--------|
| `KXTRUMPMENTION` | 94c | 27 | 0 | 9 | Kept |
| `KXTRUMPMENTIONB` | 95c | 16 | 0 | 6 | **NEW** |
| `KXTRUMPSAY` | 94c | 25 | 0 | 6 | Kept |

### Removed / rejected

`KXSURVIVORMENTION` (51W/2L), `KXHEGSETHMENTION` (16W/0L but only 4 events), `KXNBAMENTION`, `KXMELANIAMENTION`, `KXVANCEMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXMENTION`.

---

## 5. Sports

| Rule | W | L | n | Events | Status |
|------|---|---|---|--------|--------|
| `KXMLBSTGAME` (unconditional) | 22 | 0 | 22 | 12 | Kept |
| `KXWBCGAME` (unconditional) | 8 | 0 | 8 | 5 | Kept |

`KXNASCARRACE` removed — still only 2 distinct race events.

---

## 6. Commodities

| Rule | W | L | n | Events | Status |
|------|---|---|---|--------|--------|
| `KXGOLDD` (unconditional) | 19 | 0 | 19 | 9 | Kept |
| `KXBRENTD` (unconditional) | 13 | 0 | 13 | 5 | **NEW** |
| `KXWTIW >= 94c` | 50 | 0 | 50 | 6 | Kept |

---

## 7. Economics / Gas prices

| Rule | W | L | n | Events | Status |
|------|---|---|---|--------|--------|
| `KXJOBLESSCLAIMS` (unconditional) | 12 | 0 | 12 | 6 | Kept |
| `KXAAAGASW` (unconditional) | 15 | 0 | 15 | 5 | Kept |
| `KXTSAW` (unconditional) | 8 | 0 | 8 | 5 | **NEW** |
| `KXAAAGASD >= 96c` | 11 | 0 | 11 | 9 | **DEMOTED from unconditional** after live loss on 1.7¢-margin entry |

---

## 8. Politics / Entertainment long-form

| Rule | W | L | n | Events | Status |
|------|---|---|---|--------|--------|
| `KXAPRPOTUS >= 93c` | 13 | 0 | 13 | 5 | **NEW** |
| `KXALBUMSALES >= 95c` | 16 | 0 | 16 | 9 | **NEW** |
| `KXRT` (unconditional) | 10 | 0 | 10 | 6 | Kept |

---

## Recommended Scout Filter Set

### Core 100% filter set (29 rules)

| Rule Type | Rule | W@Rule | Events |
|-----------|------|--------|--------|
| Crypto 15-min | `KXETH15M` (unconditional) | 28 | 28 |
| Crypto 15-min | `KXSOL15M` (unconditional) | 19 | 19 |
| Crypto 15-min | `KXXRP15M` (unconditional) | 14 | 14 |
| Crypto 15-min | `KXBTC15M >= 94c` | 17 | 17 |
| Crypto directional | `KXETHD >= 96c` | 39 | 28 |
| Crypto threshold | `KXETH >= 94c` | 25 | 15 |
| Commodities | `KXGOLDD` (unconditional) | 19 | 9 |
| Commodities | `KXBRENTD` (unconditional) | 13 | 5 |
| Commodities | `KXWTIW >= 94c` | 50 | 6 |
| Weather | `KXHIGHMIA >= 96c` | 25 | 19 |
| Weather | `KXHIGHTDAL >= 96c` | data clean | 32 |
| Weather | `KXLOWTMIA >= 96c` | data clean | 28 |
| Sports | `KXMLBSTGAME` (unconditional) | 22 | 12 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXPOLITICSMENTION` (unconditional) | 10 | 6 |
| Mentions | `KXTRUMPMENTION >= 94c` | 27 | 9 |
| Mentions | `KXTRUMPMENTIONB >= 95c` | 16 | 6 |
| Mentions | `KXTRUMPSAY >= 94c` | 25 | 6 |
| Economics | `KXJOBLESSCLAIMS` (unconditional) | 12 | 6 |
| Economics | `KXAAAGASW` (unconditional) | 15 | 5 |
| Economics | `KXTSAW` (unconditional) | 8 | 5 |
| Gas prices | `KXAAAGASD >= 96c` | 11 | 9 |
| Politics | `KXAPRPOTUS >= 93c` | 13 | 5 |
| Entertainment | `KXRT` (unconditional) | 10 | 6 |
| Entertainment | `KXALBUMSALES >= 95c` | 16 | 9 |

**Filter composition**: Weather is 3 of 26 entries (11.5%). Non-weather dominates across Crypto (6), Mentions (5), Economics/Gas (4), Commodities (3), Entertainment (2), Sports (2), Politics (1).

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTCD` | No safe gate; 53 losses total, lossy even at 96c |
| `KXBTC` | BTC range fails at every gate (14 losses) |
| `KXWTI` | Daily oil structurally unsafe at every gate (32 losses) |
| `KXINX`, `KXINXU`, `KXNASDAQ100`, `KXNASDAQ100U` | Index gap risk, lossy at every gate |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC` | Weather variability too high |
| `KXHIGHTBOS` | Lossy through 96c |
| `KXHIGHNY` | Fully rejected |
| `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | Lossy or borderline at tight gates |
| `KXHIGHPHIL` | Loss; no qualifying gate |
| `KXHIGHAUS` | Losses at all gates |
| `KXHIGHTATL` | Gate broken; @96c only 7W |
| `KXHIGHLAX` | 115W/4L; no zero-loss gate at any threshold |
| `KXHIGHTDC` | No zero-loss gate |
| `KXLOWTAUS` | 2 losses |
| `KXSURVIVORMENTION` | Losses appeared (51W/2L) |
| `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION`, `KXMELANIAMENTION` | Wording variance or losses |
| `KXNASCARRACE` | Only 2 distinct events |
| `KXHEGSETHMENTION` | 16W/0L but only 4 distinct events (below 5-event minimum) |

---

## Re-qualification Watchlist

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXGOLDW` | 16 | 3 | 2 more distinct weekly events |
| `KXSILVERW` | 10 | 4 | 1 more event |
| `KXSOLD >= 96c` | small n | few | More trades (structural crypto risk same as KXBTCD/KXETHD) |
| `KXFEDMENTION` | 8 | 1 | More distinct Fed meetings |
| `KXBRENTW` | 19 | 3 | More weekly events |
| `KXHIGHTPHX >= 94c` | 43 | 27 | Qualifies numerically but weather cap at 3 limits inclusion |
| `KXHIGHCHI >= 95c` | 54 | 33 | Same — weather cap limits inclusion |
| `KXLOWTLAX >= 93c` | 61 | 33 | Same — weather cap limits inclusion |

---

## Bottom Line

Key changes from the Apr 14 refresh:

1. **Added six new prefixes** — `KXBRENTD` (unconditional), `KXPOLITICSMENTION` (unconditional), `KXTSAW` (unconditional), `KXAPRPOTUS >= 93c`, `KXALBUMSALES >= 95c`, `KXTRUMPMENTIONB >= 95c`. All meet trade and event minimums with zero losses at their gates.
2. **Restored `KXETH` at 94c gate** — previously rejected (only 6 trades at 96c). Fresh CSV shows 25W/0L/15 events at 94c.
3. **`KXAAAGASD` demoted to price-gated** — live loss on `KXAAAGASD-26APR21-4.025` from a 1.7¢-margin entry. CSV stats alone still show zero-loss, but live evidence shows the unconditional rule is unsafe. 96c gate minimum going forward.
4. **`KXNASCARRACE` removed** — still only 2 distinct races.
5. **Weather cap maintained** — `KXHIGHMIA`, `KXHIGHTDAL`, `KXLOWTMIA` kept at 96c. No weather swap.
6. **Code drift fixed** — `filters.py` had stale `KXBTCD >= 95c`, `KXLOWTLAX` unconditional, `KXLOWTCHI` unconditional, and `KXNASCARRACE` unconditional entries from before the Apr 14 refresh. All removed.
7. **Scribe learnings cleanup** — learnings #23 (`KXTRUMPSAY-26APR20-ALLA` "loss") and #25 (`KXHIGHMIA-26APR20-T86` "loss") deactivated after CSV confirmed both markets resolved NO/100 (i.e. our NO thesis was correct; the realized loss came from a premature stop, not a thesis error). Replaced with corrected execution-pattern learning.

Net filter entries: 17 → 26. Win rate on qualifying trades: 100.0%.
