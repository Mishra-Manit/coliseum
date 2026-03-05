# Consolidate Agent Memory into state.yaml

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the three-file memory system (memory.md + opportunity frontmatter status + state.yaml) with a single source of truth: an expanded state.yaml, and make opportunity files pure research artifacts.

**Architecture:** Expand `PortfolioState` in `storage/state.py` with two new sections: `closed_positions` (replacing memory.md EXECUTED/CLOSED entries) and `seen_tickers` (replacing memory.md PENDING entries + Scout dedup). The Guardian writes exclusively to state.yaml by moving positions from `open_positions` to `closed_positions` when Kalshi confirms they closed. Remove memory.py entirely. Strip status tracking out of opportunity file frontmatter.

**Tech Stack:** Python, Pydantic v2, PyYAML, PydanticAI. No test suite exists in this repo — verify each task with a dry-run import check or `python -m coliseum status`.

---

## Current state (read before touching anything)

Three files currently track overlapping lifecycle state:

| File | What it tracks | Who writes |
|------|---------------|------------|
| `data/memory.md` | PENDING→EXECUTED→CLOSED per ticker | Scout, Trader, Guardian |
| `data/opportunities/{date}/{ticker}.md` frontmatter `status` field | pending→researching→recommended→traded/skipped | Scout, Researcher, Recommender, Trader |
| `data/state.yaml` `open_positions` | live open positions | Trader (initial), Guardian (updates) |

After this plan: only `state.yaml` tracks lifecycle. Opportunity files have no `status` field. `memory.py` is deleted.

---

## Task 1: Add `ClosedPosition` model and expand `PortfolioState` in state.py

**Files:**
- Modify: `backend/coliseum/storage/state.py`

**Step 1: Add `ClosedPosition` model after the `Position` class (around line 47)**

Insert this new class between `Position` and `PortfolioState`:

```python
class ClosedPosition(BaseModel):
    """Closed position record — moved here by Guardian when Kalshi confirms close."""

    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    opportunity_id: str | None = None
    strategy: str = "edge"
    traded_at: datetime | None = None
    closed_at: datetime | None = None
    reasoning: str | None = None
```

**Step 2: Extend `Position` model with metadata fields**

Replace the existing `Position` class with:

```python
class Position(BaseModel):
    """Open position details."""

    id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    average_entry: float
    current_price: float
    unrealized_pnl: float
    opportunity_id: str | None = None
    strategy: str = "edge"
    traded_at: datetime | None = None
    reasoning: str | None = None
```

**Step 3: Extend `PortfolioState` with two new sections**

Replace the existing `PortfolioState` class with:

```python
class PortfolioState(BaseModel):
    """Complete portfolio state — the single source of truth."""

    last_updated: datetime | None = None
    portfolio: PortfolioStats
    open_positions: list[Position] = Field(default_factory=list)
    closed_positions: list[ClosedPosition] = Field(default_factory=list)
    seen_tickers: list[str] = Field(default_factory=list)
```

**Step 4: Add helper functions at the bottom of state.py (before or after `save_state`)**

```python
def add_seen_ticker(ticker: str) -> None:
    """Append a ticker to seen_tickers in state.yaml if not already present."""
    state = load_state()
    if ticker not in state.seen_tickers:
        state.seen_tickers.append(ticker)
        save_state(state)


def get_seen_tickers() -> list[str]:
    """Return all tickers that have been discovered by Scout."""
    return load_state().seen_tickers
```

**Step 5: Verify the module imports cleanly**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "from coliseum.storage.state import PortfolioState, Position, ClosedPosition, add_seen_ticker, get_seen_tickers; print('OK')"
```

Expected: `OK`

---

## Task 2: Update sync.py to preserve closed_positions and seen_tickers

`sync_portfolio_from_kalshi` currently overwrites state.yaml completely each run, discarding any `closed_positions` and `seen_tickers`. Fix it to merge those in.

**Files:**
- Modify: `backend/coliseum/storage/sync.py`

**Step 1: Update the import at the top of sync.py**

Add `ClosedPosition` to the imports from `coliseum.storage.state`:

```python
from coliseum.storage.state import (
    ClosedPosition,
    PortfolioState,
    PortfolioStats,
    Position,
    load_state,
    save_state,
)
```

**Step 2: In `sync_portfolio_from_kalshi`, preserve the existing closed_positions and seen_tickers when building `new_state`**

Find the block that builds `new_state` (around line 228) and change it from:

```python
new_state = PortfolioState(
    last_updated=None,
    portfolio=PortfolioStats(
        total_value=total_value,
        cash_balance=cash_balance,
        positions_value=positions_value,
    ),
    open_positions=open_positions,
)
```

To:

```python
new_state = PortfolioState(
    last_updated=None,
    portfolio=PortfolioStats(
        total_value=total_value,
        cash_balance=cash_balance,
        positions_value=positions_value,
    ),
    open_positions=open_positions,
    closed_positions=existing_state.closed_positions,
    seen_tickers=existing_state.seen_tickers,
)
```

`existing_state` is already loaded earlier in the function (line 171 in the original), so this is safe.

**Step 3: Verify**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "from coliseum.storage.sync import sync_portfolio_from_kalshi; print('OK')"
```

Expected: `OK`

---

## Task 3: Update Scout to use state.yaml instead of memory.md

Scout uses `memory.py` for two things: `get_seen_tickers()` for prompt context and `is_market_seen()` + `append_memory_entry()` for dedup. Replace with state.yaml equivalents.

**Files:**
- Modify: `backend/coliseum/agents/scout/main.py`

**Step 1: Replace the memory import block**

Find (around lines 15-20):

```python
from coliseum.storage.memory import (
    MemoryEntry,
    append_memory_entry,
    get_seen_tickers,
    is_market_seen,
)
```

Replace with:

```python
from coliseum.storage.state import add_seen_ticker, get_seen_tickers
```

**Step 2: Remove the `MemoryEntry` construction and `append_memory_entry` call**

Find the block inside the `for opp in output.opportunities` loop (around lines 231-256) that does:

```python
if is_market_seen(opp.market_ticker):
    logger.info(
        f"Skipping duplicate: {opp.market_ticker} (already in memory)"
    )
    skipped_count += 1
    continue

...

memory_entry = MemoryEntry(
    market_ticker=opp.market_ticker,
    discovered_at=now,
    close_time=opp.close_time,
    status="PENDING",
)
append_memory_entry(memory_entry)
added_count += 1
```

Replace with:

```python
seen = get_seen_tickers()
if opp.market_ticker in seen:
    logger.info(
        f"Skipping duplicate: {opp.market_ticker} (already in state)"
    )
    skipped_count += 1
    continue

...

add_seen_ticker(opp.market_ticker)
added_count += 1
```

Note: `get_seen_tickers()` is called once before the loop (it already is, at line 180 in the original). Move the `seen = get_seen_tickers()` assignment before the loop and use `seen` for the `in` check (avoids N state.yaml reads). The `add_seen_ticker()` call after saving the opportunity file is a single write per opp, which is acceptable.

**Step 3: Remove the `seen_context` block that reads from memory (keep the prompt injection logic)**

The existing code at line 179-184 already uses `seen_tickers` from `get_seen_tickers()`. After step 2, this variable comes from state.yaml instead of memory.md. No change needed to the prompt context logic — just confirm the variable name is consistent.

**Step 4: Verify**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "from coliseum.agents.scout.main import run_scout; print('OK')"
```

Expected: `OK`

---

## Task 4: Update Trader to enrich Position with metadata (remove memory.md writes)

Trader currently writes to memory.md in 3 places. All 3 can be removed. On EXECUTED, the Position saved to state.yaml should now carry `opportunity_id`, `strategy`, `reasoning`, and `traded_at`.

**Files:**
- Modify: `backend/coliseum/agents/trader/main.py`

**Step 1: Remove the memory import**

Find (around line 40):

```python
from coliseum.storage.memory import TradeDetails, update_entry
```

Delete this line entirely.

**Step 2: Remove the `update_entry` calls on REJECT and slippage failure**

Find two blocks that look like (around lines 500-504 and 549-552):

```python
update_entry(
    market_ticker=opportunity.market_ticker,
    status="SKIPPED",
)
```

Delete both of these `update_entry(...)` calls. The ticker is already in `state.seen_tickers` from the Scout step, so no additional write is needed.

**Step 3: Enrich the Position object created on successful execution**

Find the `_update_state_after_trade` function (or wherever `Position(...)` is constructed in trader/main.py after a fill). This Position is built and saved to state.yaml. Add the new fields.

The existing Position construction will look something like:

```python
position = Position(
    id=position_id,
    market_ticker=opportunity.market_ticker,
    side=side.upper(),
    contracts=contracts,
    average_entry=fill_price,
    current_price=fill_price,
    unrealized_pnl=0.0,
)
```

Replace with:

```python
position = Position(
    id=position_id,
    market_ticker=opportunity.market_ticker,
    side=side.upper(),
    contracts=contracts,
    average_entry=fill_price,
    current_price=fill_price,
    unrealized_pnl=0.0,
    opportunity_id=opportunity.id,
    strategy=opportunity.strategy,
    traded_at=datetime.now(timezone.utc),
    reasoning=output.decision.reasoning,
)
```

Add `from datetime import datetime, timezone` to imports if not already present.

**Step 4: Remove the `update_entry` call on EXECUTED (around lines 605-614)**

Find and delete:

```python
update_entry(
    market_ticker=opportunity.market_ticker,
    status="EXECUTED",
    trade=TradeDetails(
        side=side.upper(),
        ...
    ),
)
```

**Step 5: Verify**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "from coliseum.agents.trader.main import run_trader; print('OK')"
```

Expected: `OK`

---

## Task 5: Refactor Guardian to reconcile state.yaml instead of memory.md

This is the largest change. Guardian currently reads `parse_memory_file()` to find EXECUTED entries, then calls `update_entry()` to mark them CLOSED. Replace this with: compare old `open_positions` (before Kalshi sync) against new `open_positions` (after sync) — positions that disappeared have closed.

**Files:**
- Modify: `backend/coliseum/agents/guardian/main.py`

**Step 1: Remove memory imports**

Find (line 15):

```python
from coliseum.storage.memory import MemoryEntry, TradeOutcome, parse_memory_file, update_entry
```

Replace with:

```python
from coliseum.storage.state import ClosedPosition, PortfolioState, Position, load_state, save_state
```

Also add to existing state imports if needed.

**Step 2: Refactor `_compute_exit_outcome` to take a `Position` instead of `MemoryEntry`**

The current signature is:

```python
async def _compute_exit_outcome(
    entry: MemoryEntry,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> TradeOutcome:
```

Change to:

```python
async def _compute_exit_outcome(
    pos: Position,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[float, float]:
    """Return (exit_price, pnl) for a position that closed."""
```

Inside the function, replace `entry.trade.side`, `entry.trade.contracts`, `entry.trade.entry_price`, `entry.market_ticker` with `pos.side`, `pos.contracts`, `pos.average_entry`, `pos.market_ticker`.

The return value changes from `TradeOutcome(exit_price, pnl)` to `(exit_price, pnl)`.

**Step 3: Replace `reconcile_memory_with_state` with `reconcile_closed_positions`**

Remove the entire `reconcile_memory_with_state` function and replace with:

```python
async def reconcile_closed_positions(
    old_open: list[Position],
    new_state: PortfolioState,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[PortfolioState, ReconciliationStats]:
    """Detect positions that closed since last sync and move them to closed_positions."""
    new_open_keys = {(pos.market_ticker, pos.side) for pos in new_state.open_positions}
    stats = ReconciliationStats()
    newly_closed: list[ClosedPosition] = []

    for pos in old_open:
        stats.entries_inspected += 1
        key = (pos.market_ticker, pos.side)
        if key in new_open_keys:
            stats.kept_open += 1
            continue

        exit_price, pnl = await _compute_exit_outcome(pos, fills, client)
        newly_closed.append(
            ClosedPosition(
                market_ticker=pos.market_ticker,
                side=pos.side,
                contracts=pos.contracts,
                entry_price=pos.average_entry,
                exit_price=exit_price,
                pnl=pnl,
                opportunity_id=pos.opportunity_id,
                strategy=pos.strategy,
                traded_at=pos.traded_at,
                closed_at=datetime.now(timezone.utc),
                reasoning=pos.reasoning,
            )
        )
        stats.newly_closed += 1
        logger.info(
            "Guardian closed %s exit_price=%.4f pnl=$%.2f",
            pos.market_ticker,
            exit_price,
            pnl,
        )

    updated_state = PortfolioState(
        portfolio=new_state.portfolio,
        open_positions=new_state.open_positions,
        closed_positions=new_state.closed_positions + newly_closed,
        seen_tickers=new_state.seen_tickers,
    )
    save_state(updated_state)
    return updated_state, stats
```

Add `from datetime import datetime, timezone` if not already imported.

**Step 4: Update `reconcile_memory_with_state_tool` in `_register_tools`**

Rename the tool to `reconcile_closed_positions_tool` and update its body:

```python
@agent.tool
async def reconcile_closed_positions_tool(
    ctx: RunContext[GuardianDependencies],
) -> dict[str, object]:
    """Detect positions closed since last sync and move them to closed_positions in state.yaml."""
    if ctx.deps.synced_state is None:
        ctx.deps.synced_state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
    if ctx.deps.fills is None:
        ctx.deps.fills = await ctx.deps.kalshi_client.get_fills(limit=500)

    old_open = load_state().open_positions  # load BEFORE sync to get pre-sync positions
    updated_state, stats = await reconcile_closed_positions(
        old_open=old_open,
        new_state=ctx.deps.synced_state,
        fills=ctx.deps.fills,
        client=ctx.deps.kalshi_client,
    )
    ctx.deps.synced_state = updated_state
    ctx.deps.reconciliation = stats
    return stats.model_dump()
```

Note: `old_open` must be loaded BEFORE the sync tool runs. The Guardian LLM prompt should call `sync_portfolio_from_kalshi_tool` first, then `reconcile_closed_positions_tool`. The `old_open` in the reconcile tool reads state BEFORE the sync overwrites it, which is correct only if called immediately after the sync. To make this safe regardless of call order, store `old_open` in `GuardianDependencies` — see Step 5.

**Step 5: Store pre-sync open_positions in GuardianDependencies**

Open `backend/coliseum/agents/guardian/models.py` and add a field to `GuardianDependencies`:

```python
pre_sync_open_positions: list = Field(default_factory=list)
```

Then in `sync_portfolio_from_kalshi_tool`, capture the old positions before syncing:

```python
@agent.tool
async def sync_portfolio_from_kalshi_tool(
    ctx: RunContext[GuardianDependencies],
) -> dict[str, object]:
    """Sync local state.yaml from live Kalshi portfolio account data."""
    # Capture pre-sync state before overwriting
    pre_sync_state = load_state()
    ctx.deps.pre_sync_open_positions = pre_sync_state.open_positions

    state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
    ctx.deps.synced_state = state
    return {
        "positions_synced": len(state.open_positions),
        "cash_balance": state.portfolio.cash_balance,
        "positions_value": state.portfolio.positions_value,
        "total_value": state.portfolio.total_value,
    }
```

And in `reconcile_closed_positions_tool`, use `ctx.deps.pre_sync_open_positions` instead of loading state again.

**Step 6: Update `_find_positions_missing_in_memory` to `_find_positions_without_opportunity_id`**

Replace the function with:

```python
def _find_positions_without_opportunity_id(state: PortfolioState) -> list[str]:
    """Find open positions that have no opportunity_id (not opened by our pipeline)."""
    return [
        f"{pos.market_ticker}:{pos.side}"
        for pos in state.open_positions
        if not pos.opportunity_id
    ]
```

Update the tool and fallback that calls it accordingly.

**Step 7: Update `_run_guardian_fallback`**

Remove the `parse_memory_file()` call. Use `load_state().open_positions` for pre-sync positions instead:

```python
async def _run_guardian_fallback(client: KalshiClient) -> GuardianResult:
    """Run deterministic fallback reconciliation if agent orchestration fails."""
    pre_sync_state = load_state()
    state = await sync_portfolio_from_kalshi(client)
    fills = await client.get_fills(limit=500)
    updated_state, stats = await reconcile_closed_positions(
        old_open=pre_sync_state.open_positions,
        new_state=state,
        fills=fills,
        client=client,
    )
    missing = _find_positions_without_opportunity_id(updated_state)
    return GuardianResult(
        positions_synced=len(updated_state.open_positions),
        reconciliation=stats,
        warnings=missing,
        agent_summary="Fallback deterministic reconciliation executed after agent error.",
    )
```

**Step 8: Update Guardian system prompt in prompts.py**

Open `backend/coliseum/agents/guardian/prompts.py` and update the tool references from `reconcile_memory_with_state_tool` to `reconcile_closed_positions_tool`.

**Step 9: Verify**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "from coliseum.agents.guardian.main import run_guardian; print('OK')"
```

Expected: `OK`

---

## Task 6: Strip status tracking from opportunity file frontmatter

Opportunity files should be write-once research artifacts. Remove the `status` field from `OpportunitySignal` and delete all `update_opportunity_status` calls.

**Files:**
- Modify: `backend/coliseum/storage/files.py`
- Modify: `backend/coliseum/agents/analyst/researcher/main.py`
- Modify: `backend/coliseum/agents/analyst/recommender/main.py`
- Modify: `backend/coliseum/agents/trader/main.py`

**Step 1: Remove `status` field from `OpportunitySignal` in files.py**

In `coliseum/storage/files.py`, find the `status` field in `OpportunitySignal` (around line 63):

```python
status: Literal[
    "pending", "researching", "recommended", "traded", "expired", "skipped"
] = Field(
    default="pending",
    description="Opportunity lifecycle status."
)
```

Delete this field entirely. Also delete the `OpportunityStatus` type alias at the top of the file and the `update_opportunity_status` function at the bottom.

**Step 2: Remove `update_opportunity_status` import and calls from researcher/main.py**

Find (around line 22):
```python
    update_opportunity_status,
```
Remove this from the import list.

Find the call (around line 80):
```python
update_opportunity_status(opportunity.market_ticker, "researching")
```
Delete this line.

**Step 3: Remove `update_opportunity_status` import and call from recommender/main.py**

Same pattern: remove import line, delete the call to `update_opportunity_status(opportunity.market_ticker, "recommended")` (around line 228).

**Step 4: Remove `update_opportunity_status` import and calls from trader/main.py**

Remove the import line for `update_opportunity_status` from files.py imports.

Delete the three `update_opportunity_status(...)` calls (two for "skipped", one for "traded").

**Step 5: Remove `OpportunityStatus` type alias from state.py**

`state.py` also defines `OpportunityStatus` (line 18-21 in original). Delete it — it's no longer used now that status lives in state.yaml implicitly via `seen_tickers`, `open_positions`, and `closed_positions`.

**Step 6: Verify all four modules import cleanly**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "
from coliseum.storage.files import OpportunitySignal, save_opportunity
from coliseum.agents.analyst.researcher.main import run_researcher
from coliseum.agents.analyst.recommender.main import run_recommender
from coliseum.agents.trader.main import run_trader
print('OK')
"
```

Expected: `OK`

---

## Task 7: Delete memory.py and remove all remaining imports

**Files:**
- Delete: `backend/coliseum/storage/memory.py`
- Modify: `backend/coliseum/__main__.py`

**Step 1: Grep for any remaining memory imports**

```bash
grep -r "from coliseum.storage.memory\|import memory" /Users/manitmishra/Desktop/Coliseum/backend/coliseum --include="*.py" -l
```

Expected: no results (all removed in Tasks 3-5). If any files appear, fix those imports before proceeding.

**Step 2: Remove `create_memory_file_if_missing` call from `__main__.py`**

Open `backend/coliseum/__main__.py` and find any call to `create_memory_file_if_missing()` or any import of it. Delete the call and the import.

**Step 3: Delete memory.py**

```bash
rm /Users/manitmishra/Desktop/Coliseum/backend/coliseum/storage/memory.py
```

**Step 4: Verify full system import**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -c "
import coliseum.storage.state
import coliseum.storage.sync
import coliseum.storage.files
import coliseum.agents.scout.main
import coliseum.agents.analyst.researcher.main
import coliseum.agents.analyst.recommender.main
import coliseum.agents.trader.main
import coliseum.agents.guardian.main
print('All modules OK')
"
```

Expected: `All modules OK`

---

## Task 8: Delete data/memory.md and run a smoke test

**Step 1: Delete the memory file**

```bash
rm /Users/manitmishra/Desktop/Coliseum/backend/data/memory.md
```

**Step 2: Run status to confirm state.yaml loads cleanly**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -m coliseum status
```

Expected: prints portfolio status with no errors.

**Step 3: Run a dry-run scout scan to confirm seen_tickers are written to state.yaml**

```bash
cd /Users/manitmishra/Desktop/Coliseum/backend && source venv/bin/activate && python -m coliseum scout --dry-run
```

Expected: scan completes, `data/state.yaml` now contains a `seen_tickers` section.

---

## New state.yaml schema (reference)

After all tasks complete, `data/state.yaml` will look like:

```yaml
last_updated: '2026-02-19T12:00:00'
portfolio:
  total_value: 100.0
  cash_balance: 100.0
  positions_value: 0.0
open_positions:
  - id: pos_a1b2c3d4
    market_ticker: KXBTCD-26FEB-T89999
    side: YES
    contracts: 5
    average_entry: 0.92
    current_price: 0.94
    unrealized_pnl: 0.10
    opportunity_id: opp_e5f6g7h8
    strategy: edge
    traded_at: '2026-02-19T10:00:00'
    reasoning: Strong consensus across sources, market underpriced by 3¢.
closed_positions:
  - market_ticker: KXBTCD-26JAN-T89999
    side: YES
    contracts: 5
    entry_price: 0.92
    exit_price: 0.95
    pnl: 0.15
    opportunity_id: opp_a1b2c3d4
    strategy: edge
    traded_at: '2026-01-21T10:00:00'
    closed_at: '2026-01-26T23:59:00'
    reasoning: Strong consensus across sources.
seen_tickers:
  - KXBTCD-26JAN-T89999
  - KXBTCD-26FEB-T89999
  - KXSOX-2026-CHC-WIN
```

---

## Key invariants after this change

1. **Guardian writes only to `state.yaml`**: sync overwrites `open_positions` + `portfolio`, reconcile appends to `closed_positions`. One file, one writer per run.
2. **Scout writes only to `state.yaml`** (seen_tickers) and `opportunities/*.md` (research files).
3. **Opportunity files are append-only research text**: no status field, no lifecycle tracking.
4. **`trades/{date}.jsonl`** remains as an immutable append-only audit ledger (untouched by this plan).
5. **`data/memory.md` is gone**: no code references it after Task 7.
