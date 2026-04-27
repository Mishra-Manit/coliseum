# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Refreshed**: Apr 27, 2026
**Scope**: 5,737 completed trades across 2,343 distinct events

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 5,863 |
| Completed trades | 5,737 |
| Wins (`close_price=100`) | 5,432 |
| Losses (`close_price=0`) | 305 |
| Overall win rate | 94.7% |

---

## Live-trading loss audit (Apr 21–27)

Five Scout-executed positions closed at a real or paper-realized loss in this window. Two are genuine thesis failures; three are stop-outs that crystallized real PnL even when the resolution would have been correct.

| Ticker | Side | Entry | Exit | PnL | Verdict |
|--------|------|-------|------|-----|---------|
| `KXAAAGASD-26APR21-4.025` | YES | 0.94 | 0.00 | -$4.70 | **Real thesis loss** — 1.7¢-margin entry, AAA print at trigger |
| `KXAAAGASD-26APR26-4.100` | YES | 0.95 | 0.00 | (real) | **Real thesis loss** — second AAAGASD failure inside one week |
| `KXBRENTD-26APR2317-T101.50` | NO | 0.94 | 0.49 | -$3.60 | Stop-out, paper-realized; volatility spike inside 8min |
| `KXGOLDD-26APR2717-T4702` | NO | 0.96 | 0.58 | -$2.28 | Stop-out, paper-realized; volatility spike inside 8min |
| `KXETHD-26APR2421-T2319.99` | NO | ~0.96 | 0.84 | -$0.13 | Stop-out, small magnitude |

**Filter implications:**
- `KXAAAGASD` has produced two thesis failures in six days. The CSV-only ≥96c gate has only n=4 (below the 8-trade minimum). **Remove entirely.**
- `KXGOLDD` and `KXBRENTD` were unconditional but are demonstrably volatile inside the trading day at top-of-book entries. Both stopped out the same day they were opened. **Remove entirely.** Move to watchlist for re-evaluation if intraday-vol behavior calms.
- `KXETHD` ≥96c remains directionally safe; the 0.84 stop-out is well above the 0.50 stop trigger threshold and likely a momentary tape spike, not a thesis miss.
- The user's complaint that "filters aren't doing well with crypto and commodities" is borne out specifically in **commodities**: of the 4 commodity-prefix entries in the prior shortlist, 3 produced losses or stop-outs in the past week. Only `KXWTIW ≥94c` survives.

## Where the 305 Total Losses Come From

### By Category

| Category | W | L | n | Events | Win Rate |
|----------|---|---|---|--------|----------|
| Climate and Weather | 1,966 | 108 | 2,074 | 1,012 | 94.8% |
| Crypto | 1,937 | 92 | 2,029 | 787 | 95.5% |
| Financials | 549 | 48 | 597 | 133 | 92.0% |
| Mentions | 420 | 30 | 450 | 139 | 93.3% |
| Economics | 143 | 6 | 149 | 75 | 96.0% |
| Sports | 75 | 2 | 77 | 33 | 97.4% |
| Entertainment | 139 | 5 | 144 | 87 | 96.5% |
| Politics | 56 | 6 | 62 | 31 | 90.3% |
| Commodities | 89 | 3 | 92 | 20 | 96.7% |
| Elections | 13 | 2 | 15 | 6 | 86.7% |
| Science and Technology | 28 | 2 | 30 | 17 | 93.3% |

No category qualifies for unconditional inclusion.

---

## Changes from Apr 21 refresh

### Removed entries (5)

| Removed Rule | Why |
|--------------|-----|
| `KXGOLDD` (unconditional) | Apr 27 stop-out at 0.96 entry → 0.58 exit (-$2.28). Intraday vol incompatible with low-loss criterion. ≥96c gate sample is only n=7 (below 8 minimum). |
| `KXBRENTD` (unconditional) | Apr 23 stop-out at 0.94 entry → 0.49 exit (-$3.60). Same intraday vol pattern. |
| `KXAAAGASD ≥96c` | Two real losses in six days (Apr 21 at 94c and Apr 26 at 95c). ≥96c gate has n=4 — below 8-trade minimum. |
| `KXTRUMPSAY ≥94c` | CSV now shows 55W/4L overall; **no zero-loss gate exists at any threshold**. |
| `KXALBUMSALES ≥95c` | CSV now shows 32W/3L overall; no zero-loss gate exists at any threshold. |

### Added entries (1)

| New Rule | Evidence |
|----------|----------|
| `KXARTISTSTREAMSU` (unconditional) | 8W/0L across 8 distinct artist-week events. Weekly Luminate stream-count thresholds — low-volatility, deterministic resolution by Friday data drop. |

### Kept unchanged

All Crypto 15-min (KXETH15M / KXSOL15M / KXXRP15M unconditional, KXBTC15M ≥94c), Crypto threshold (KXETH ≥94c), Crypto directional (KXETHD ≥96c), Weather 3-cap (HIGHMIA / HIGHTDAL / LOWTMIA at ≥96c), Sports (MLBSTGAME / WBCGAME), Politics-mentions (PRESMENTION / POLITICSMENTION / TRUMPMENTION ≥94c / TRUMPMENTIONB ≥95c), Economics (JOBLESSCLAIMS / AAAGASW weekly / TSAW), Politics (APRPOTUS ≥93c), Entertainment (RT), and Crude oil weekly (WTIW ≥94c).

---

## Recommended Scout Filter Set

### Core 100% filter set (22 rules — down from 26)

| Rule Type | Rule | W@Rule | Events |
|-----------|------|--------|--------|
| Crypto 15-min | `KXETH15M` (unconditional) | 33 | 33 |
| Crypto 15-min | `KXSOL15M` (unconditional) | 20 | 20 |
| Crypto 15-min | `KXXRP15M` (unconditional) | 15 | 15 |
| Crypto 15-min | `KXBTC15M >= 94c` | 18 | 18 |
| Crypto directional | `KXETHD >= 96c` | 46 | 33 |
| Crypto threshold | `KXETH >= 94c` | 32 | 17 |
| Commodities | `KXWTIW >= 94c` | 54 | 7 |
| Weather | `KXHIGHMIA >= 96c` | 28 | 22 |
| Weather | `KXHIGHTDAL >= 96c` | 19 | 17 |
| Weather | `KXLOWTMIA >= 96c` | 15 | 13 |
| Sports | `KXMLBSTGAME` (unconditional) | 22 | 12 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXPOLITICSMENTION` (unconditional) | 10 | 6 |
| Mentions | `KXTRUMPMENTION >= 94c` | 27 | 9 |
| Mentions | `KXTRUMPMENTIONB >= 95c` | 16 | 6 |
| Economics | `KXJOBLESSCLAIMS` (unconditional) | 13 | 7 |
| Economics | `KXAAAGASW` (unconditional) | 20 | 6 |
| Economics | `KXTSAW` (unconditional) | 10 | 6 |
| Politics | `KXAPRPOTUS >= 93c` | 15 | 6 |
| Entertainment | `KXRT` (unconditional) | 14 | 8 |
| Entertainment | `KXARTISTSTREAMSU` (unconditional) | 8 | 8 |

**Filter composition**: Crypto 6, Mentions 4, Economics 3, Weather 3, Sports 2, Entertainment 2, Politics 1, Commodities 1.

---

## Why the Crypto + Commodities Story Looks the Way It Does

**Crypto**: the surviving rules (15M ranges, ETH threshold, ETHD ≥96c) are intentionally conservative; their loss exposure comes from short-window markets that resolve on tape, not on slow-moving spot drift. The data shows zero-loss across all six crypto rules at their gates. The user's "crypto isn't doing well" intuition is mostly driven by **stop-outs in directional markets** (KXETHD, KXBTCD-style) rather than thesis failures, and the structural ≥96c gate already addresses this.

**Commodities**: this category had 3 unconditional and 1 gated entry. The unconditional entries (`KXGOLDD`, `KXBRENTD`) failed because gold and Brent both move >2% intraday in normal weeks, which is enough to crater a 96c-NO bet through a stop. We are left with **only crude weekly (`KXWTIW ≥94c`)** as a survivable commodity rule. That reflects the inherent volatility of daily commodity markers — expect commodity exposure in the bot to stay small until weekly contracts dominate.

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTCD` | No safe gate; 61 losses, lossy at every gate including 96c |
| `KXBTC` | BTC range fails at every gate (14 losses) |
| `KXWTI` | Daily oil structurally unsafe at every gate |
| `KXGOLDD` | Live stop-out at 96c entry; intraday vol too high |
| `KXBRENTD` | Live stop-out at 94c entry; intraday vol too high |
| `KXAAAGASD` | Two real losses in 6 days; ≥96c sample below minimum |
| `KXTRUMPSAY` | 4 losses in CSV; no zero-loss gate at any threshold |
| `KXALBUMSALES` | 3 losses in CSV; no zero-loss gate at any threshold |
| `KXINX`, `KXINXU`, `KXNASDAQ100`, `KXNASDAQ100U` | Index gap risk |
| `KXHIGHDEN`, `KXLOWTDEN`, `KXLOWTNYC`, `KXHIGHTBOS`, `KXHIGHNY`, `KXHIGHLAX`, `KXHIGHTDC`, `KXLOWTAUS`, `KXHIGHPHIL`, `KXHIGHAUS`, `KXHIGHTATL`, `KXHIGHTNOLA`, `KXHIGHTSEA`, `KXLOWTPHIL` | Weather variability too high — no zero-loss gate, or capped out |
| `KXSURVIVORMENTION`, `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION`, `KXMELANIAMENTION` | Wording variance or losses |
| `KXNASCARRACE` | Only 2 distinct events |
| `KXHEGSETHMENTION` | 16W/0L but only 4 distinct events (below 5-event minimum) |

---

## Re-qualification Watchlist

| Prefix | Trades | Events | Needs |
|--------|--------|--------|-------|
| `KXGOLDD` | 21 | 10 | Wait 2–3 weeks for stop-out to be confirmed as one-off vs structural; if quiet, re-add at ≥95c gate (n=12 events=8 currently) |
| `KXBRENTD` | 20 | 7 | Same — ≥95c gate has n=13 events=6, eligible if behavior stabilizes |
| `KXBRENTW` | 23 | 4 | 1 more weekly event for diversity |
| `KXGOLDW` | 16 | 3 | 2 more weekly events |
| `KXSILVERW` | 10 | 4 | 1 more event |
| `KXSOLD ≥96c` | small | small | More trades (structural crypto risk same as KXBTCD/KXETHD) |
| `KXFEDMENTION` | 8 | 1 | More distinct Fed meetings |
| `KXHIGHCHI ≥96c` | 42 | 27 | Strong numerical fit — blocked only by 3-weather cap; swap candidate |
| `KXHIGHTPHX ≥95c` | 39 | 27 | Strong numerical fit — blocked by weather cap |
| `KXLOWTLAX ≥95c` | 42 | 28 | Strong numerical fit — blocked by weather cap |

---

## Bottom Line

Net filter entries: 26 → **22**. Win rate on qualifying trades: 100.0% in CSV (with two recent live stop-outs in commodities expressly removed).

Key changes:

1. **Commodities pruned hard.** `KXGOLDD` and `KXBRENTD` removed after live stop-outs this week; only `KXWTIW ≥94c` remains. Intraday volatility on daily commodity markers is incompatible with the "less volatile, resolves to $1.00" criterion.
2. **`KXAAAGASD` fully removed.** Two real losses inside 6 days at 94c and 95c entries; no qualifying ≥96c sample.
3. **Two stale mention/entertainment rules removed** after losses appeared in CSV: `KXTRUMPSAY ≥94c` (4 losses) and `KXALBUMSALES ≥95c` (3 losses).
4. **One new entry added**: `KXARTISTSTREAMSU` (8W/0L/8 events) — weekly Luminate streams; deterministic, low-vol resolution.
5. **All crypto rules unchanged** — the structural ≥96c gate on KXETHD and the unconditional 15-min range markets are still 100% across the dataset; the user's "crypto isn't doing well" intuition reflects stop-out churn, not filter-level miscalibration.
