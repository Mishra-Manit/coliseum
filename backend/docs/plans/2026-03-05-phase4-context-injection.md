# Phase 4: Context Injection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing memory system into each LLM agent's prompts so accumulated knowledge (recent decisions, portfolio state, system learnings) shapes every run, and enrich Guardian's ClosedPosition records with the original entry rationale from the opportunity file.

**Architecture:** A single new module `coliseum/memory/context.py` assembles formatted context strings from existing memory loaders — no new storage, no new models (except one field on ClosedPosition). Each agent's prompt-building function gets a context block prepended. Guardian gets a pure file-read enrichment when it closes positions.

**Tech Stack:** Python, existing `coliseum.memory.*` loaders, existing `coliseum.storage.files`, Pydantic, plain string formatting.

**No tests exist in this repo (`pytest` is not set up). Verify by running `python -m coliseum run --once` or each agent's CLI subcommand after each task.**

---

## Task 1: Create `coliseum/memory/context.py` — the context assembler

This is the only new file. It has three pure functions that load memory and return formatted strings for injection into agent prompts. No side effects, no I/O beyond reading existing files.

**Files:**
- Create: `backend/coliseum/memory/context.py`
- Modify: `backend/coliseum/memory/__init__.py`

**Step 1: Create the module**

```python
# backend/coliseum/memory/context.py
"""Context assemblers: load memory and format it for injection into agent prompts."""

from coliseum.memory.decisions import DecisionEntry, load_recent_decisions
from coliseum.memory.journal import load_recent_journal
from coliseum.memory.learnings import load_learnings
from coliseum.storage.state import PortfolioState, load_state


def _format_decisions(decisions: list[DecisionEntry]) -> str:
    if not decisions:
        return "  (none in the last 24h)"
    lines = []
    for d in decisions:
        price_str = f"@ {d.price * 100:.0f}¢" if d.price else ""
        status_str = f"({d.execution_status})" if d.execution_status else ""
        reason_str = f' — "{d.reasoning[:80]}"' if d.reasoning else ""
        lines.append(f"  - {d.action} {d.ticker} {price_str} {status_str}{reason_str}")
    return "\n".join(lines)


def _format_portfolio(state: PortfolioState) -> str:
    p = state.portfolio
    positions = len(state.open_positions)
    tickers = ", ".join(pos.market_ticker for pos in state.open_positions) if state.open_positions else "none"
    return (
        f"  Cash: ${p.cash_balance:.2f} | Positions: ${p.positions_value:.2f} "
        f"({positions} open) | Total: ${p.total_value:.2f}\n"
        f"  Open tickers: {tickers}"
    )


def build_scout_context() -> str:
    """Assemble context block for the Scout agent's user prompt."""
    try:
        state = load_state()
        decisions = load_recent_decisions(hours=24)
        learnings = load_learnings(section="Market Patterns")
    except Exception:
        return ""

    portfolio_block = _format_portfolio(state)
    decisions_block = _format_decisions(decisions)

    return f"""
## System Memory Context

### Portfolio State
{portfolio_block}

### Recent Decisions (last 24h)
{decisions_block}

### System Learnings — Market Patterns
{learnings}

Use this context to avoid re-researching recently skipped tickers and to understand current portfolio exposure before selecting an opportunity.
"""


def build_analyst_context() -> str:
    """Assemble context block for the Analyst Researcher's prompt."""
    try:
        state = load_state()
    except Exception:
        return ""

    portfolio_block = _format_portfolio(state)
    positions_detail = ""
    if state.open_positions:
        lines = [
            f"  - {pos.market_ticker} ({pos.side}, {pos.contracts} contracts @ {pos.average_entry * 100:.0f}¢)"
            for pos in state.open_positions
        ]
        positions_detail = "\n".join(lines)
    else:
        positions_detail = "  (no open positions)"

    return f"""
## Portfolio Context

{portfolio_block}

Open position detail:
{positions_detail}

Account for concentration risk — avoid recommending a position in the same market as an existing holding.
"""


def build_trader_context() -> str:
    """Assemble context block for the Trader agent's prompt."""
    try:
        state = load_state()
        decisions = load_recent_decisions(hours=48)
    except Exception:
        return ""

    portfolio_block = _format_portfolio(state)
    decisions_block = _format_decisions(decisions)

    return f"""
## Execution Memory

### Portfolio State
{portfolio_block}

### Recent Decisions (last 48h)
{decisions_block}

Use recent decisions to detect patterns (e.g., repeated fills at lower-than-ask prices, or repeated rejections on similar market types).
"""
```

**Step 2: Export from `__init__.py`**

In `backend/coliseum/memory/__init__.py`, add:
```python
from coliseum.memory.context import build_scout_context, build_analyst_context, build_trader_context
```

And add to `__all__`:
```python
"build_scout_context",
"build_analyst_context",
"build_trader_context",
```

**Step 3: Smoke-check**

```bash
cd backend && source venv/bin/activate
python -c "from coliseum.memory.context import build_scout_context; print(build_scout_context())"
```

Expected: prints a formatted context block with portfolio state (or empty string if data dir not initialized).

**Step 4: Commit**

```bash
git add backend/coliseum/memory/context.py backend/coliseum/memory/__init__.py
git commit -m "feat: add memory context assemblers for agent prompt injection"
```

---

## Task 2: Wire Scout — inject context into user prompt

Scout's user prompt is built inline inside `run_scout()` in `main.py`. Context goes **before** the market dataset.

**Files:**
- Modify: `backend/coliseum/agents/scout/main.py`

**Step 1: Import the context builder**

At the top of `main.py`, add:
```python
from coliseum.memory.context import build_scout_context
```

**Step 2: Inject into the run prompt**

In `run_scout()`, find the block that builds `prompt`:

```python
prompt = (
    f"Scan Kalshi markets for near-decided opportunities..."
    ...
    f"{_build_market_context_prompt(prefetched_markets)}"
)
```

Replace with:

```python
memory_context = build_scout_context()
prompt = (
    f"Scan Kalshi markets for near-decided opportunities—markets at "
    f"{scout_cfg.min_price}-{scout_cfg.max_price}% where the outcome "
    f"is strongly favored with negligible or low reversal risk. "
    f"Find exactly 1 opportunity—the single least-risky qualifying market. "
    f"Select markets that pass the Risk Assessment Checklist. Remember: residual uncertainty is normal for open markets—do not skip a market just because the outcome is not yet 100% official. "
    f"CRITICAL: You MUST return at least 1 opportunity. If no market meets the ideal risk threshold, select the single least-risky available market as a fallback and label it clearly in the rationale."
    f"{memory_context}"
    f"{_build_market_context_prompt(prefetched_markets)}"
)
```

**Step 3: Verify**

```bash
cd backend && source venv/bin/activate
python -m coliseum scout
```

Expected: Scout runs normally. In Logfire or logs, the agent receives the memory context block before the market JSON. No errors.

**Step 4: Commit**

```bash
git add backend/coliseum/agents/scout/main.py
git commit -m "feat: inject portfolio and decision context into Scout prompt"
```

---

## Task 3: Wire Analyst Researcher — inject portfolio context

The Researcher's prompt is built by `_build_research_prompt()` in `researcher.py`. Portfolio context goes at the top so the agent understands current exposure.

**Files:**
- Modify: `backend/coliseum/agents/analyst/researcher.py`

**Step 1: Import the context builder**

```python
from coliseum.memory.context import build_analyst_context
```

**Step 2: Inject into `_build_research_prompt()`**

Current function signature:
```python
def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
```

Replace the returned string to prepend the context block:

```python
def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
    """Build the research prompt for the agent."""
    header = format_opportunity_header(opportunity)
    memory_context = build_analyst_context()

    return f"""Research this prediction market opportunity and synthesize your findings.
{memory_context}
## Opportunity Details

{header}

**Scout's Rationale**: {opportunity.rationale}

## Your Task

1. Formulate 2-4 very specific research questions about this event
2. Use web search for each question to gather grounded information
3. Synthesize findings into a coherent analysis with embedded sources

## Research Standards

- **Objectivity**: Consider both bullish and bearish evidence
- **Grounding**: Only cite facts from web search results (no hallucination)
- **Base rates**: Start with historical precedents, then adjust for specifics

## Important

You are ONLY responsible for research. Do NOT:
- Estimate probability of YES outcome
- Include pricing metrics or sizing outputs
- Make trade recommendations (BUY/SELL/ABSTAIN)

The Recommender agent will handle the trading decision based on your research.
"""
```

**Step 3: Verify**

```bash
cd backend && source venv/bin/activate
python -m coliseum analyst --opportunity-id <any-existing-opp-id>
```

Expected: Researcher runs, the prompt now includes portfolio context above the opportunity details. No errors.

**Step 4: Commit**

```bash
git add backend/coliseum/agents/analyst/researcher.py
git commit -m "feat: inject portfolio context into Analyst Researcher prompt"
```

---

## Task 4: Wire Analyst Recommender — inject portfolio concentration

The Recommender makes the pass/fail flip-risk decision. Knowing the portfolio's current concentration helps it flag if the opportunity overlaps with an existing position.

**Files:**
- Modify: `backend/coliseum/agents/analyst/recommender.py`

**Step 1: Import the context builder**

```python
from coliseum.memory.context import build_analyst_context
```

**Step 2: Inject into `_build_decision_prompt()`**

Current:
```python
def _build_decision_prompt(opportunity: OpportunitySignal, markdown_body: str) -> str:
```

Replace the returned string:

```python
def _build_decision_prompt(opportunity: OpportunitySignal, markdown_body: str) -> str:
    """Build the evaluation prompt for execution readiness."""
    header = format_opportunity_header(opportunity)
    memory_context = build_analyst_context()

    return f"""Evaluate this research for execution readiness (no final trade decision).
{memory_context}
## Opportunity Details

{header}

## Full Research Context

{markdown_body}

## Your Task

1. Review the research above carefully
2. Identify whether flip risk is present based on the research
3. Write concise reasoning for Trader explaining why this should proceed or be rejected
4. Do not make a final BUY/NO decision (leave action unset)

## Important

- Be disciplined and conservative. When in doubt, downgrade risk
"""
```

**Step 3: Verify**

```bash
cd backend && source venv/bin/activate
python -m coliseum analyst --opportunity-id <any-existing-opp-id>
```

Expected: Recommender runs, prompt includes portfolio context. No errors.

**Step 4: Commit**

```bash
git add backend/coliseum/agents/analyst/recommender.py
git commit -m "feat: inject portfolio concentration context into Analyst Recommender prompt"
```

---

## Task 5: Wire Trader — inject execution history context

The Trader's user prompt is built by `_build_trader_prompt()` in `prompts.py`. Execution history goes before the research body.

**Files:**
- Modify: `backend/coliseum/agents/trader/prompts.py`

**Step 1: Import the context builder**

```python
from coliseum.memory.context import build_trader_context
```

**Step 2: Inject into `_build_trader_prompt()`**

Current function builds a prompt with opportunity details + markdown_body. Add the context block between the opportunity details and the research context:

```python
def _build_trader_prompt(
    opportunity: OpportunitySignal,
    markdown_body: str,
    settings: Settings,
) -> str:
    """Construct trading decision prompt."""
    memory_context = build_trader_context()

    return f"""You are evaluating a trade for execution.

## Opportunity Details

**ID**: {opportunity.id}
**Event Ticker**: {opportunity.event_ticker}
**Market**: {opportunity.market_ticker}
**Title**: {opportunity.title}
**Outcome**: {opportunity.subtitle or "N/A"}
**YES Price**: {opportunity.yes_price:.2%} ({opportunity.yes_price * 100:.1f}¢)
**NO Price**: {opportunity.no_price:.2%} ({opportunity.no_price * 100:.1f}¢)
**Closes**: {opportunity.close_time.strftime('%Y-%m-%d %H:%M UTC') if opportunity.close_time else 'N/A'}
{memory_context}
## Full Research Context

{markdown_body}

## Your Task

1. Review the research—assume BUY by default and only search for concrete crazy flip risk
2. Use `get_current_market_price` to confirm YES or NO is still 92-96%
3. Make your decision: EXECUTE_BUY_YES, EXECUTE_BUY_NO, or REJECT (buy the side at 92-96%)

## Key Questions

- Has the determining event already occurred (per official sources)?
- Do official sources confirm an active process that can realistically reverse settlement soon?
- Is the outcome officially final?

Default to EXECUTE. REJECT only if official evidence shows a credible crazy flip path.
"""
```

**Step 3: Verify**

```bash
cd backend && source venv/bin/activate
python -m coliseum trader --opportunity-id <any-existing-opp-id>
```

Expected: Trader runs, prompt includes execution memory context. No errors.

**Step 4: Commit**

```bash
git add backend/coliseum/agents/trader/prompts.py
git commit -m "feat: inject execution history context into Trader prompt"
```

---

## Task 6: Enrich Guardian ClosedPosition with entry rationale

When Guardian closes a position, it knows the `opportunity_id`. We read the opportunity file to extract the original Scout rationale and embed it in the `ClosedPosition` record for permanent audit trail. This is pure deterministic file I/O — no LLM.

**Files:**
- Modify: `backend/coliseum/storage/state.py` (add field to `ClosedPosition`)
- Modify: `backend/coliseum/agents/guardian/main.py` (add lookup helper, wire into reconciliation)
- Modify: `backend/data/state.yaml` (update schema — add `entry_rationale: null` to any existing closed_positions)

**Step 1: Add `entry_rationale` to `ClosedPosition`**

In `backend/coliseum/storage/state.py`, find the `ClosedPosition` model:

```python
class ClosedPosition(BaseModel):
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    opportunity_id: str | None = None
    closed_at: datetime | None = None
```

Add the new field:

```python
class ClosedPosition(BaseModel):
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    opportunity_id: str | None = None
    closed_at: datetime | None = None
    entry_rationale: str | None = None  # Original Scout rationale from opportunity file
```

**Step 2: Add rationale lookup helper in Guardian**

In `backend/coliseum/agents/guardian/main.py`, add this import at the top:

```python
from coliseum.storage.files import find_opportunity_file_by_id, get_opportunity_markdown_body
```

Then add this helper function (place it before `reconcile_closed_positions`):

```python
def _extract_entry_rationale(opportunity_id: str | None) -> str | None:
    """Read opportunity file and extract the original Scout rationale."""
    if not opportunity_id:
        return None
    try:
        opp_file = find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            return None
        body = get_opportunity_markdown_body(opp_file)
        for line in body.splitlines():
            if line.startswith("**Rationale**:"):
                return line.removeprefix("**Rationale**:").strip()
        return None
    except Exception as exc:
        logger.warning("Could not extract entry rationale for %s: %s", opportunity_id, exc)
        return None
```

**Step 3: Wire into `reconcile_closed_positions()`**

Find the block inside `reconcile_closed_positions()` that creates `ClosedPosition`:

```python
newly_closed.append(
    ClosedPosition(
        market_ticker=pos.market_ticker,
        side=pos.side,
        contracts=pos.contracts,
        entry_price=pos.average_entry,
        exit_price=exit_price,
        pnl=pnl,
        opportunity_id=pos.opportunity_id,
        closed_at=datetime.now(timezone.utc),
    )
)
```

Replace with:

```python
newly_closed.append(
    ClosedPosition(
        market_ticker=pos.market_ticker,
        side=pos.side,
        contracts=pos.contracts,
        entry_price=pos.average_entry,
        exit_price=exit_price,
        pnl=pnl,
        opportunity_id=pos.opportunity_id,
        closed_at=datetime.now(timezone.utc),
        entry_rationale=_extract_entry_rationale(pos.opportunity_id),
    )
)
```

**Step 4: Update `data/state.yaml`**

Open `backend/data/state.yaml`. For any items under `closed_positions:`, add `entry_rationale: null` to each entry so the schema stays consistent. If the list is empty, no change needed.

**Step 5: Smoke-check**

```bash
cd backend && source venv/bin/activate
python -m coliseum guardian
```

Expected: Guardian runs cleanly. If any positions close, their `ClosedPosition` records in `state.yaml` now include `entry_rationale`. No errors.

---

## Final Verification

Run a full pipeline cycle end-to-end:

```bash
cd backend && source venv/bin/activate
python -m coliseum run --once
```

Check:
- Scout log shows "System Memory Context" in its prompt input
- Researcher and Recommender logs show portfolio context
- Trader log shows execution memory context
- `data/state.yaml` closed_positions entries contain `entry_rationale` field (populated or null)
- `data/memory/decisions.jsonl` accumulates entries
- `data/memory/journal/` has today's file updated
