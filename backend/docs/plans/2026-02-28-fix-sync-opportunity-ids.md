# Fix sync_xxx Opportunity IDs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure positions opened by the Trader always carry `opp_xxx` opportunity IDs, never `sync_xxx` placeholders.

**Architecture:** Two independent fixes. First, patch `execute_working_order` to do a final `get_order_status` call after `cancel_order`, catching any fills that landed in the cancel window. Second, bookend both the production and test pipelines with Guardian at start and end so post-trade reconciliation happens immediately after trades execute.

**Tech Stack:** Python, asyncio, Kalshi API client, state.yaml (YAML), pydantic

---

### Task 1: Final status poll after cancel in `execute_working_order`

**Root cause:** When `execute_working_order` exhausts its reprice attempts, it calls `client.cancel_order(order_id)` then checks `order.fill_count` from the *previous* `get_order_status` call (line 336). Fills that arrived during or after the cancel are invisible. `contracts_filled` returns 0, `_update_state_after_trade` is never called, and Guardian later stamps the position `sync_xxx`.

**Files:**
- Modify: `backend/coliseum/agents/trader/main.py:384-407`

**Step 1: Read the exact cancellation block**

The block to change is the `else` branch of `if attempt < max_attempts - 1` inside the loop (around line 380):

```python
else:
    # Out of attempts, cancel
    await client.cancel_order(order_id)
    logger.info(f"Cancelled order {order_id} after {max_attempts} attempts")

    # Return partial fill if any
    if order.fill_count > 0:
        ...
    return OrderResult(order_id=order_id, status="cancelled")
```

`order` here is stale — it's the result of `get_order_status` from line 336, *before* the cancel.

**Step 2: Add the final poll immediately after `cancel_order`**

Replace the cancellation block (the `else` branch at the bottom of the loop) with:

```python
else:
    # Out of attempts, cancel
    await client.cancel_order(order_id)
    logger.info(f"Cancelled order {order_id} after {max_attempts} attempts")

    # Final poll — catch any fills that landed during the cancel window
    try:
        order = await client.get_order_status(order_id)
    except Exception as exc:
        logger.warning("Final status poll failed for %s: %s", order_id, exc)

    # Return partial fill if any
    if order.fill_count > 0:
        fill_price_decimal = (
            (order.taker_fill_cost + order.maker_fill_cost)
            / (order.fill_count * 100)
        )
        total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100
        return OrderResult(
            order_id=order_id,
            fill_price=fill_price_decimal,
            contracts_filled=order.fill_count,
            total_cost_usd=total_cost,
            status="partial",
        )

    return OrderResult(
        order_id=order_id,
        status="cancelled",
    )
```

**Step 3: Verify the diff is minimal**

The only change is inserting the `try/except` block for `order = await client.get_order_status(order_id)` between `cancel_order` and the fill count check. Nothing else changes.

**Step 4: Commit**

```bash
git add backend/coliseum/agents/trader/main.py
git commit -m "fix: final status poll after cancel to catch late fills in execute_working_order"
```

---

### Task 2: Add Guardian at end of production pipeline

**Context:** `backend/coliseum/pipeline.py` currently runs:
`Guardian → Scout → (Analyst → Trader) × n`

After trades execute, there's no reconciliation. Any fills missed by the Trader (edge case) will be picked up by the *next* pipeline run's opening Guardian, not the current one. Adding Guardian at the end closes this gap immediately.

**Files:**
- Modify: `backend/coliseum/pipeline.py:71` (after the final log line)

**Step 1: Add the closing Guardian call**

Append to `run_pipeline` after the `logger.info(f"Pipeline complete...")` line:

```python
    # Final Guardian: reconcile any positions opened this cycle
    try:
        guardian_result = await run_guardian(settings=settings)
        logger.info(
            "Guardian (post-trade) complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        logger.error(f"Guardian (post-trade) failed: {e}")
```

Also update the docstring on line 15 from:
```python
"""Run one full pipeline cycle: Guardian -> Scout -> (Analyst -> Trader)."""
```
to:
```python
"""Run one full pipeline cycle: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""
```

And the log on line 16 from:
```python
logger.info("Pipeline starting: Guardian -> Scout -> (Analyst -> Trader)")
```
to:
```python
logger.info("Pipeline starting: Guardian -> Scout -> (Analyst -> Trader) -> Guardian")
```

**Step 2: Commit**

```bash
git add backend/coliseum/pipeline.py
git commit -m "feat: add post-trade Guardian reconciliation at end of production pipeline"
```

---

### Task 3: Add Guardian at start of test full pipeline

**Context:** `backend/coliseum/test_pipeline/run.py`'s `run_full_pipeline` currently runs:
`Scout → (Analyst → Trader) × n → Guardian`

The production pipeline runs Guardian at the *start* to sync state before trading. The test pipeline should mirror this. Add a Guardian step before Scout.

**Files:**
- Modify: `backend/coliseum/test_pipeline/run.py:567` (before the Scout step)

**Step 1: Import `run_guardian` at the top of the file**

The file currently does not import `run_guardian`. Add it to the existing guardian imports (around line 46):

```python
from coliseum.agents.guardian.main import (
    _find_positions_without_opportunity_id,
    reconcile_closed_positions,
    run_guardian,
)
```

**Step 2: Add the opening Guardian step in `run_full_pipeline`**

Insert before the existing `# Step 1: Scout` block (around line 567), renumbering the existing steps:

```python
    # Step 1: Guardian - Pre-trade sync
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: Guardian - Pre-trade reconciliation")
    logger.info("=" * 70)
    try:
        guardian_result = await run_guardian(settings=settings)
        logger.info(
            "Guardian (pre-trade) complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        logger.error(f"Guardian (pre-trade) failed: {e}")
```

Then renumber the existing steps:
- Old "STEP 1: Scout" → "STEP 2: Scout"
- Old "PROCESSING OPPORTUNITY" block → "STEP 3: Analyst + Trader per opportunity"
- Old "STEP 4: Guardian" → "STEP 5: Guardian - Post-trade reconciliation"

Also update the header log and footer log to reflect the new flow:
- Header: `"Running: Guardian -> Scout -> (Analyst -> Trader) for each -> Guardian"`
- Footer: `"Flow: Guardian -> Scout -> (Analyst -> Trader) for each -> Guardian"`

**Step 3: Commit**

```bash
git add backend/coliseum/test_pipeline/run.py
git commit -m "feat: add pre-trade Guardian reconciliation at start of test full pipeline"
```
