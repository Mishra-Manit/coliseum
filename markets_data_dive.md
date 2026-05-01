# Markets Data Dive: Refreshed 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`
**Refreshed**: Apr 30, 2026
**Scope**: 6,173 completed trades across 2,524 distinct events

---

## Why this refresh exists (capital-preservation override)

Portfolio NAV collapsed from **$25.24 (Apr 18) → $8.85 (Apr 30)** — a 65% drawdown in 12 days. The Apr 27 refresh ("22 rules, conservative") still produced live losses on three of its surviving rules within 72 hours of being deployed. This refresh is therefore deliberately stricter than what the CSV-only "100% rule" would suggest, because the CSV is lagging the live tape.

### Live-trading loss audit (Apr 19–30, post-prior-refresh)

| Date | Ticker | Entry | Exit | PnL | Filter that allowed it |
|------|--------|-------|------|-----|------------------------|
| 4/19 | `KXTRUMPSAY-26APR20-ALLA` | 0.95 | 0.71 | -$1.20 | `ade00eb` (gate 94, since removed) |
| 4/20 | `KXHIGHMIA-26APR20-T86` | 0.96 | 0.66 | -$1.50 | `ade00eb` (gate 96) |
| 4/21 | `KXAAAGASD-26APR21-4.025` | 0.94 | 0.00 | -$4.70 | `ade00eb` (unconditional) |
| 4/23 | `KXBRENTD-26APR23` | 0.94 | 0.49 | -$3.60 | `223a46d` (unconditional, just added) |
| 4/25 | `KXETHD-26APR24` | 0.97 | 0.84 | -$0.13 | `223a46d` (gate 96) |
| 4/27 | `KXGOLDD-26APR27` | 0.96 | 0.58 | -$2.28 | `223a46d` (unconditional) |
| 4/29 | `KXETHD-26APR29` | 0.95 | 0.63 | -$2.56 | `6888916` (gate 96, partial-fill bypass) |
| 4/30 | `KXETHD-26MAY01` | 0.96 | 0.37 | -$0.59 | `6888916` (gate 96) |
| 4/30 | `KXAPRPOTUS-26MAY01-40.6` | 0.96 | 0.51 | -$3.15 | `6888916` (gate 93, day-1 failure) |

**Loss shape is identical across every line**: enter at 0.94–0.97, stop-loss fires at 0.37–0.74, 25–45c slippage on 5–8 contracts wipes 4–10 wins per loss. The filter has zero margin for error, so any rule whose live behavior shows even one stop-out must be removed — it cannot be amortized.

### Structural conclusions from the audit

1. **Directional crypto is broken at every gate.** `KXETHD` lost 3× in 6 days at entries 0.95 / 0.96 / 0.97. Tightening to 97c does not save it (the 0.97 entry stopped out). The whole `KX*D` directional family must come out until a new clean window is observed.
2. **Daily commodity markers (`KXGOLDD`, `KXBRENTD`, `KXAAAGASD`)** failed in identical fashion; intraday vol on these markers eats 96c-NO bets through the stop. Removed in prior refresh; staying removed.
3. **Weather** is the largest historical loss bucket (108 losses, 1,012 events). The Apr 20 KXHIGHMIA stop-out at the 96c gate confirms the gate is no longer protective. **All weather is removed** — the 3-cap policy was already too generous given the realized-vol regime.
4. **Mention-counter family** is bifurcated: `KXPRESMENTION` / `KXPOLITICSMENTION` are deterministic news-counter markets and stay. The Trump-adjacent family (`KXTRUMPMENTION`, `KXTRUMPMENTIONB`, `KXTRUMPSAY`) is correlated and `KXTRUMPSAY` already produced a live loss; the rest of the family is removed under the structural-similarity rule from the skill.
5. **`KXAPRPOTUS`** added Apr 27 at gate 93c lost on its first live entry at 0.96. CSV showed 15W/0L/6 events at 93c — exactly the threshold from the skill, and still failed. This argues for raising the unconditional event-diversity minimum from 5 → 8 for any politics-family addition.
6. **`KXBTC15M`** has 2 historical losses and a small live sample. Removed for now; will be reconsidered after a clean window.
7. **`KXETH` (threshold, not directional)** has 34W/0L at the 94c gate but the broader crypto-directional regime is hot — gate is **tightened from 94 → 95** as a safety hedge.

The CSV is also stale relative to the live tape: `KXETHD ≥96c` shows **49W / 0L** in the CSV, but it is **7W / 3L** in actual closed positions. The refresh therefore runs the CSV analysis as a starting point and then **subtracts** any prefix where live PnL contradicts the CSV.

---

## Baseline Performance (CSV)

| Metric | Value |
|--------|-------|
| Total tracked rows | 6,310 |
| Completed trades | 6,173 |
| Wins (`close_price=100`) | 5,844 |
| Losses (`close_price=0`) | 329 |
| Overall win rate | 94.7% |

---

## Where the 329 Total Losses Come From

### By Category

| Category | W | L | n | Events | Win Rate |
|----------|---|---|---|--------|----------|
| Climate and Weather | 2,108 | 116 | 2,224 | 1,083 | 94.8% |
| Crypto | 2,082 | 99 | 2,181 | 845 | 95.5% |
| Financials | 580 | 51 | 631 | 140 | 91.9% |
| Mentions | 451 | 32 | 483 | 149 | 93.4% |
| Economics | 152 | 6 | 158 | 79 | 96.2% |
| Sports | 78 | 2 | 80 | 35 | 97.5% |
| Entertainment | 147 | 5 | 152 | 91 | 96.7% |
| Politics | 60 | 7 | 67 | 33 | 89.6% |
| Commodities | 96 | 3 | 99 | 22 | 97.0% |
| Elections | 13 | 2 | 15 | 6 | 86.7% |
| Science and Technology | 28 | 2 | 30 | 17 | 93.3% |

No category qualifies for unconditional inclusion.

---

## Changes from Apr 27 refresh

### Removed entries (9)

| Removed Rule | Why |
|--------------|-----|
| `KXETHD ≥96c` | 3 live losses in 6 days at entries 0.95 / 0.96 / 0.97. Gate is no longer protective; directional crypto family is structurally hot. |
| `KXAPRPOTUS ≥93c` | Lost first live entry at 0.96 (-$3.15) one day after being added. Politics-family event diversity (6) too low for the realized risk. |
| `KXTRUMPMENTION ≥94c` | Same correlated family as KXTRUMPSAY which already produced a live loss; structural-similarity rule. |
| `KXTRUMPMENTIONB ≥95c` | Same family as above; only 6 events. |
| `KXHIGHMIA ≥96c` | Live stop-out at 96c on Apr 20 (-$1.50). |
| `KXHIGHTDAL ≥96c` | Same realized-vol regime; no live margin once HIGHMIA broke. |
| `KXLOWTMIA ≥96c` | Same realized-vol regime; weather cap collapsed. |
| `KXBTC15M ≥94c` | 2 historical losses in CSV; small live sample; removing until a clean window appears. |

### Tightened (1)

| Rule | Before | After | Why |
|------|--------|-------|-----|
| `KXETH` | ≥94c | ≥95c | Hedge against current crypto-vol regime; threshold (not directional), so still distinct from KXETHD risk. |

### Kept

All five crypto-15M / sports / mention-counter / weekly-economics / entertainment unconditional rules, plus `KXWTIW ≥94c` (only commodity to survive both the CSV and live tape).

---

## Recommended Scout Filter Set

### Core 100% filter set (12 unconditional + 2 price-gated = 14 rules — down from 22)

| Rule Type | Rule | W | Events |
|-----------|------|---|--------|
| Crypto 15-min | `KXETH15M` (unconditional) | 34 | 34 |
| Crypto 15-min | `KXSOL15M` (unconditional) | 20 | 20 |
| Crypto 15-min | `KXXRP15M` (unconditional) | 15 | 15 |
| Crypto threshold | `KXETH ≥95c` | 32 | 19 |
| Commodities | `KXWTIW ≥94c` | 54 | 7 |
| Sports | `KXMLBSTGAME` (unconditional) | 22 | 12 |
| Sports | `KXWBCGAME` (unconditional) | 8 | 5 |
| Mentions | `KXPRESMENTION` (unconditional) | 13 | 5 |
| Mentions | `KXPOLITICSMENTION` (unconditional) | 10 | 6 |
| Economics | `KXJOBLESSCLAIMS` (unconditional) | 14 | 8 |
| Economics | `KXAAAGASW` (unconditional) | 20 | 6 |
| Economics | `KXTSAW` (unconditional) | 10 | 6 |
| Entertainment | `KXRT` (unconditional) | 14 | 8 |
| Entertainment | `KXARTISTSTREAMSU` (unconditional) | 8 | 8 |

**Filter composition**: Crypto 4, Economics 3, Sports 2, Mentions 2, Entertainment 2, Commodities 1.

---

## What is Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXETHD` (any gate) | 3 live losses at 0.95 / 0.96 / 0.97 in 6 days |
| `KXBTCD`, `KXBTC` | No safe gate; 67 / 15 losses respectively |
| `KXBTC15M` | 2 historical losses; remove until clean window |
| `KXSOLD`, `KXXRPD` directional | Same structural risk as KXETHD/BTCD; XRPD has small clean sample but family-correlated |
| `KXWTI` (daily) | Daily oil structurally unsafe; 32 losses |
| `KXGOLDD`, `KXBRENTD`, `KXAAAGASD` | Live stop-outs in the last 10 days |
| `KXTRUMPSAY`, `KXTRUMPMENTION`, `KXTRUMPMENTIONB` | Correlated family; `KXTRUMPSAY` already lost |
| `KXAPRPOTUS` | Day-1 live failure |
| `KXALBUMSALES` | 3 CSV losses; no zero-loss gate |
| All weather (`KXHIGH*`, `KXLOWT*`) | Largest loss bucket; KXHIGHMIA broke 96c gate live |
| `KXINX*`, `KXNASDAQ100*` | Index gap risk |
| `KXSURVIVORMENTION`, `KXNBAMENTION`, `KXMENTION`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION`, `KXVANCEMENTION`, `KXMELANIAMENTION` | Wording variance or losses |
| `KXNASCARRACE`, `KXHEGSETHMENTION` | Below 5-event minimum |

---

## Re-qualification Watchlist

These prefixes had clean CSV records but are intentionally excluded for capital-preservation reasons. They can be reconsidered after a 2–3 week observation window with no fresh live losses across the broader category.

| Prefix | CSV record | Needs |
|--------|-----------|-------|
| `KXETHD ≥97c` | 49W/0L CSV, 7W/3L live | A clean 2-week window in directional crypto before any re-add |
| `KXBTC15M ≥94c` | 28W/2L CSV | More events at the gate; clean live tape |
| `KXHIGHMIA ≥97c` | strong CSV | New cleanwindow after Apr 20 break |
| `KXHIGHTDAL ≥96c` | 23W/0L CSV at gate | Weather category-wide stability |
| `KXLOWTMIA ≥96c` | 47W/0L CSV at gate | Same |
| `KXTRUMPMENTION ≥95c` | 27W/0L CSV at 94c | Trump-family stability; tighten gate by 1c on re-add |
| `KXAPRPOTUS ≥97c` | 15W/0L CSV at 93c | Higher event diversity (≥8) and a clean live window |
| `KXGOLDD ≥96c` | 21W/0L CSV | Wait for intraday-vol to calm |
| `KXBRENTD ≥95c` | 33W/0L CSV | Same |
| `KXSOLD ≥96c` | 15W/0L | Family-level crypto-directional stability |
| `KXXRPD` | 10W/0L | Family-level crypto-directional stability |
| `KXBRENTW`, `KXGOLDW`, `KXSILVERW` | Weekly clean | Need additional events for diversity |

---

## Bottom Line

Net filter entries: **22 → 14**. This is the smallest filter since the early-April baseline that produced the clean Apr 6–18 equity curve.

Key changes:

1. **All crypto-directional and weather rules removed.** Both buckets produced live losses in the last 10 days at their supposed-safe gates. They re-enter only after a verifiably clean window.
2. **Trump-mention family fully removed** under the skill's structural-similarity rule.
3. **`KXAPRPOTUS` removed** after a day-1 live failure invalidated its CSV signal.
4. **`KXETH` tightened from 94 → 95** as a hedge while the crypto-vol regime is hot.
5. **Re-qualification Watchlist created** so removed buckets can earn back in once a fresh clean window exists.

This filter is intentionally narrower than the data-only "100%-rule" reading would suggest, because the live tape has been ahead of the CSV for ~2 weeks. Trade volume will fall; capital preservation is the priority.
