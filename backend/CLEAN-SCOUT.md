# Scout Agent Simplification Plan

## Analysis Summary

After thorough exploration of the Scout agent implementation, I've identified **5 key areas of unnecessary complexity** that can be streamlined without compromising functionality or safety.

### Current Architecture (Good Foundation)

The Scout agent follows solid design principles:
- ✅ Clean separation of concerns (agent logic, models, prompts, storage)
- ✅ Type-safe Pydantic models throughout
- ✅ Atomic file writes for data safety
- ✅ Dry-run mode for testing
- ✅ Async-first design

### Identified Complexity Issues

| Issue | Current Impact | Proposed Fix |
|-------|---------------|--------------|
| **1. Triple Deduplication** | 3 redundant duplicate checks (prompt injection + is_market_seen + queue scan) | Remove queue-level O(n) scan, keep prompt injection + is_market_seen safety net |
| **2. Queue O(n) Scan** | Scans ALL queue files on every new opportunity (lines 62-73 in queue.py) | Eliminate - redundant with is_market_seen tracking |
| **3. Multiple State Rewrites** | 20 full state.yaml rewrites for 20 opportunities (mark_market_seen in loop) | Batch all seen_markets updates into single write at end |
| **4. Excessive Cleanup** | Runs cleanup_seen_markets() every Scout scan when markets rarely expire | Move to scheduled daily maintenance job |
| **5. Redundant Queue Parameter** | market_ticker passed to queue_for_analyst() only for redundant dedup | Remove parameter, simplify queue interface |

---

## Detailed Simplification Plan

### 1. Remove Queue-Level Deduplication

**File**: `backend/coliseum/storage/queue.py`

**Current Code** (lines 49-89):
```python
def queue_for_analyst(opportunity_id: str, market_ticker: str | None = None) -> bool:
    queue_dir = _get_queue_dir("analyst")

    # Check for existing queue entry with same market_ticker
    if market_ticker:
        for existing_file in queue_dir.glob("*.json"):  # O(n) scan!
            try:
                data = json.loads(existing_file.read_text(encoding="utf-8"))
                if data.get("market_ticker") == market_ticker:
                    logger.info(f"Skipping duplicate queue for {market_ticker}")
                    return False
            except Exception:
                continue
    # ... rest of function
```

**Simplified Code**:
```python
def queue_for_analyst(opportunity_id: str) -> None:
    """Queue an opportunity ID for the Analyst agent.

    Note: Deduplication is handled upstream via is_market_seen() check.
    """
    queue_dir = _get_queue_dir("analyst")
    file_path = queue_dir / _generate_queue_filename()

    item = {
        "opportunity_id": opportunity_id,
        "queued_at": datetime.utcnow().isoformat(),
    }

    try:
        file_path.write_text(json.dumps(item, indent=2), encoding="utf-8")
        logger.info(f"Queued opportunity {opportunity_id} for Analyst")
    except Exception as e:
        logger.error(f"Failed to queue opportunity {opportunity_id}: {e}")
        raise
```

**Changes**:
- Remove `market_ticker` parameter entirely
- Remove O(n) queue scan (lines 62-73)
- Change return type from `bool` to `None` (no need to signal skip)
- Simplify item dict to only include `opportunity_id` and `queued_at`

**Rationale**: The `is_market_seen()` check at line 191 in scout/main.py already prevents duplicates. The queue scan is redundant and scales poorly (O(n) on every queue operation).

---

### 2. Batch State Updates

**File**: `backend/coliseum/agents/scout/main.py`

**Current Code** (lines 184-224):
```python
# Save opportunities to disk, mark as seen, and queue for Analyst
for opp in output.opportunities:
    try:
        if is_market_seen(opp.market_ticker):
            skipped_count += 1
            continue

        save_opportunity(opp)

        # Mark as seen to prevent future duplicates
        mark_market_seen(  # ← Full state rewrite on EACH opportunity!
            market_ticker=opp.market_ticker,
            opportunity_id=opp.id,
            close_time=opp.close_time,
            status="pending",
        )

        queue_for_analyst(opp.id, market_ticker=opp.market_ticker)
        queued_count += 1
```

**Simplified Code**:
```python
# Save opportunities and collect seen markets for batch update
markets_to_mark = []  # Collect all markets to mark as seen

for opp in output.opportunities:
    try:
        if is_market_seen(opp.market_ticker):
            logger.info(f"Skipping duplicate: {opp.market_ticker}")
            skipped_count += 1
            continue

        # Save opportunity file
        save_opportunity(opp)

        # Collect for batch marking (no state write yet)
        markets_to_mark.append({
            "market_ticker": opp.market_ticker,
            "opportunity_id": opp.id,
            "close_time": opp.close_time,
        })

        # Queue for Analyst (simplified - no market_ticker param)
        queue_for_analyst(opp.id)
        queued_count += 1

        logger.info(f"Queued {opp.priority} priority: {opp.market_ticker}")
    except Exception as e:
        logger.error(f"Failed to save/queue opportunity {opp.id}: {e}")

# Batch update: Mark all markets as seen in ONE state write
if markets_to_mark:
    batch_mark_markets_seen(markets_to_mark)
```

**New Function** in `backend/coliseum/storage/state.py`:
```python
def batch_mark_markets_seen(markets: list[dict]) -> None:
    """Mark multiple markets as seen in a single state write.

    Args:
        markets: List of dicts with keys: market_ticker, opportunity_id, close_time
    """
    state = load_state()
    now = datetime.now(timezone.utc)

    added_count = 0
    for market in markets:
        ticker = market["market_ticker"]

        # Skip if already seen (preserve original discovery)
        if ticker in state.seen_markets:
            logger.debug(f"Market {ticker} already seen, skipping")
            continue

        state.seen_markets[ticker] = SeenMarket(
            opportunity_id=market["opportunity_id"],
            discovered_at=now,
            close_time=market["close_time"],
            status="pending",
        )
        added_count += 1

    if added_count > 0:
        save_state(state)  # Single state write for all markets
        logger.info(f"Batch marked {added_count} markets as seen")
```

**Changes**:
- Collect all markets to mark during opportunity processing loop
- Call new `batch_mark_markets_seen()` once at the end
- Reduces 20 state rewrites to 1 state rewrite

**Performance Improvement**: For 20 opportunities, this reduces from **20 full state.yaml rewrites** to **1 single write** - a 20x reduction in I/O operations.

---

### 3. Move Cleanup to Scheduled Maintenance

**File**: `backend/coliseum/agents/scout/main.py`

**Current Code** (lines 135-142):
```python
# Cleanup expired markets from seen_markets before scanning
if not dry_run:
    try:
        cleaned = cleanup_seen_markets()  # Runs EVERY Scout scan
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired markets")
    except Exception as e:
        logger.warning(f"Failed to cleanup seen_markets: {e}")
```

**Simplified Code**:
```python
# Remove this entire block from run_scout()
# Cleanup will be handled by scheduled maintenance job instead
```

**New Scheduled Job** in `backend/coliseum/scheduler.py`:
```python
def cleanup_seen_markets_job() -> None:
    """Daily maintenance: Remove expired markets from tracking."""
    from coliseum.storage.state import cleanup_seen_markets

    try:
        cleaned = cleanup_seen_markets()
        if cleaned > 0:
            logger.info(f"✓ Maintenance: Cleaned up {cleaned} expired markets")
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}", exc_info=True)

# Add to scheduler (runs daily at 3 AM UTC)
scheduler.add_job(
    cleanup_seen_markets_job,
    trigger=CronTrigger(hour=3, minute=0),
    id="cleanup-seen-markets",
    name="Cleanup Expired Markets",
)
```

**Rationale**:
- Markets rarely expire between Scout scans (scans every 15-60 min, markets close in 24-72 hours)
- Running cleanup every scan is wasteful
- Daily cleanup at 3 AM is sufficient and doesn't add latency to Scout scans

---

### 4. Simplify Queue Interface

**Files**: `backend/coliseum/storage/queue.py` and `backend/coliseum/agents/scout/main.py`

**Current Interface**:
```python
queue_for_analyst(opp.id, market_ticker=opp.market_ticker)  # market_ticker for redundant dedup
```

**Simplified Interface**:
```python
queue_for_analyst(opp.id)  # Simple, clean
```

**Changes**:
- Remove `market_ticker` parameter from `queue_for_analyst()` signature
- Remove `market_ticker` field from queue item JSON
- Update `QueueItem` model in queue.py to remove `market_ticker: str | None = None`

**Affected Call Sites**:
- `backend/coliseum/agents/scout/main.py` line 210

---

### 5. Keep is_market_seen Safety Net

**No changes** - This check stays in place.

**File**: `backend/coliseum/agents/scout/main.py` (lines 191-196)

**Rationale**:
- LLM prompt injection prevents most duplicates
- But LLMs can still make mistakes (hallucinate, ignore instructions)
- This safety net catches any LLM failures
- Minimal performance cost (simple dict lookup)
- Good defensive programming practice

---

## Critical Files to Modify

| File | Changes | Lines Affected |
|------|---------|----------------|
| `backend/coliseum/storage/queue.py` | Remove O(n) dedup scan, simplify signature | 49-89 (queue_for_analyst) |
| `backend/coliseum/storage/state.py` | Add batch_mark_markets_seen() function | New function (~30 lines) |
| `backend/coliseum/agents/scout/main.py` | Batch state updates, remove cleanup call, simplify queue call | 135-224 |
| `backend/coliseum/scheduler.py` | Add cleanup_seen_markets_job scheduled task | New job (~15 lines) |

---

## Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **State writes per Scout scan** (20 opportunities) | 20 | 1 | 20x reduction |
| **Queue dedup complexity** | O(n) scan per item | O(1) dict lookup | O(n) → O(1) |
| **Cleanup overhead** | Every Scout scan (15-60 min) | Once daily | ~24-96x less frequent |
| **Queue file scans** | 20 × (queue_size) | 0 | Eliminated |

---

## Testing Strategy

### Unit Tests to Add/Update

1. **Test batch_mark_markets_seen()**:
   - Verify single state write for multiple markets
   - Check deduplication (skip already-seen markets)
   - Validate timestamps and status

2. **Test simplified queue_for_analyst()**:
   - Verify queue item created with only opportunity_id
   - Check file naming and timestamp prefix
   - Validate JSON structure

3. **Test scheduled cleanup job**:
   - Mock scheduler trigger
   - Verify cleanup_seen_markets() called
   - Check logging output

### Integration Test

```bash
# Run Scout in dry-run mode
cd backend
source venv/bin/activate
python -m coliseum scout --dry-run

# Run Scout with actual persistence
python -m coliseum scout

# Verify:
# 1. Opportunities saved to data/opportunities/
# 2. All markets marked as seen in state.yaml (single batch update)
# 3. Queue items created in data/queue/analyst/
# 4. No duplicate markets in seen_markets or queue
```

### Verification Checklist

After implementation:
- [ ] Scout scan completes without errors
- [ ] Opportunities saved correctly to markdown files
- [ ] All markets appear in state.yaml seen_markets (single update)
- [ ] Queue items created without market_ticker field
- [ ] No duplicate markets in queue or seen_markets
- [ ] cleanup_seen_markets() removed from run_scout()
- [ ] Scheduled cleanup job registered in scheduler
- [ ] Performance: Single state write per scan confirmed via logging

---

## Architecture After Simplification

```
Scout Scan Flow (Simplified):
├── Load seen_tickers from state.yaml
├── Inject into LLM prompt context (prevent LLM duplicates)
├── Run agent with fetch_markets_closing_soon tool
├── For each discovered opportunity:
│   ├── Check is_market_seen() [safety net - quick dict lookup]
│   ├── save_opportunity() → markdown file
│   ├── Collect market for batch tracking
│   └── queue_for_analyst(opportunity_id) [no market_ticker needed]
└── batch_mark_markets_seen() [SINGLE state write for all]

Scheduled Maintenance (Daily 3 AM):
└── cleanup_seen_markets() [remove expired markets]
```

---

## Summary of Benefits

1. **Cleaner Code**: Removes 3 layers of redundant deduplication to 2 necessary layers
2. **Better Performance**: 20x fewer state writes, eliminates O(n) queue scans
3. **Simpler Interface**: queue_for_analyst() becomes trivial one-liner
4. **Lower I/O**: Batch operations reduce disk writes significantly
5. **Maintains Safety**: Keeps is_market_seen() safety net for LLM failures
6. **Same Guarantees**: No change to correctness or deduplication guarantees

---

## Implementation Order

1. **Phase 1**: Add `batch_mark_markets_seen()` to state.py (new function, no breaking changes)
2. **Phase 2**: Update scout/main.py to use batch marking (backward compatible)
3. **Phase 3**: Remove queue dedup scan and market_ticker param (breaking change to queue interface)
4. **Phase 4**: Add scheduled cleanup job to scheduler.py
5. **Phase 5**: Remove cleanup call from scout/main.py
6. **Phase 6**: Run integration tests to verify all changes

This order allows testing each change incrementally before making breaking changes to the queue interface.
