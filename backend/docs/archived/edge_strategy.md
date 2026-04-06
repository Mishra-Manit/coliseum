# Edge Trading Strategy (Archived)

## Status

This document preserves the historical **Edge Trading** design that was removed from active runtime behavior.

- Runtime mode now: **sure_thing only**
- Edge-specific execution paths: **removed**
- Edge math module: **retired to compatibility shim**

---

## What the Edge Strategy Was

The archived Edge approach targeted **market mispricing capture** instead of hold-to-resolution certainty.

Core idea:

1. Estimate a truer outcome probability from research.
2. Compare that estimate to market-implied pricing.
3. Enter when mismatch was favorable.
4. Size using probabilistic bankroll formulas.
5. Exit when enough repricing had been captured, not necessarily at event settlement.

This contrasted with the current sure-thing flow, which is centered on near-decided markets and reversal-risk screening.

---

## Historical Architecture

The strategy was implemented through the same multi-agent pipeline, but with Edge-focused logic at key stages:

- **Scout**: found markets likely to be mispriced and tradable for repricing.
- **Analyst / Researcher**: gathered factual context to support probability judgments.
- **Analyst / Recommender**: produced recommendation fields tied to probabilistic pricing mismatch and sizing.
- **Trader**: used recommendation output to choose side and contract sizing within risk limits.
- **Guardian**: designed to monitor open positions and enforce profit/stop/time exits for repricing workflows.

---

## Historical Math and Decision Inputs

The prior implementation used a probability-and-sizing framework with:

- pricing mismatch calculations,
- return expectation calculations,
- bankroll fraction sizing,
- additional hard caps from risk configuration.

These calculations previously informed recommendation quality and position sizing decisions before execution.

---

## Historical Data and Frontmatter Shape

Opportunity/trade artifacts previously carried strategy-era metadata such as:

- recommendation quantitative scoring fields,
- sizing-related recommendation values,
- strategy-identifying frontmatter fields in opportunities/trades,
- compatibility fields expected by older API/frontend payloads.

During deprecation, these were removed from active models and payloads to keep one clean sure-thing schema.

---

## Where It Lived in Code (Before Removal)

The Edge implementation was historically spread across:

- Analyst recommender models/prompts/runtime
- Analyst calculations module
- Trader prompt/runtime decision expectations
- Opportunity/trade persistence models
- API response shaping
- CLI status output
- Frontend dashboard types and strategy labels
- Config keys for strategy-scoped behavior
- Documentation describing legacy math and repricing thesis

---

## Decommissioning Summary

The following categories were removed or simplified to enforce sure-thing-only behavior:

1. **Strategy branching logic**
   - Removed multi-strategy checks and fallbacks.
   - Kept a single execution path.

2. **Recommendation schema bloat**
   - Removed legacy quantitative recommendation fields no longer used by sure-thing flow.

3. **Persistence and API contract cleanup**
   - Removed strategy fields from opportunity/trade model usage where no longer meaningful.
   - Aligned API responses to simplified payloads.

4. **Frontend type and UI cleanup**
   - Removed legacy strategy-related payload assumptions.
   - Switched to fixed single-mode labeling in the dashboard.

5. **Prompt and narrative cleanup**
   - Removed legacy quantitative strategy wording from active prompts.

6. **Configuration cleanup**
   - Removed obsolete top-level strategy toggles and edge-only knobs from active config usage.

7. **Documentation cleanup**
   - Moved historical context into this archive document.

---

## Notable File-Level Changes in This Removal Pass

Representative files adjusted during decommissioning include:

- `backend/coliseum/pipeline.py`
- `backend/coliseum/__main__.py`
- `backend/coliseum/api/server.py`
- `backend/coliseum/storage/files.py`
- `backend/coliseum/config.py`
- `backend/coliseum/agents/analyst/models.py`
- `backend/coliseum/agents/analyst/prompts.py`
- `backend/coliseum/agents/analyst/researcher.py`
- `backend/coliseum/agents/analyst/recommender.py`
- `backend/coliseum/agents/analyst/calculations.py` (retired to shim)
- `backend/coliseum/agents/scout/main.py`
- `backend/coliseum/agents/scout/prompts.py`
- `backend/coliseum/agents/trader/main.py`
- `backend/coliseum/agents/trader/prompts.py`
- `backend/coliseum/test_pipeline/run.py`
- `backend/config.yaml`
- `backend/test_data/config.yaml`
- `frontend/lib/types.ts`
- `frontend/components/dashboard/opportunities-feed.tsx`
- `frontend/components/dashboard/opportunity-detail.tsx`
- `frontend/components/dashboard/dashboard-navbar.tsx`

---

## Why This Archive Exists

This record is intentionally retained so future maintainers can understand:

- what was removed,
- why old references may appear in historical commits,
- how the prior architecture was structured,
- and why current runtime behavior is deliberately constrained to one strategy.

For active behavior, rely on the current sure-thing code and docs, not this archived strategy description.