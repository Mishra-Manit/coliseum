# Markets Data Dive: Scout Shortlist (Jul 30, 2026)

**Filter of record**: `backend/coliseum/agents/scout/filters.py`
**Shape**: one flat allowlist of 16 series + a global 94c entry floor. No tiers, no per-family gates.

## Selection rule

A series is included only if it clears all three thresholds on the **combined** record:

| Threshold | Value | Why |
|---|---|---|
| Resolved trades at >=94c | >= 15 | Small samples at 96c are indistinguishable from noise |
| Distinct events | >= 5 | An event is the independent unit, not a trade |
| Combined accuracy | >= 97.5% | Break-even at 95c is 95%; this leaves ~2.5 points of margin |

## Evidence sources

Three independent sources, combined per family:

| Source | What it is | Bias |
|---|---|---|
| **CSV** | `backend/monitoring/markets.csv`, entries >=94c | In-sample — the filter was fit on it |
| **LIVE** | `trade_closes` in Supabase, real fills Apr–Jun 2026 | Real money, real slippage |
| **OOS** | Paper decisions after Jul 8 2026, resolved against Kalshi | **Forward-tested** — the only honest sample |

The CSV alone cannot validate the filter: selecting zero-loss buckets from a dataset and then
scoring on that same dataset returns ~100% by construction. That number is the selection rule
restated, not evidence. Only the OOS column is predictive.

## The shortlist (16 series)

`*` marks families carrying forward-tested evidence.

| Series | Combined | Events | Category |
|---|---|---|---|
| KXWTIW `*` | 130W/2L | 9 | Commodities |
| KXBRENTW | 33W/0L | 6 | Commodities |
| KXAAAGASW `*` | 50W/1L | 7 | Commodities |
| KXGOLDW | 16W/0L | 5 | Commodities |
| KXETH15M | 27W/0L | 26 | Crypto 15-min |
| KXBTC15M | 22W/0L | 22 | Crypto 15-min |
| KXSOL15M | 17W/0L | 17 | Crypto 15-min |
| KXETH `*` | 51W/1L | 25 | Crypto spot |
| KXJOBLESSCLAIMS `*` | 32W/0L | 6 | Economics |
| KXTSAW `*` | 15W/0L | 7 | Economics |
| KXTRUMPMENTION | 29W/0L | 9 | Mentions |
| KXRT `*` | 41W/1L | 7 | Entertainment |
| KXHIGHTPHX | 73W/0L | 39 | Weather |
| KXHIGHTSFO | 74W/1L | 41 | Weather |
| KXLOWTLAX | 64W/1L | 40 | Weather |
| KXHIGHCHI | 129W/3L | 53 | Weather |

Weather is deliberately capped at four tickers. Those markets are correlated with one another on
any given day, so adding more buys diversification that is not real.

## How it backtests

| Source | Admitted | Result |
|---|---|---|
| CSV | 636 | 630W 6L, 99.06% |
| LIVE | 54 | 52W 2L, **+$6.40** (actual unfiltered result was −$2.85) |
| OOS | 123 | 121W 2L, 98.37%, **EV +2.37c/contract at 96c** |

The LIVE row is the useful one: the filter removes $9.25 of realized losses from the same period,
including the two worst single trades (`KXAAAGASD` −$4.70, `KXBRENTD` −$3.60).

## Caveats — read before scaling size

**The out-of-sample sample is smaller than it looks.** 123 trades resolve off only **17 distinct
events**. 51 KXWTIW trades come from 3 weekly crude settlements — that is 3 bets, not 51. At n=17
you cannot distinguish 98% from 92%.

**Confidence is not predictive.** Decisions with confidence <0.70 went 39/39; the 0.70–0.80 band
went 0.966. Do not size on the model's confidence score.

**Margins are thin by construction.** At 96c the payoff is 4.2:1 against you — 96% accuracy just
breaks even. Kalshi fees (`0.07 × C × P × (1−P)`, ~0.27c at 96c) consume ~11% of the measured edge.

**Zero-loss is a finite-sample artifact.** Several families listed as zero-loss will eventually
lose. `KXAAAGASW` and `KXGOLDD` were both zero-loss in the CSV and then lost real money at 96c —
which is why the 97.5% bar is a floor, not a target.

## Rejected, with cause

| Series | Why |
|---|---|
| KXAAAGASD | 2 live trades, −$4.50, worst single loss on record |
| KXETHD | 155W/9L = 94.5%, below the accuracy bar |
| KXBRENTD | 76W/2L but −$3.60 realized; 97.4%, just under the bar |
| KXGOLDD | Zero-loss in CSV, then lost at 96c live |
| KXHIGHMIA | 112W/5L = 95.7%, below the bar |
| KXNASDAQ100 / KXNASDAQ100U | 90.9% / 93.3% |
| KXNETFLIXRANK\* | Under 15 combined trades, or under the accuracy bar |
| KXMLBSTGAME, KXWBCGAME, KXPRESMENTION, KXPOLITICSMENTION | Under 15 combined trades |

## Re-qualification

A rejected series re-enters only by clearing the same three thresholds on refreshed data. Prefer
adding forward-tested evidence over re-running the CSV, which cannot falsify a filter derived
from it.
