# Coliseum Codebase Simplification Plan

Analysis date: 2026-02-20
Files analyzed: 30+ Python files across agents, storage, services, and infrastructure
Estimated LOC reduction: ~850 lines

---

## Table of Contents

1. [Critical Bug](#1-critical-bug)
2. [Core Infrastructure](#2-core-infrastructure)
3. [Agent Architecture](#3-agent-architecture)
4. [Storage Layer](#4-storage-layer)
5. [Services Layer](#5-services-layer)
6. [Dead Code](#6-dead-code)
7. [Implementation Phases](#7-implementation-phases)

---

## 1. Critical Bug

### pipeline.py:39-42 — Malformed f-string crashes on None edge

**Severity:** CRITICAL — runtime crash

The ternary operator splits the f-string mid-expression, causing a `ValueError` whenever `analyzed.edge is None`. This will crash every sure_thing trade evaluation since sure_thing sets edge to `0.0` (falsy).

```python
# CURRENT (broken):
logger.info(
    f"Analyst complete for {opp.id}: "
    f"edge={analyzed.edge:+.2%}" if analyzed.edge is not None
    else f"Analyst complete for {opp.id}: edge=N/A"
)

# FIX:
edge_str = f"{analyzed.edge:+.2%}" if analyzed.edge is not None else "N/A"
logger.info(f"Analyst complete for {opp.id}: edge={edge_str}")
```

**Also in pipeline.py:**

- `pipeline.py:19` — Scout is called with `strategy=settings.strategy` but this parameter is not used anywhere downstream. Either the Strategy enum is dead or the wiring is missing.
- `pipeline.py:49-52` — Scout and Analyst both receive `dry_run=False`, but Trader does not. Inconsistent API.

---

## 2. Core Infrastructure

### 2.1 __main__.py — Logfire init duplicated 5 times

**File:** `coliseum/__main__.py:29, 256, 297, 338, 377`

The same 7-line try/except block is copy-pasted into every CLI command function:

```python
# Duplicated in cmd_run, cmd_scout, cmd_analyst, cmd_trader, cmd_guardian:
try:
    from coliseum.observability import initialize_logfire
    settings = get_settings()
    initialize_logfire(settings)
except Exception as e:
    logger.warning(f"Failed to initialize Logfire: {e}")
```

**Fix:** Extract once:

```python
def _init_logfire() -> None:
    try:
        from coliseum.observability import initialize_logfire
        initialize_logfire(get_settings())
    except Exception as e:
        logger.warning(f"Failed to initialize Logfire: {e}")
```

**Savings:** ~35 lines removed.

---

### 2.2 __main__.py — Verbose config display (62-line print block)

**File:** `coliseum/__main__.py:146-207`

The `cmd_config()` function has 62 lines of repetitive `print(f"  Key: {value}")` statements organized by section. Each section is manually formatted.

**Fix:** A single utility function handles all sections:

```python
def _print_section(title: str, items: dict[str, str]) -> None:
    print(f"\n{title}:")
    for key, value in items.items():
        print(f"  {key}: {value}")
```

**Savings:** ~40 lines removed.

---

### 2.3 config.py — Hardcoded section list in YAML merge

**File:** `coliseum/config.py:190-198`

The `load_yaml_config()` method uses a hardcoded list of section names to apply YAML overrides. Adding a new config section requires updating this list manually:

```python
# Fragile hardcoded list:
for section_name in ["trading", "risk", "scheduler", "models", "exa", "telegram"]:
    if section_name in yaml_config:
        section = getattr(self, section_name)
        ...
```

**Fix:** Use Pydantic's `model_fields` to auto-detect all BaseModel sections:

```python
for name in self.model_fields:
    if name in yaml_config and isinstance(getattr(self, name), BaseModel):
        old = getattr(self, name)
        merged = old.model_validate({**old.model_dump(), **yaml_config[name]})
        setattr(self, name, merged)
```

**Savings:** Eliminates hardcoded list, auto-adapts when new sections are added.

---

### 2.4 config.py — RSA key loading is overly defensive

**File:** `coliseum/config.py:153-169`

`get_rsa_private_key()` has redundant `is_file()` / `exists()` checks and silent empty-string return. A missing key silently causes auth failures at runtime instead of failing early.

```python
# CURRENT: 17 lines with redundant checks
if key_path.is_file():
    return key_path.read_text()
if key_path.exists():
    logger.warning(f"RSA key path is not a file: {key_path}")
else:
    logger.warning(f"RSA key file not found: {key_path}")

# FIX: 6 lines, clearer intent
if key_path.is_file():
    return key_path.read_text()
logger.warning(f"RSA key not found: {key_path}")
return ""
```

---

### 2.5 llm_providers.py — Duplicate provider detection logic

**File:** `coliseum/llm_providers.py:54-81`

Two functions (`get_model_string` and `get_provider_for_model`) both iterate over model types with identical isinstance chains. Adding a new provider requires updating both.

**Fix:** Single source of truth:

```python
_PROVIDER_PREFIXES: dict[type, tuple[LLMProvider, str]] = {
    OpenAIModel:    (LLMProvider.OPENAI,    "openai-responses"),
    AnthropicModel: (LLMProvider.ANTHROPIC, "anthropic"),
    FireworksModel: (LLMProvider.FIREWORKS, "fireworks"),
}

def get_provider_for_model(model) -> LLMProvider:
    for cls, (provider, _) in _PROVIDER_PREFIXES.items():
        if isinstance(model, cls):
            return provider
    raise ValueError(f"Unknown model type: {type(model)}")

def get_model_string(model) -> str:
    for cls, (_, prefix) in _PROVIDER_PREFIXES.items():
        if isinstance(model, cls):
            return f"{prefix}:{model.value}"
    raise ValueError(f"Unknown model type: {type(model)}")
```

**Savings:** ~20 lines removed, single place to add new providers.

---

### 2.6 scheduler.py — Guardian News Scan is a placeholder

**File:** `coliseum/scheduler.py:46-52`

The Guardian News Scan job is registered but calls `_placeholder_job()` which only logs. This is incomplete functionality running on a schedule:

```python
scheduler.add_job(
    _placeholder_job,                    # Does nothing
    IntervalTrigger(minutes=settings.scheduler.guardian_news_scan_minutes),
    args=["Guardian News Scan"],
    ...
)
```

**Fix:** Either implement it or remove the job registration entirely. Shipping a no-op scheduled job is misleading.

---

### 2.7 scheduler.py — Emojis in logger calls, wrong return type

**File:** `coliseum/scheduler.py:58-60, 67`

Logger calls contain emoji characters (`✓`) which violates the project's no-emoji policy. Additionally, the function is typed `-> NoReturn` but returns normally after catching `KeyboardInterrupt`.

```python
# Remove emojis:
logger.info("Scheduler starting")
logger.info(f"Jobs registered: {len(scheduler.get_jobs())}")

# Fix return type:
def run_scheduler(settings: Settings) -> None:  # not NoReturn
```

---

## 3. Agent Architecture

### 3.1 Analyst — Researcher + Recommender should be merged

**Files:** `analyst/main.py`, `analyst/researcher/main.py`, `analyst/recommender/main.py`

The Analyst agent runs as two sequential sub-agents: Researcher then Recommender. Both:
- Load the same opportunity file independently
- Register near-identical tools (`load_opportunity`, Kalshi client, Exa search)
- Write to the same opportunity file in sequence
- Each incur a full LLM round-trip

Current flow:
```
run_analyst()
  → run_researcher()   # Phase 1: research → appends "## Research Synthesis"
  → run_recommender()  # Phase 2: decide  → appends "## Trade Evaluation"
```

Proposed flow:
```
run_analyst()
  → single agent: load once → research → decide → write both sections
```

**Impact:**
- 1 LLM call instead of 2 per opportunity (50% latency reduction on analyst)
- ~200 LOC removed (duplicate tool registrations, orchestration layer, `analyst/main.py`)
- Single file read/write instead of two
- Cleaner deps model — no need to pass researcher output to recommender via file

**Migration:** The researcher system prompt becomes "Phase 1" in the merged analyst prompt. The recommender system prompt becomes "Phase 2". Tool registrations merge. The `analyst/main.py` orchestrator is deleted.

---

### 3.2 Scout — 500-line prompt with ~50% duplication

**File:** `coliseum/agents/scout/prompts.py`

The scout has two strategy-specific prompts (edge ~300 lines, sure_thing ~185 lines). Four sections are duplicated verbatim between them:

| Section | Duplicated at |
|---|---|
| `_TOOL_USAGE_RULES` | lines 10-50 (both prompts) |
| `_OUTPUT_REQUIREMENTS_CORE` | lines 52-61 (both prompts) |
| `_BANNED_MARKET_LIST` | lines 87-117 (both prompts) |
| `_VALIDATION_STRUCTURAL` | lines 119-137 (both prompts) |

**Fix:** Single parameterized builder:

```python
def build_scout_prompt(strategy: str, min_p: float, max_p: float, max_h: int) -> str:
    strategy_section = _build_strategy_section(strategy, min_p, max_p, max_h)
    return "\n".join([
        SCOUT_CONTEXT,
        strategy_section,
        _TOOL_USAGE_RULES,
        _BANNED_MARKET_LIST,
        _VALIDATION_STRUCTURAL,
    ])
```

**Savings:** ~350 lines → ~150 lines. Any change to shared sections applies once.

---

### 3.3 Scout — Validation checklists belong in Pydantic, not prompts

**File:** `coliseum/agents/scout/prompts.py:282-300, 480-502`

Both strategy prompts contain 40-45 line checkbox validation lists instructing the LLM to validate its own output format. This is the wrong layer for structural validation.

```
# Current: 45 lines telling LLM to self-validate
- [ ] id: non-empty string starting with "opp_"
- [ ] yes_price and no_price: decimal between 0.0 and 1.0
- [ ] volume_24h: non-negative integer
...
```

**Fix:** Pydantic validators on the output model enforce this reliably at parse time:

```python
class ScoutOpportunity(BaseModel):
    id: str = Field(..., pattern=r"^opp_")
    yes_price: float = Field(..., ge=0.0, le=1.0)
    no_price: float = Field(..., ge=0.0, le=1.0)
    volume_24h: int = Field(..., ge=0)
```

**Savings:** ~80 lines removed from prompts, validation is now testable and guaranteed.

---

### 3.4 Scout — Market prefetch logic duplicates what client should own

**File:** `coliseum/agents/scout/main.py:44-134`

`_prefetch_markets_for_scan()` applies 5 sequential filter passes after fetching from Kalshi. The Kalshi client should own filtering since it knows the data shape:

```python
# Current (in scout):
markets = await client.get_markets_closing_in_range(min_hours, max_hours)
markets = [m for m in markets if m.volume >= min_volume]
markets = [m for m in markets if min_price <= m.yes_price <= max_price]
markets = [m for m in markets if spread <= max_spread]  # sure_thing only

# Proposed (in client):
markets = await client.get_filtered_markets(
    closing_hours=(min_hours, max_hours),
    min_volume=min_volume,
    price_range=(min_price, max_price),
    max_spread=max_spread,
)
```

**Savings:** ~90 lines in scout, replaced by a more reusable client method.

---

### 3.5 shared_tools.py — Two nearly-identical tool registration functions

**File:** `coliseum/agents/shared_tools.py:27-99`

`register_load_opportunity()` and `register_load_opportunity_with_research()` are forks of the same function. The only difference is an `include_metrics` block (lines 87-97):

```python
# The ONLY difference between the two functions:
if include_metrics:
    result.update({
        "estimated_true_probability": opportunity.estimated_true_probability,
        "current_market_price": opportunity.current_market_price,
        ...
    })
```

**Fix:** Single function, optional parameter:

```python
def register_load_opportunity(agent, include_metrics: bool = False) -> None:
    @agent.tool
    async def load_opportunity(ctx):
        ...
        if include_metrics:
            result.update({...})
        return result
```

Also: the `deps_attr: str = "opportunity_id"` parameter is never passed with a non-default value. Remove it and hardcode `"opportunity_id"`.

**Savings:** ~45 lines removed.

---

### 3.6 Trader — Duplicated tool registration across strategies

**File:** `coliseum/agents/trader/main.py:90-230`

`_register_edge_tools()` and `_register_sure_thing_tools()` share `get_current_market_price` and `send_telegram_alert` registrations. The sure_thing variant is a strict subset of edge tools.

```python
# Edge registers: portfolio check, price, slippage, place/get/cancel/amend order, telegram
# Sure-thing registers: price (DUPLICATE), telegram (DUPLICATE)
```

**Fix:** Single registration function with strategy flag:

```python
def _register_trader_tools(agent, strategy: str) -> None:
    register_load_opportunity_with_research(agent, include_metrics=(strategy == "edge"))
    _register_get_current_market_price(agent)
    _register_send_telegram_alert(agent)
    if strategy == "edge":
        _register_check_portfolio_state(agent)
        _register_order_execution_tools(agent)
```

**Savings:** ~60 lines removed.

---

### 3.7 Guardian — Three tools each re-initialize the same state

**File:** `coliseum/agents/guardian/main.py:186-238`

Three separate Guardian tools each guard against `ctx.deps.synced_state is None` and re-sync from Kalshi independently. This creates duplicate async calls if the LLM calls them in certain orders:

```python
# sync_portfolio_from_kalshi_tool (line 186):
ctx.deps.pre_sync_open_positions = load_state().open_positions
ctx.deps.synced_state = state

# reconcile_closed_positions_tool (line 213):
if ctx.deps.synced_state is None:
    ctx.deps.pre_sync_open_positions = load_state().open_positions  # DUPLICATE
    ctx.deps.synced_state = await sync_portfolio_from_kalshi(...)

# find_positions_without_opportunity_id_tool (line 236):
if ctx.deps.synced_state is None:
    ctx.deps.synced_state = await sync_portfolio_from_kalshi(...)  # DUPLICATE
```

**Fix:** Single helper called by all three:

```python
async def _ensure_synced_state(ctx: RunContext, client: KalshiClient) -> PortfolioState:
    if ctx.deps.synced_state is None:
        ctx.deps.pre_sync_open_positions = load_state().open_positions
        ctx.deps.synced_state = await sync_portfolio_from_kalshi(client)
    return ctx.deps.synced_state
```

---

### 3.8 Guardian — Fallback reimplements agent logic, defeating its purpose

**File:** `coliseum/agents/guardian/main.py:280-297`

`_run_guardian_fallback()` is a full deterministic reimplementation of what the Guardian agent is supposed to do. If the agent fails, this fallback runs instead. This means:

- The agent is never the authoritative code path
- Two code paths must be kept in sync as logic evolves
- The complexity of maintaining both outweighs the resilience benefit

**Options (pick one):**
1. Remove the agent, run fallback always (deterministic, testable, simpler)
2. Remove the fallback, let agent failures propagate and alert
3. Have the agent call deterministic helpers as tools (hybrid — agent orchestrates, tools are pure functions)

Option 3 is the cleanest long-term architecture.

---

### 3.9 Researcher prompts — 80% identical across strategies

**File:** `coliseum/agents/analyst/researcher/prompts.py`

`RESEARCHER_SYSTEM_PROMPT` (99 lines) and `RESEARCHER_SURE_THING_PROMPT` (51 lines) share context, output format, and constraints. Only the mission and search depth differ.

**Fix:**

```python
_RESEARCHER_SHARED_CONTEXT = """You are a Research Specialist for a prediction market trading system.
Do not hallucinate. Output only grounded, sourced facts.
Return valid JSON: {"synthesis": "...markdown..."}."""

def build_researcher_prompt(strategy: str) -> str:
    if strategy == "sure_thing":
        mission = "Verify no complete YES/NO reversal risk. 1-2 searches maximum."
    else:
        mission = "Validate Scout's mispricing thesis. 3-4 searches. Estimate true probability."
    return f"{_RESEARCHER_SHARED_CONTEXT}\n\nMission: {mission}"
```

**Savings:** ~100 lines → ~20 lines.

---

### 3.10 AgentFactory — 49 lines wrapping two trivial methods

**File:** `coliseum/agents/agent_factory.py`

The `AgentFactory` class provides lazy initialization and API key setup. Its `_setup_api_keys()` method (lines 44-48) does:

```python
settings = get_settings()
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
```

This is simple enough to inline into `get_agent()`. The entire class can be reduced from 49 to ~15 lines without losing any capability.

---

## 4. Storage Layer

### 4.1 files.py — Frontmatter parsing duplicated 5 times

**File:** `coliseum/storage/files.py:179, 255, 272, 315, 354`

The same 4-line YAML frontmatter parsing block appears verbatim in 5 separate functions:

```python
# Repeated at lines 179, 255, 272, 315, 354:
parts = content.split("---", 2)
if len(parts) < 3:
    raise ValueError(f"Could not parse frontmatter in {file_path}")
frontmatter = yaml.safe_load(parts[1]) or {}
```

There is also inconsistent error handling: three functions raise `ValueError` on bad frontmatter, but `find_opportunity_file_by_id()` silently skips malformed files with `continue`.

**Fix:** Single utility:

```python
def _parse_frontmatter(content: str, file_path: Path | str = "") -> dict:
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter in: {file_path}")
    return yaml.safe_load(parts[1]) or {}
```

**Savings:** 4 duplicate blocks removed (~16 lines). Error handling becomes consistent.

---

### 4.2 sync.py — Pass-through wrapper functions add indirection

**File:** `coliseum/storage/sync.py:23-40`

Four public functions are single-line delegates to identically-named private functions:

```python
def normalize_kalshi_side(side):     return _normalize_side(side)
def normalize_probability_price(p):  return _normalize_price(p)
def extract_fill_count(fill):        return _extract_fill_count(fill)
def extract_fill_price(fill):        return _extract_fill_price(fill)
```

There is no documented reason for this split. `sync_portfolio_from_kalshi()` calls `_normalize_side()` directly (private), while `fetch_market_side_price()` calls `normalize_kalshi_side()` (public wrapper). The inconsistency suggests this was unintentional.

**Fix:** Remove private versions, rename public versions to remove leading underscore convention confusion. Use consistently throughout.

**Savings:** 4 functions removed (~12 lines), clearer API.

---

### 4.3 sync.py — Intermediate tuple nesting in average entry computation

**File:** `coliseum/storage/sync.py:106-134`

`_compute_average_entries()` builds a dict of `(total_cost, total_count)` tuples then unpacks them in a dict comprehension. The nested tuple is harder to follow than necessary:

```python
# Current: nested tuple intermediate
totals: dict[tuple[str, str], tuple[float, int]] = {}
totals[key] = (total_cost + price * count, total_count + count)
return {key: cost / count for key, (cost, count) in totals.items() if count > 0}
```

**Fix:** Use `defaultdict` with a list for clearer accumulation:

```python
from collections import defaultdict

totals: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0, 0])
for fill in fills:
    key = (ticker, side)
    totals[key][0] += price * count
    totals[key][1] += count
return {key: v[0] / v[1] for key, v in totals.items() if v[1] > 0}
```

---

### 4.4 files.py — find_opportunity_file() silently returns None on missing directory

**File:** `coliseum/storage/files.py:392-411`

When the opportunities directory does not exist, the function returns `None` with no log output. Callers have no way to distinguish "no opportunities found" from "directory misconfigured":

```python
if not opps_dir.exists():
    return None  # Silent — is this expected or a setup error?
```

**Fix:**

```python
if not opps_dir.exists():
    logger.debug(f"Opportunities directory not found: {opps_dir}")
    return None
```

---

### 4.5 test_pipeline/run.py — Mutates frozen Pydantic model via object.__setattr__

**File:** `coliseum/test_pipeline/run.py:176`

The data directory override function bypasses Pydantic's immutability to mutate a settings singleton:

```python
def patched_get_settings():
    settings = original_get_settings()
    object.__setattr__(settings, 'data_dir', TEST_DATA_DIR)  # Violates immutability
    return settings
```

This is fragile: if `get_settings()` is called before the patch, or if the module structure changes, the patch breaks silently.

**Fix:** Support a `data_dir` override via environment variable only (which the function already sets on line 170). Remove the monkeypatch entirely:

```python
def _override_data_dir() -> None:
    os.environ["DATA_DIR"] = str(TEST_DATA_DIR)
    get_settings.cache_clear()
    # Settings will pick up DATA_DIR on next call — no mutation needed
```

This requires verifying `Settings` reads `DATA_DIR` from env, which it does via Pydantic's env parsing.

---

## 5. Services Layer

### 5.1 kalshi/client.py — Orderbook inversion needs explanation or test

**File:** `coliseum/services/kalshi/client.py:250-267`

The Kalshi API returns `{"yes": [...], "no": [...]}` but the mapping in `get_orderbook()` inverts yes/no for asks:

```python
yes_bids=parse_levels(orderbook.get("yes", [])),
yes_asks=parse_levels(orderbook.get("no", [])),   # Inverted
no_bids=parse_levels(orderbook.get("no", [])),
no_asks=parse_levels(orderbook.get("yes", [])),   # Inverted
```

A comment says "Kalshi inverts this" but there is no test verifying the inversion is correct. If this is wrong, trade pricing is wrong.

**Fix:** Add an inline comment explaining the Kalshi API convention and add a unit test for the inversion logic.

---

### 5.2 kalshi/client.py — Closure-based parse_levels can be inlined

**File:** `coliseum/services/kalshi/client.py:256-259`

`parse_levels()` is a 4-line nested function used in exactly one method (4 call sites, all in the same 15-line block). It adds a function lookup without benefit.

**Fix:** Inline as a list comprehension:

```python
def _levels(data):
    return [OrderBookLevel(price=lvl[0], count=lvl[1]) for lvl in (data or [])]
```

Or inline directly at each call site since the expression is short.

---

### 5.3 telegram/client.py and exa/client.py — Context managers don't clean up resources

**Files:** `coliseum/services/telegram/client.py:59-67`, `coliseum/services/exa/client.py:36-39`

Both async context managers implement `__aexit__` but neither explicitly closes the underlying client/session:

```python
# TelegramClient.__aexit__: checks _bot exists, logs, but does NOT close it
# ExaClient.__aexit__: sets _client = None, but does NOT await cleanup
```

If the underlying libraries have session/socket cleanup, it is silently skipped. This can cause resource leaks in long-running processes.

**Fix:** Check library docs for explicit close/shutdown methods and call them in `__aexit__`.

---

## 6. Dead Code

| Item | File | Line | Reason |
|------|------|------|--------|
| `get_opportunity_markdown_body()` | `files.py` | 351 | Zero call sites in codebase |
| `ModelMessage` import | `trader/main.py` | 12 | Imported, never referenced |
| `Strategy` enum | `config.py` | 77 | Set in config but never read by pipeline |
| `sure_thing_contracts` field | `config.py` | 21 | Set in config, no code reads it |
| Unused Fireworks model enum values | `llm_providers.py` | 37-46 | Audit which are actually referenced |
| `_placeholder_job` | `scheduler.py` | 17 | Only used by unimplemented Guardian News Scan |
| `deps_attr` parameter | `shared_tools.py` | 27 | Always uses default, never overridden |

---

## 7. Implementation Phases

### Phase 1 — Safe fixes, no behavior change (~1-2 hrs)

These are isolated changes with no risk of altering agent behavior.

- [ ] Fix `pipeline.py:39-42` f-string crash bug
- [ ] Extract `_parse_frontmatter()` in `files.py` (remove 4 duplicates)
- [ ] Remove pass-through wrappers in `sync.py`
- [ ] Extract `_init_logfire()` helper in `__main__.py`
- [ ] Remove `get_opportunity_markdown_body()` (unused)
- [ ] Remove `ModelMessage` import in `trader/main.py`
- [ ] Remove `deps_attr` parameter from `shared_tools.py`
- [ ] Merge `register_load_opportunity` and `register_load_opportunity_with_research` into one function
- [ ] Fix `scheduler.py` return type and remove emojis from logger
- [ ] Add diagnostic logging to `find_opportunity_file()`

### Phase 2 — Agent simplification (~3-5 hrs)

These change agent structure but preserve all trading logic.

- [ ] Merge Researcher + Recommender into single Analyst agent
- [ ] Parameterize Scout prompt builder (edge vs sure_thing share base sections)
- [ ] Extract `_ensure_synced_state()` helper in Guardian
- [ ] Consolidate Trader tool registration (`_register_edge_tools` + `_register_sure_thing_tools`)
- [ ] Condense Researcher system prompts via `build_researcher_prompt(strategy)`
- [ ] Decide and implement: Guardian fallback (agent + tools, or remove fallback, or remove agent)

### Phase 3 — Structural improvements (~3-4 hrs)

These require more careful coordination across files.

- [ ] Config YAML merge via `model_fields` introspection (remove hardcoded section list)
- [ ] Move Scout market filtering into `KalshiClient.get_filtered_markets()`
- [ ] Move Scout output validation from prompts into Pydantic model validators
- [ ] Fix `test_pipeline/run.py` monkeypatch — use env var only, no `object.__setattr__`
- [ ] Consolidate `llm_providers.py` provider detection into single lookup map
- [ ] Audit and remove unused model enum values (Fireworks, unused OpenAI models)
- [ ] Inline `AgentFactory` — reduce from 49 to ~15 lines
- [ ] Add unit test for Kalshi orderbook inversion logic

---

## Summary

| Category | Issues Found | Est. LOC Removed |
|---|---|---|
| Critical bugs | 1 | — |
| Core infrastructure | 7 | ~120 |
| Agent architecture | 10 | ~550 |
| Storage layer | 5 | ~80 |
| Services layer | 3 | ~20 |
| Dead code | 7 | ~80 |
| **Total** | **33** | **~850** |
