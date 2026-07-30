---
name: update-market-shortlist
description: Recompute the 100%-win market shortlist from backend/monitoring/markets.csv, update markets_data_dive.md, and sync backend/coliseum/agents/scout/filters.py to the new zero-loss allowlist.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Edit, MultiEdit, Bash, Write
---

# Update Market Shortlist

Use this skill when the user wants to refresh the Scout shortlist from the latest tracked CSV data.

## Goal

Re-run the full market-shortlist workflow using `backend/monitoring/markets.csv`, then update:

- `markets_data_dive.md`
- `backend/coliseum/agents/scout/filters.py`

The end state should keep only event families with a historical `100%` win rate in the analyzed dataset, with explicit prefix-specific price gates when needed.

## Inputs

- Optional: `$ARGUMENTS`
- If arguments are provided, treat them as analyst guidance only. Do not change the core safety criterion of selecting only historically 100%-win buckets unless the user explicitly asks for a looser strategy.

## Required context

Before editing anything, read:

- `AGENTS.md`
- `markets_data_dive.md`
- `backend/coliseum/agents/scout/filters.py`

## Workflow

1. Run `scripts/analyze_market_shortlist.py` (located alongside this skill file) to get the full analysis including event diversity metrics.
2. Review the script output. It provides: overall stats, per-category breakdown, per-prefix breakdown with event diversity, and price-gated candidates with event diversity.
3. Apply the conservative selection criteria (see below) to determine the shortlist.
4. Update `markets_data_dive.md` with the new analysis, revised shortlist, and re-qualification watchlist.
5. Update `backend/coliseum/agents/scout/filters.py` so the implementation matches the latest findings exactly.
6. Keep the filter implementation simple:
   - unconditional safe categories
   - unconditional safe prefixes
   - price-gated prefixes
   - default reject
7. Validate after edits using the project commands from `.factory/services.yaml`.

## Conservative Selection Criteria

These rules encode a conservative approach to choosing events. Follow them strictly.

### Trade count is not enough — event diversity is required

A "trade" is one contract. An "event" is one distinct `event_ticker`. Multiple trades from the same event are correlated — they resolve together. A prefix with 18 trades from 2 events is really 2 independent observations, not 18.

Always compute both `trades` (total winning contracts) and `events` (distinct `event_ticker` values) for every candidate.

### Minimum thresholds for inclusion

| Type | Min trades | Min distinct events |
|------|-----------|-------------------|
| Unconditional category | 30 | n/a (categories are broad) |
| Unconditional prefix | 8 | 5 |
| Price-gated prefix | 8 at the gate | 5 at the gate |

If a prefix meets the trade threshold but not the event threshold (e.g., 18 trades from 2 events), it does NOT qualify. Add it to the re-qualification watchlist instead.

### Prefer not adding over adding

When in doubt, exclude. The cost of missing a good trade (false negative) is low. The cost of including a bad trade (false positive) is high — it breaks the 100% win rate.

### Do not relax existing gates

If a prefix already has a price gate (e.g., `KXETH >= 96`), do not relax it (e.g., to `>= 94`) unless the evidence at the lower gate is overwhelming: at least 20 trades AND 10 distinct events at the new gate. Maintaining consistency with structurally similar prefixes (e.g., all crypto directional at `96c`) is a feature, not a bug.

### Structural similarity matters

If a prefix belongs to a family where other members need a price gate (e.g., `KXBTCD >= 96`, `KXETHD >= 96`), do not allow a structurally similar new member unconditionally (e.g., `KXSOLD` without a gate) just because it has a small zero-loss sample. The structural risk applies equally; the small sample just hasn't shown it yet.

Families with known structural risk:
- **Crypto directional** (`KXBTCD`, `KXETHD`, `KXSOLD`, `KXXRPD`): require `96c` gate minimum
- **Northeast weather** (`KXHIGHNY`, `KXHIGHTBOS`, `KXHIGHTDC`): require tight gates or reject
- **Trump-adjacent mentions** (`KXTRUMPMENTION`, `KXTRUMPMENTIONB`, `KXTRUMPSAY`): require `94c+` gate minimum

### Weather ticker cap

Weather markets are structurally volatile — they account for the majority of losses in the dataset and frequently break gates over time. The shortlist is capped at **3 weather tickers maximum**. When selecting the 3, prefer the ones with the highest trade count, event diversity, and tightest gates. All weather tickers must be price-gated (never unconditional). If a weather ticker breaks its gate, remove it and do not backfill with another weather ticker unless explicitly asked.

### Removing existing entries

If an existing filter entry now fails the minimum thresholds (e.g., it had 0 trades, or its event diversity is below the minimum), remove it. The filter should be based on current evidence, not inertia.

### Re-qualification watchlist

Any prefix with 100% win rate but insufficient trades or event diversity should be listed in a "Re-qualification Watchlist" section in `markets_data_dive.md`. This tracks candidates that may earn their way in as more data accumulates.

## Guardrails

- Do not use broad category rules for `Crypto` or `Sports` unless the data clearly supports them with zero losses.
- Use the actionable Scout-side entry price that corresponds to the selected tradeable side; do not assume `max(yes_ask, no_ask)` is always the implementation detail.
- Keep the Scout filter auditable and deterministic.
- Prefer exact allowlists over heuristic prose.
- Do not edit unrelated files.
- Do not commit changes.

## Verification

Run these validations before finishing:

1. `.factory/services.yaml` `lint` command
2. `.factory/services.yaml` `typecheck` command
3. `.factory/services.yaml` `test` command
4. `python3 -m py_compile backend/coliseum/agents/scout/filters.py`

## Success criteria

- `markets_data_dive.md` reflects the latest CSV-backed analysis
- `backend/coliseum/agents/scout/filters.py` matches the documented shortlist
- validators pass
- final summary includes:
  - updated qualifying-trade count
  - whether any previously safe bucket became unsafe
  - whether any new bucket was added or removed
  - event diversity metrics for all included entries
