# Coliseum V2: Comprehensive Product Requirements Document

## Executive Summary

Coliseum is an AI prediction market simulation where autonomous AI agents compete to predict real-world event outcomes. The system operates as a **daily batch pipeline** (not real-time) where agents analyze market snapshots, place paper bets, and are graded after events resolve. The vision is "The ESPN for AI Forecasting" - a spectator experience where users watch AI models compete on prediction markets.

**Core Philosophy**: Pure batch processing, daily digest format, permanent competition with no resets, and focus on prediction accuracy over trading mechanics.

---

## Technical Stack

- **Backend**: Python FastAPI (monolithic application with pipeline pattern)
- **Database**: MongoDB with Motor/Pymongo (fully normalized schema, repository pattern)
- **Task Queue**: Celery + Redis (async pipeline execution, distributed task scheduling)
- **Orchestration**: Celery Beat (daily 09:00 EST market-aligned timing + dynamic settlements)
- **AI/LLM**: OpenRouter (GPT-4, Claude 3.5, Llama, etc.) + Exa AI (research)
- **Data Source**: Kalshi API (any market type, closing within 24 hours)
- **Frontend**: Next.js 16 with shadcn/ui (read-only leaderboard, REST API consumer)
- **Observability**: Pydantic models + Logfire for tracking (automatic LLM call logging)
- **Secrets**: .env files (local dev) + environment variables (production)
- **Infrastructure**: Docker Compose (local), Gunicorn + Uvicorn workers (production)

---

## Architecture Overview

### Pipeline Flow

```
[Kalshi API] → (1) Event Ingestion → (2) Research → (3) Betting → (4) Settlement
      ↓              ↓                    ↓              ↓              ↓
   MongoDB ←─────────┴────────────────────┴──────────────┘              │
                  (Atomic write after Stage 3)                          │
                                                                         │
   MongoDB ←────────────────────────────────────────────────────────────┘
                  (Immediate writes per event in Stage 4)

                        Orchestrated by PipelineRunner
                              ↓
                    In-Memory: DailyPipelineState
                              ↓
              Celery Tasks: Daily Pipeline + Dynamic Settlements
```

**Key Architectural Patterns**:
- ✅ **Sequential Pipeline**: PipelineRunner orchestrates 4 stages with BasePipelineStage interface
- ✅ **In-Memory State**: DailyPipelineState dataclass flows through stages (no DB reads between stages)
- ✅ **Hybrid DB Writes**: Stages 1-3 write atomically at end; Stage 4 writes immediately per event
- ✅ **Celery Task Queue**: Async execution with automatic retries and dynamic scheduling
- ✅ **Repository Pattern**: Clean database abstraction layer for testability
- ✅ **3-Tier Models**: Separate models for database, API, and pipeline (clear separation of concerns)

**Timing**: Daily execution at 09:00 EST (14:00 UTC) via Celery Beat

**Launch Strategy**: Immediate live trading from day 1, no warm-up period

---

## Stage 1: Event Ingestion

### Objective
Select exactly 5 high-quality prediction markets for the day's competition.

### Process

1. **API Scan** (09:00 EST trigger)
   - Fetch approximately 20 active Kalshi events
   - Query events closing within next 24 hours
   - Filter for any market type (no restriction to binary YES/NO markets)

2. **LLM-Based Selection**
   - Feed all ~20 events to an LLM (e.g., GPT-4o or Claude 3.5)
   - Prompt the LLM to select the 5 most interesting events to bet on
   - Selection criteria provided to LLM:
     - Topic diversity (variety across politics, finance, sports, tech, etc.)
     - Market activity and liquidity
     - Clear resolution criteria
      - Events that will likely resolve within 24 hours
     - Controversial or uncertain outcomes (more interesting for predictions)
   - LLM returns 5 event IDs/tickers from the provided list

3. **Price Locking**
   - Record current "Yes" price at time of selection for the 5 chosen events
   - This is the locked price agents will "buy" at
   - Price freeze ensures fair competition (no timing advantage)

4. **Database Write**
   - Create new `daily_batch` document
   - Create 5 `event` documents with locked prices
   - Status: `pending`

### Error Handling
- **Fail-fast**: If Kalshi API is down or returns bad data, skip the day entirely
- If LLM fails to return valid selection, retry once, then fail-fast
- Send alert to admin (email/Slack)
- Do not run subsequent stages without valid event data

---

## Stage 2: Research Phase

### Objective
Generate comprehensive intelligence briefs for each selected event to inform agent decisions.

### Process

1. **Research Agent Activation**
   - For each of the 5 events, instantiate a Research Agent
   - Agent uses Exa AI Answer API (search-grounded LLM)

2. **Intelligence Gathering**
   - **Scope**: Standard analysis (3-5 Exa AI calls, ~15 minutes, ~2000 tokens output)
   - **Sources**: News articles, polls, expert analysis, historical data
   - **Prompt Strategy**: "You are an objective market researcher. Given this prediction market question: [QUESTION] with resolution criteria: [CRITERIA], search for the most recent and credible data points. Do not make a prediction. Output a bulleted list of facts, context, and relevant developments. Focus on information that would help assess the probability of YES vs NO outcomes."

3. **Brief Structure** (standardized format)
   ```
   # Market Question: [Question]
   # Resolution Criteria: [Criteria]
   # Close Time: [Timestamp]
   # Current Price: [Locked Price]

   ## Key Facts
   - [Fact 1]
   - [Fact 2]
   - [...]

   ## Recent Developments
   - [Development 1]
   - [Development 2]

   ## Historical Context
   - [Context 1]
   - [Context 2]

   ## Consensus/Expert Views
   - [View 1]
   - [View 2]
   ```

4. **Database Update**
   - Write intelligence brief to `events.intelligence_brief` field
   - Each event now has locked price + comprehensive research

### Cost Estimation
- 5 events × 4 Exa AI calls × $0.005/call = $0.10 per day
- ~$6/month for research phase

---

## Stage 3: Betting Session

### Objective
Eight AI agents analyze briefs and place bets, competing to maximize bankroll.

### Agent Configuration

**Models** (8 total, database as source of truth):
1. GPT-4o (green)
2. Claude 3.5 (orange)
3. Grok-2 (blue)
4. Gemini Pro (purple)
5. Llama 3.1 (red)
6. Mistral Large (cyan)
7. DeepSeek V2 (yellow)
8. Qwen Max (pink)

**Starting Bankroll**: $100,000 per agent

**Bankroll Management**:
- Permanent competition (never reset)
- Agents can go broke (bankroll → $0) but remain in system
- No elastic floor or subsidies

**Persona System**:
- **Dynamic rotation**: Personas change weekly
- **Storage**: Git-versioned YAML config files in repo
- **Examples**:
  - Week 1: "Conservative value investor" (bet only on high-confidence, low-risk)
  - Week 2: "Aggressive contrarian" (bet against consensus)
  - Week 3: "Momentum trader" (follow recent market trends)
  - Week 4: "Data-driven analyst" (only technical fundamentals)
- Each model uses the same persona in a given week (test model capabilities, not strategies)
- Persona prompt templates include:
  - Risk tolerance
  - Decision framework
  - Confidence calibration
  - Position sizing philosophy

### Betting Process

1. **Context Loading** (per agent)
   - Current bankroll
   - Last 5 trades (event, decision, outcome, PnL)
   - Performance summary (win rate, total PnL, current rank)

2. **Decision Making** (per event)
   - **Input**: Full intelligence brief (2000 tokens) + agent context + locked price
   - **System Prompt**:
   ```
   You are [Agent Name] ([Model]), a competitive prediction market trader.
   This week, you are embodying the persona: [Persona Name]
   [Persona Description]

   Current Bankroll: $[X]
   Recent Performance: [Last 5 outcomes]

   You are analyzing the following prediction market:
   [Intelligence Brief]

   The current locked price for YES is [Price] (meaning NO is [1-Price]).

   Based on your persona and the research provided, decide:
   1. BET YES / BET NO / ABSTAIN
   2. If betting, how much to wager (max 10% of bankroll per event)

   Provide your reasoning and decision in JSON format:
   {
     "decision": "YES" | "NO" | "ABSTAIN",
     "amount": <dollar amount>,
     "confidence": <0-100>,
     "reasoning": "<your analysis>"
   }
   ```

   - **Temperature**: 0.7 (allow some creativity in reasoning)
   - **Timeout**: 5 minutes per agent decision
   - **Execution**: Synchronous (wait for all 8 agents before proceeding)

3. **Risk Management**
   - Per-event limit: Max 10% of current bankroll
   - No portfolio-level cap (agent could theoretically bet on all 5 events)
   - Abstention is neutral (no penalty, no impact on stats)

4. **Bet Recording**
   - Write each decision to `bets` collection
   - Status: `pending`
   - Provisionally debit bankroll (not final until settlement)
   - Store full `reasoning_trace` for transparency

5. **Error Handling**
   - If agent fails to respond within 5min → automatic ABSTAIN
   - Failed agents logged but don't block other agents

### Cost Estimation
- 8 agents × 5 events = 40 LLM calls per day
- Average 3000 tokens input (brief + context) × 500 tokens output
- GPT-4o: ~$0.03/call → $1.20/day
- Claude Opus: ~$0.06/call → varies by agent mix
- **Estimated**: $1.50-$2.00/day = $50-60/month for betting phase

---

## Stage 4: Settlement

### Objective
Finalize bet outcomes and update agent bankrolls after events resolve.

### Process

1. **Trigger**
   - Scheduled 2 hours after each event's close time
   - Separate job per event (staggered settlements)

2. **Outcome Fetching**
   - Query Kalshi API: `GET /events/{ticker}/outcome`
   - Possible results: `YES`, `NO`, `VOID`
   - Retry logic: 3 attempts with exponential backoff

3. **Payout Calculation** (Hybrid model with fees)

   **For Winning Bets**:
   ```python
   gross_payout = bet_amount / locked_price
   profit = gross_payout - bet_amount
   fee = gross_payout * 0.07  # Kalshi typical fee
   net_payout = gross_payout - fee
   pnl = net_payout - bet_amount
   ```

   **For Losing Bets**:
   ```python
   pnl = -bet_amount
   ```

   **For VOID Events**:
   ```python
   pnl = 0  # Full refund, return original bet_amount
   ```

   **Abstention**:
   ```python
   pnl = 0  # No money at risk
   ```

4. **Database Updates**
   - Update `bets` collection:
     - Set `status: "settled"`
     - Set `pnl: <calculated value>`
   - Update `agents` collection:
     - Increment `current_bankroll` by PnL
     - Append to `history` array:
       ```json
       {
         "event_id": "...",
         "decision": "YES",
         "amount": 1000,
         "pnl": 122.22,
         "result": "WIN",
         "timestamp": "2024-01-07T22:00:00Z"
       }
       ```
   - Update `events` collection:
     - Set `status: "settled"`
     - Set `outcome: "YES" | "NO" | "VOID"`

5. **History Maintenance**
   - Keep full history forever (infinite retention)
   - Agent `history` array grows unbounded
   - For agent context window, only load last 5 trades

---

## MongoDB Schema (Normalized)

### Collection: `daily_batches`

Stores the daily simulation run context.

```json
{
  "_id": ObjectId,
  "date": "2024-01-07",
  "trigger_time": "2024-01-07T14:00:00Z",  // 09:00 EST = 14:00 UTC
  "status": "pending" | "processing" | "completed" | "failed",
  "event_ids": [ObjectId, ObjectId, ...],  // References to 5 events
  "created_at": ISODate,
  "completed_at": ISODate | null
}
```

**Indexes**:
- `date` (unique)
- `status`

---

### Collection: `events`

Stores individual market data and research.

```json
{
  "_id": ObjectId,
  "batch_id": ObjectId,  // Reference to daily_batches
  "kalshi_ticker": "FED-RATE-JAN",
  "title": "Will the Fed cut rates in January?",
  "question": "Full question text...",
  "resolution_criteria": "Resolves YES if...",
  "category": "finance",  // LLM-classified
  "kalshi_category": "Economics",  // Original Kalshi category

  "locked_price": 0.45,  // YES price at time of selection
  "locked_at": ISODate,

  "close_time": ISODate,
  "expected_resolution_time": ISODate,  // close_time + 2 hours

  "status": "open" | "waiting_settlement" | "settled",
  "outcome": null | "YES" | "NO" | "VOID",
  "settled_at": ISODate | null,

  "intelligence_brief": "# Key Facts\n- ...",  // Full research text
  "research_completed_at": ISODate,

  "created_at": ISODate
}
```

**Indexes**:
- `batch_id`
- `kalshi_ticker` (unique)
- `status`
- `close_time`
- `category`

---

### Collection: `agents`

Competitor AI models.

```json
{
  "_id": ObjectId,
  "name": "Claude-Opus",
  "model_slug": "anthropic/claude-3-opus",  // OpenRouter format
  "display_color": "#ff6b35",
  "display_color_text": "#ffffff",
  "avatar_initials": "CO",

  "current_bankroll": 105234.50,
  "starting_bankroll": 100000.00,
  "total_pnl": 5234.50,

  "stats": {
    "total_bets": 150,
    "wins": 85,
    "losses": 55,
    "abstentions": 10,
    "win_rate": 0.607,
    "avg_bet_size": 4500.00,
    "largest_win": 12000.00,
    "largest_loss": -8000.00
  },

  "history": [
    {
      "event_id": ObjectId,
      "decision": "YES",
      "amount": 5000.00,
      "pnl": 1234.56,
      "result": "WIN",
      "timestamp": ISODate
    },
    // ... (grows forever)
  ],

  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes**:
- `model_slug` (unique)
- `current_bankroll` (for leaderboard sorting)

**Note**: Frontend queries this collection for leaderboard data (on-demand calculation).

---

### Collection: `bets`

Ledger of all betting actions.

```json
{
  "_id": ObjectId,
  "batch_id": ObjectId,
  "agent_id": ObjectId,
  "event_id": ObjectId,

  "decision": "YES" | "NO" | "ABSTAIN",
  "amount_wagered": 5000.00,
  "locked_price_at_bet": 0.45,

  "reasoning_trace": "I am betting YES because inflation data suggests...",
  "confidence": 75,  // 0-100 scale

  "status": "pending" | "settled",
  "pnl": null | 1234.56,  // Calculated during settlement
  "outcome": null | "WIN" | "LOSS" | "VOID" | "ABSTAIN",

  "created_at": ISODate,
  "settled_at": ISODate | null
}
```

**Indexes**:
- `batch_id`
- `agent_id`
- `event_id`
- `status`
- Compound: `(agent_id, created_at)` for history queries

---

### Collection: `personas`

Weekly persona configurations (metadata only; actual prompts in Git).

```json
{
  "_id": ObjectId,
  "week_number": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "persona_name": "Conservative Value Investor",
  "config_file": "personas/conservative_value.yaml",  // Git reference
  "description": "Bets only on high-confidence, low-risk opportunities...",
  "active": true,
  "created_at": ISODate
}
```

**Indexes**:
- `week_number` (unique)
- `active`

---

## Pipeline Architecture Deep Dive

### Data Flow Through Pipeline

**1. Pipeline Initialization** (09:00 EST daily):
```python
# Celery Beat triggers task
run_daily_pipeline_task.apply_async(args=[today_date])

# Task creates pipeline and state
runner = create_daily_pipeline()  # Factory pattern
state = DailyPipelineState(
    batch_id=generate_batch_id(),
    execution_date=today_date,
    trigger_time=datetime.now()
)
```

**2. Stage Execution** (in-memory processing):
```python
# PipelineRunner executes stages sequentially
for stage in [IngestionStage, ResearchStage, BettingStage]:
    result = await stage.execute(state, progress_callback)
    # Each stage reads from state and writes to state
    # No database operations during execution
    if not result.success:
        raise StageExecutionError(...)

# All data accumulated in memory
state.selected_events = [...]        # From IngestionStage
state.intelligence_briefs = {...}    # From ResearchStage
state.agent_decisions = [...]        # From BettingStage
```

**3. Atomic Database Write** (after Stage 3):
```python
# Single transaction writes all data
async with await mongo_client.start_session() as session:
    async with session.start_transaction():
        # Write batch
        batch_repo.create(state.to_batch_document())

        # Write events (5)
        event_repo.create_many(state.to_event_documents())

        # Write bets (up to 40)
        bet_repo.create_many(state.to_bet_documents())

        # Commit atomically
```

**4. Dynamic Settlement Scheduling** (per event):
```python
# After pipeline completes, schedule settlements
for event in state.selected_events:
    settle_time = event.close_time + timedelta(hours=2)
    settle_event_task.apply_async(
        args=[event.id],
        eta=settle_time  # Celery dynamic scheduling
    )
```

**5. Settlement Execution** (independent per event):
```python
# Separate task per event, triggered 2 hours after close
settle_event_task(event_id):
    # Fetch outcome from Kalshi
    outcome = kalshi_client.get_outcome(event_id)

    # Calculate payouts for all bets
    for bet in bets_for_event(event_id):
        pnl = calculate_payout(bet, outcome)

        # Immediate database write (not batched)
        bet_repo.update(bet.id, {"pnl": pnl, "status": "settled"})
        agent_repo.increment_bankroll(bet.agent_id, pnl)

    event_repo.update(event_id, {"outcome": outcome, "status": "settled"})
```

### Stage Interface Contract

All stages implement `BasePipelineStage`:

```python
from abc import ABC, abstractmethod

class BasePipelineStage(ABC):
    stage_name: str  # For logging

    async def execute(
        self,
        pipeline_state: DailyPipelineState,
        progress_callback: Optional[Callable] = None
    ) -> StageResult:
        """
        Execute this pipeline stage.

        Contract:
        - Read inputs from pipeline_state
        - Perform business logic (API calls, LLM calls, calculations)
        - Write outputs to pipeline_state
        - Return StageResult with success/failure
        - Do NOT write to database (except Stage 4 settlement)
        """
        start_time = time.time()

        try:
            # Call subclass implementation
            await self._execute_stage(pipeline_state, progress_callback)

            # Record timing
            pipeline_state.stage_timings[self.stage_name] = time.time() - start_time

            # Log success
            logfire.info(f"{self.stage_name} completed", **self._get_log_data(pipeline_state))

            return StageResult(success=True, stage_name=self.stage_name)

        except Exception as e:
            # Record error
            pipeline_state.errors.append(f"{self.stage_name}: {str(e)}")

            # Log failure
            logfire.error(f"{self.stage_name} failed", error=str(e), **self._get_log_data(pipeline_state))

            # Determine if retryable
            if isinstance(e, ExternalAPIError):
                raise  # Celery will retry
            else:
                raise StageExecutionError(self.stage_name, str(e))

    @abstractmethod
    async def _execute_stage(
        self,
        pipeline_state: DailyPipelineState,
        progress_callback: Optional[Callable]
    ) -> None:
        """Subclass implements actual stage logic"""
        pass
```

### Error Handling Flow

**Retryable Errors** (Celery auto-retry):
```python
class ExternalAPIError(PipelineExecutionError):
    retryable = True

# In Celery task
@celery_app.task(bind=True, max_retries=3, autoretry_for=(ExternalAPIError,))
def run_daily_pipeline_task(self, execution_date: str):
    # If Kalshi/OpenRouter/Exa AI fails, Celery retries
    # Exponential backoff: 1min, 2min, 4min
```

**Non-Retryable Errors** (fail fast):
```python
class ValidationError(PipelineExecutionError):
    retryable = False

# Invalid data format, bad configuration, etc.
# Log to Logfire, alert admin, mark batch as failed
```

**Partial Failures** (continue with warnings):
```python
# Example: ArXiv research fails for 1 event
# Stage continues, records warning in state.errors
# Pipeline completes successfully
# Frontend shows "Research partially failed" badge
```

### Testing Strategy with Pipeline Pattern

**Unit Tests** (mock repositories):
```python
# Test IngestionStage in isolation
async def test_ingestion_stage():
    # Arrange
    mock_kalshi = MockKalshiClient(return_events=[...])
    stage = IngestionStage(kalshi_client=mock_kalshi)
    state = DailyPipelineState(...)

    # Act
    result = await stage.execute(state)

    # Assert
    assert result.success
    assert len(state.selected_events) == 5
    assert state.ingestion_metadata["events_scanned"] > 0
```

**Integration Tests** (real MongoDB):
```python
# Test full pipeline with Docker MongoDB
async def test_full_pipeline_e2e():
    runner = create_daily_pipeline()
    state = DailyPipelineState(...)

    batch_id = await runner.run_daily_pipeline(state)

    # Verify database state
    assert await batch_repo.find_by_id(batch_id) is not None
    assert await event_repo.count_by_batch(batch_id) == 5
```

---

## Persona System (Git-Versioned)

### File Structure

```
backend/
  personas/
    conservative_value.yaml
    aggressive_contrarian.yaml
    momentum_trader.yaml
    data_driven_analyst.yaml
    ...
```

### Example Persona File: `conservative_value.yaml`

```yaml
name: "Conservative Value Investor"
description: "Bets only on high-confidence, low-risk opportunities with strong fundamentals"
version: "1.0"

risk_tolerance: "low"
confidence_threshold: 75  # Only bet if confidence > 75%
max_bet_percentage: 5  # Conservative sizing (max 5% of bankroll)

decision_framework: |
  You are a conservative value investor. Your approach:
  1. Only bet when you have strong conviction (>75% confidence)
  2. Prefer events with clear, objective resolution criteria
  3. Favor markets with high liquidity and established precedents
  4. Avoid speculative or highly uncertain events
  5. Size positions conservatively (max 5% of bankroll)
  6. Abstain when information is insufficient or contradictory

evaluation_criteria:
  - "Clarity of resolution criteria"
  - "Quality and recency of data"
  - "Historical precedent"
  - "Expert consensus"

prompt_template: |
  You are a conservative value investor in prediction markets.
  Your goal is long-term, steady growth through high-probability bets.

  Risk Tolerance: Low
  Confidence Threshold: >75% to bet
  Max Position Size: 5% of bankroll

  Evaluate this market through the lens of:
  - Is the resolution criteria clear and objective?
  - Is there sufficient high-quality data to form a strong view?
  - Are there historical precedents to guide the prediction?
  - What is the expert consensus?

  ABSTAIN if you lack high confidence. Preservation of capital is paramount.
```

### Rotation Schedule

- **Personas rotate weekly** (Monday 00:00 EST)
- Backend checks current week number and loads corresponding persona config
- All 8 agents use the same persona in a given week
- Frontend displays current persona prominently ("This Week: Conservative Value Investor")

---

## FastAPI Backend Structure

### Monolithic Application with Pipeline Pattern

The backend follows a **sequential pipeline architecture** with clear orchestration, in-memory state management, and async task execution via Celery.

```
backend/
  main.py                          # FastAPI app entry point
  config.py                        # Pydantic Settings (environment variables)
  celery_config.py                 # Celery app + Beat schedule

  models/                          # 3-tier model separation
    database/                      # MongoDB ODM models
      agent.py                     # Agent schema + indexes
      event.py                     # Event schema
      bet.py                       # Bet ledger
      daily_batch.py               # Batch metadata
      persona.py                   # Persona config metadata
    api/                           # FastAPI Pydantic models
      leaderboard.py               # LeaderboardResponse
      events.py                    # EventResponse, EventDetailResponse
      agents.py                    # AgentProfileResponse
    pipeline/                      # Pipeline stage models
      state.py                     # DailyPipelineState dataclass
      decisions.py                 # BetDecision, EventData
      results.py                   # StageResult, StageStatus enums
      intelligence.py              # IntelligenceBrief model

  database/                        # MongoDB connection + repositories
    connection.py                  # Motor client initialization
    indexes.py                     # Index creation on startup
    repositories/                  # Repository pattern
      base.py                      # BaseRepository with CRUD
      agents.py                    # AgentRepository
      events.py                    # EventRepository
      bets.py                      # BetRepository
      batches.py                   # DailyBatchRepository

  pipeline/                        # Pipeline stages + orchestration
    core/                          # Infrastructure
      runner.py                    # PipelineRunner orchestrator
      base_stage.py                # BasePipelineStage abstract class
      exceptions.py                # Custom exception hierarchy
    stages/                        # Individual pipeline stages (4)
      ingestion/
        main.py                    # IngestionStage class
        kalshi_client.py           # Kalshi API wrapper
        llm_selector.py            # LLM-based event selection
      research/
        main.py                    # ResearchStage class
        exa_client.py              # Exa AI API wrapper
        brief_generator.py         # Intelligence brief creation
        prompts.py                 # Research prompts
      betting/
        main.py                    # BettingStage class
        openrouter_client.py       # OpenRouter API wrapper
        agent_runner.py            # Parallel agent execution
        context_loader.py          # Load agent history + bankroll
        prompts.py                 # Persona-based betting prompts
        validators.py              # Bet size validation, JSON parsing
      settlement/
        main.py                    # SettlementStage class
        outcome_fetcher.py         # Kalshi outcome API
        payout_calculator.py       # PnL calculation with fees
        bankroll_updater.py        # Agent bankroll updates
    __init__.py                    # Factory: create_daily_pipeline()

  tasks/                           # Celery task definitions
    pipeline_tasks.py              # run_daily_pipeline_task
    settlement_tasks.py            # settle_event_task (dynamic scheduling)

  api/                             # FastAPI REST endpoints
    routes/
      leaderboard.py               # GET /api/leaderboard
      events.py                    # GET /api/events, /api/events/{id}
      agents.py                    # GET /api/agents/{id}
      batches.py                   # GET /api/batches
    dependencies.py                # Dependency injection (DB, auth)

  services/                        # Business logic services
    persona_manager.py             # Load persona configs from YAML
    leaderboard_calculator.py      # On-demand leaderboard computation
    metrics_tracker.py             # Cost tracking, performance metrics

  personas/                        # Git-versioned persona configs
    conservative_value.yaml
    aggressive_contrarian.yaml
    ...

  utils/                           # Utilities
    logging.py                     # Logfire integration
    errors.py                      # Error formatting
    time_utils.py                  # Timezone conversions (EST/UTC)

  tests/                           # Test suite
    unit/                          # Unit tests for stages
      test_ingestion.py
      test_research.py
      test_betting.py
      test_settlement.py
    integration/                   # Integration tests
      test_pipeline_e2e.py
      test_repositories.py
    fixtures/                      # Test data
      mock_events.json
      mock_personas.yaml
```

### Pipeline Orchestration Pattern

**Core Components**:

1. **PipelineRunner** (`pipeline/core/runner.py`): Orchestrates sequential execution
   ```python
   class PipelineRunner:
       async def run_daily_pipeline(
           self,
           pipeline_state: DailyPipelineState,
           progress_callback: Optional[Callable] = None
       ) -> str:  # Returns batch_id
           for stage in self.stages:
               result = await stage.execute(pipeline_state, progress_callback)
               if not result.success:
                   raise StageExecutionError(...)
           return pipeline_state.batch_id
   ```

2. **BasePipelineStage** (`pipeline/core/base_stage.py`): Abstract base for all stages
   - Enforces consistent interface across stages
   - Automatic logging and timing
   - Error handling wrapper

3. **DailyPipelineState** (`models/pipeline/state.py`): In-memory state object
   ```python
   @dataclass
   class DailyPipelineState:
       # Pipeline metadata
       batch_id: str
       execution_date: date
       trigger_time: datetime

       # Stage 1 outputs (Ingestion)
       selected_events: List[EventData] = field(default_factory=list)
       ingestion_metadata: Dict[str, Any] = field(default_factory=dict)

       # Stage 2 outputs (Research)
       intelligence_briefs: Dict[str, str] = field(default_factory=dict)
       research_metadata: Dict[str, Any] = field(default_factory=dict)

       # Stage 3 outputs (Betting)
       agent_decisions: List[BetDecision] = field(default_factory=list)
       betting_metadata: Dict[str, Any] = field(default_factory=dict)

       # Tracking
       stage_timings: Dict[str, float] = field(default_factory=dict)
       errors: List[str] = field(default_factory=list)
   ```

**Benefits**:
- Single source of truth for execution order
- All intermediate state in memory (faster, cleaner)
- Atomic database write at pipeline completion
- Easy to test stages in isolation
- Clear data flow visualization

### Exception Hierarchy

Custom exceptions with retry logic (`pipeline/core/exceptions.py`):

```python
class PipelineExecutionError(Exception):
    """Base exception for all pipeline errors"""
    retryable: bool = False

class StageExecutionError(PipelineExecutionError):
    """Fatal stage failure"""
    retryable = False

class ExternalAPIError(PipelineExecutionError):
    """Kalshi/OpenRouter/Exa AI API error"""
    retryable = True  # Can retry with backoff

class ValidationError(PipelineExecutionError):
    """Data validation failed"""
    retryable = False
```

### Repository Pattern

Clean database abstraction (`database/repositories/`):

```python
class BaseRepository:
    async def create(self, document: Dict) -> str: ...
    async def find_by_id(self, id: str) -> Optional[Dict]: ...
    async def update(self, id: str, updates: Dict) -> bool: ...

class EventRepository(BaseRepository):
    async def create_events_for_batch(
        self, batch_id: str, events: List[EventData]
    ) -> List[str]:
        """Batch insert with MongoDB transaction"""
```

**Benefits**:
- Testable with mock repositories
- Centralized query logic
- Transaction management in one place

### Celery Task Queue Integration

**Celery Configuration** (`celery_config.py`):
```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery('coliseum', broker='redis://localhost:6379/0')

celery_app.conf.beat_schedule = {
    'daily-pipeline-09am-est': {
        'task': 'tasks.pipeline_tasks.run_daily_pipeline_task',
        'schedule': crontab(hour=14, minute=0),  # 09:00 EST = 14:00 UTC
    },
}
```

**Task Definitions** (`tasks/pipeline_tasks.py`):
```python
@celery_app.task(bind=True, max_retries=3)
def run_daily_pipeline_task(self, execution_date: str):
    """Daily 09:00 EST pipeline execution"""
    runner = create_daily_pipeline()
    state = DailyPipelineState(execution_date=execution_date)

    batch_id = await runner.run_daily_pipeline(state)
    schedule_settlement_tasks(batch_id)  # Dynamic scheduling
    return batch_id

@celery_app.task(bind=True, max_retries=5)
def settle_event_task(self, event_id: str):
    """Triggered 2 hours after event close_time"""
    stage = SettlementStage()
    result = await stage.settle_event(event_id)
    return result
```

**Benefits**:
- Reliable distributed execution
- Automatic retry with exponential backoff
- Progress tracking via Celery state
- Dynamic settlement scheduling (no fixed cron jobs needed)

### Hybrid Database Write Strategy

**Daily Pipeline (Stages 1-3)**: Write atomically at end
- Keep all state in memory during execution
- Single transaction at pipeline completion
- Writes: `daily_batch`, `events` (5), `bets` (up to 40)
- Benefits: Fast execution, atomic consistency, easy rollback

**Settlement (Stage 4)**: Write immediately per event
- Independent settlement tasks per event
- Immediate write on outcome fetch
- Updates: `bets.pnl`, `bets.status`, `agents.current_bankroll`, `events.outcome`
- Benefits: No data loss if process crashes, real-time updates

### Deployment

- **Development**: `uvicorn main:app --reload`
- **Production**:
  - FastAPI: Gunicorn + Uvicorn workers
  - Celery Worker: `celery -A celery_config worker --loglevel=info`
  - Celery Beat: `celery -A celery_config beat --loglevel=info`
  - Redis: Task queue backend
- **Pipeline Orchestration**: Celery Beat (not cron)
  - Daily job: 09:00 EST (14:00 UTC) → triggers `run_daily_pipeline_task`
  - Settlement jobs: Dynamically scheduled 2 hours after each event close_time
- **Infrastructure**: Docker Compose recommended for local development
  - FastAPI container
  - Celery worker container
  - Celery beat container
  - Redis container
  - MongoDB (Atlas for production)

---

## REST API Specification

### Authentication

- **MVP**: No authentication (read-only public leaderboard)
- **Future**: API keys for write operations, user accounts

### Endpoints

#### GET `/api/leaderboard`

Returns current agent rankings (on-demand calculation).

**Response**:
```json
{
  "updated_at": "2024-01-07T15:30:00Z",
  "agents": [
    {
      "id": "agent_id",
      "name": "Claude-Opus",
      "model_slug": "anthropic/claude-3-opus",
      "rank": 1,
      "current_bankroll": 125000.00,
      "total_pnl": 25000.00,
      "pnl_percent": 25.0,
      "stats": {
        "total_bets": 150,
        "wins": 90,
        "losses": 50,
        "abstentions": 10,
        "win_rate": 0.643
      },
      "display_color": "#ff6b35"
    },
    // ... 7 more agents
  ]
}
```

**Calculation**:
- Query all agents from DB
- Sort by `current_bankroll` (descending)
- Calculate derived stats on-the-fly

---

#### GET `/api/events`

Returns recent events (paginated).

**Query Params**:
- `limit` (default: 20)
- `offset` (default: 0)
- `status` (filter: `open`, `settled`)
- `category` (filter: `politics`, `finance`, etc.)

**Response**:
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "events": [
    {
      "id": "event_id",
      "title": "Will the Fed cut rates in January?",
      "question": "Full question...",
      "category": "finance",
      "locked_price": 0.45,
      "close_time": "2024-01-07T20:00:00Z",
      "status": "settled",
      "outcome": "YES",
      "bet_count": 8,
      "total_wagered": 32000.00
    },
    // ... more events
  ]
}
```

---

#### GET `/api/events/{event_id}`

Returns detailed event data including intelligence brief and bets.

**Response**:
```json
{
  "id": "event_id",
  "title": "Will the Fed cut rates in January?",
  "question": "Full question text...",
  "resolution_criteria": "Resolves YES if...",
  "category": "finance",
  "locked_price": 0.45,
  "close_time": "2024-01-07T20:00:00Z",
  "status": "settled",
  "outcome": "YES",
  "intelligence_brief": "# Key Facts\n- ...",
  "bets": [
    {
      "agent_name": "Claude-Opus",
      "decision": "YES",
      "amount": 5000.00,
      "confidence": 80,
      "reasoning": "Based on recent inflation data...",
      "pnl": 1234.56,
      "outcome": "WIN"
    },
    // ... 7 more bets (or fewer if abstentions)
  ]
}
```

---

#### GET `/api/agents/{agent_id}`

Returns detailed agent profile with historical performance.

**Response**:
```json
{
  "id": "agent_id",
  "name": "Claude-Opus",
  "model_slug": "anthropic/claude-3-opus",
  "current_bankroll": 125000.00,
  "total_pnl": 25000.00,
  "stats": {
    "total_bets": 150,
    "wins": 90,
    "losses": 50,
    "abstentions": 10,
    "win_rate": 0.643,
    "avg_bet_size": 4800.00,
    "largest_win": 15000.00,
    "largest_loss": -8000.00,
    "best_category": "politics",
    "worst_category": "sports"
  },
  "recent_performance": [
    {
      "event_title": "Will the Fed cut rates?",
      "decision": "YES",
      "amount": 5000.00,
      "pnl": 1234.56,
      "outcome": "WIN",
      "date": "2024-01-07"
    },
    // ... last 10 bets
  ],
  "bankroll_history": [
    {"date": "2024-01-01", "bankroll": 100000.00},
    {"date": "2024-01-02", "bankroll": 102000.00},
    // ... daily snapshots
  ]
}
```

---

#### GET `/api/batches`

Returns daily batch history.

**Response**:
```json
{
  "batches": [
    {
      "id": "batch_id",
      "date": "2024-01-07",
      "status": "completed",
      "event_count": 5,
      "total_bets": 40,
      "total_wagered": 160000.00,
      "events": [
        {"id": "...", "title": "...", "category": "politics"},
        // ... 4 more
      ]
    },
    // ... more batches
  ]
}
```

---

## Observability & Monitoring (Pydantic + Logfire)

### Logging Strategy

All pipeline stages emit structured logs via Pydantic models and Logfire.

**Example: Ingestion Stage Log**

```python
from pydantic import BaseModel
import logfire

class IngestionLog(BaseModel):
    stage: str = "ingestion"
    timestamp: datetime
    events_scanned: int
    events_selected: int
    selected_event_ids: list[str]
    quota_breakdown: dict  # {"politics": 2, "finance": 1, ...}
    duration_seconds: float
    status: str  # "success" | "failed"
    error: str | None = None

# Usage
log = IngestionLog(
    timestamp=datetime.now(),
    events_scanned=120,
    events_selected=5,
    selected_event_ids=[...],
    quota_breakdown={"politics": 2, "finance": 1, "sports": 1, "wildcard": 1},
    duration_seconds=45.2,
    status="success"
)
logfire.info("Ingestion completed", **log.dict())
```

**Key Metrics to Track**:

1. **Pipeline Metrics**:
   - Stage execution time (ingestion, research, betting, settlement)
   - Success/failure rates per stage
   - Total pipeline duration

2. **Agent Decision Metrics**:
   - LLM call latency per agent
   - Timeout occurrences
   - Decision distribution (YES/NO/ABSTAIN breakdown)
   - Average confidence scores

3. **Cost Tracking**:
   - API call costs per stage
   - Daily/monthly spend by service (Kalshi, OpenRouter, Exa AI)
   - Cost per agent per event

4. **Alert Conditions**:
   - Pipeline failure (any stage fails)
   - Kalshi API errors
   - Agent timeout rate >20%
   - Daily spend exceeds budget threshold

---

## Cost Projections

### Daily Costs

| Component | Usage | Unit Cost | Daily Cost |
|-----------|-------|-----------|------------|
| **Kalshi API** | 20-30 calls/day | Free tier | $0.00 |
| **Event Selection (LLM)** | 1 call/day | $0.02/call | $0.02 |
| **Exa AI Research** | 5 events × 4 calls | $0.005/call | $0.10 |
| **Agent Decisions (GPT-4)** | 40 calls × $0.03 | $0.03/call | $1.20 |
| **Agent Decisions (Claude)** | Mix of models | ~$0.04/call | $0.60 |
| **MongoDB Atlas** | 1GB storage | Shared tier | $0.00 |
| **Logfire** | 10k events/day | Free tier | $0.00 |
| **Total** | | | **~$2.00/day** |

### Monthly Projection
- **$60/month** for core operations
- **+$10/month** buffer for spikes
- **Total: ~$70/month** for MVP

### Scaling Considerations
- If expanding to 10 events/day: ~$150/month
- If adding user paper trading: +$20-50/month (depends on users)
- Production MongoDB: +$25/month (M10 cluster)

---

## Error Handling & Failure Recovery

### Failure Modes & Responses

| Failure | Detection | Response | Recovery |
|---------|-----------|----------|----------|
| **Kalshi API down** | HTTP timeout/500 | Fail-fast, skip day, alert admin | Manual retry next day |
| **Agent timeout** | 5min timeout | Auto-ABSTAIN for that agent | Continue with other agents |
| **MongoDB connection** | Connection error | Retry 3x, then fail-fast | Alert admin, manual restart |
| **Exa AI rate limit** | 429 response | Exponential backoff | Retry up to 3x |
| **Settlement fetch fails** | API error | Retry every hour (max 24hr) | Mark event as "delayed" |
| **LLM returns invalid JSON** | Pydantic validation | Log error, auto-ABSTAIN | Continue pipeline |

### Idempotency

- **Ingestion**: Check if `daily_batch` for date exists before creating
- **Research**: Check if `event.intelligence_brief` exists before running
- **Betting**: Check if `bet` record exists for `(agent_id, event_id, batch_id)` combo
- **Settlement**: Check if `bet.status == "settled"` before recalculating

### Checkpointing

Pipeline stages are independent and stateful:
- Each stage writes to DB before proceeding
- Can manually re-run individual stages if needed
- Example: If research fails on 1 event, can retry just that event

---

## Testing Strategy

### Incremental Testing Approach

**User's approach**: "Will spend the credits needed. Test one step at a time."

**Recommended Test Sequence**:

1. **Stage 1: Ingestion** (Week 1)
   - Call Kalshi API in read-only mode
   - Verify event selection logic (quotas, scoring)
   - Confirm 5 events selected daily
   - **Cost**: Minimal (free API calls)

2. **Stage 2: Research** (Week 1-2)
   - Run research on 1 event manually
   - Verify Exa AI integration
   - Check intelligence brief quality/format
   - **Cost**: ~$0.05 per test event

3. **Stage 3: Betting** (Week 2)
   - Run 1-2 agents on 1 event with research
   - Test prompt → JSON response parsing
   - Verify decision logic (bet sizing, abstention)
   - **Cost**: ~$0.25 per test run (2 agents × 1 event)

4. **Stage 4: Settlement** (Week 2)
   - Mock a settled event (use historical Kalshi data)
   - Test payout calculation with known outcomes
   - Verify bankroll updates
   - **Cost**: Free (no external APIs)

5. **End-to-End Pipeline** (Week 3)
   - Run full pipeline on 1-2 events with 3-4 agents
   - Monitor logs, timing, costs
   - **Cost**: ~$1.50 per test day

6. **Full Production** (Week 3-4)
   - Scale to 5 events, 8 agents
   - Monitor for 3-5 days before announcing publicly
   - **Cost**: $2/day as projected

**Total Testing Budget**: ~$50-75 before full launch

### Test Data

- **Historical Kalshi events**: Use past events with known outcomes for settlement testing
- **Mocked intelligence briefs**: Pre-written briefs for agent testing
- **Seed database**: Pre-populate `agents` collection with starting bankrolls

---

## Frontend Integration

### Current Frontend State
- Next.js 16 with shadcn/ui
- Hardcoded 8 agents with colors/avatars
- Mock event data
- Read-only leaderboard focus

### Backend Integration Points

1. **Agent Data Sync**
   - Frontend should fetch agent list from `GET /api/leaderboard` on page load
   - Use backend as source of truth for colors, names, slugs
   - Remove hardcoded agent arrays

2. **Leaderboard Update**
   - Poll `GET /api/leaderboard` every 30 seconds (during pipeline hours)
   - Poll every 5 minutes (off-hours)
   - Display live rankings, bankrolls, stats

3. **Event History**
   - Fetch recent batches from `GET /api/batches`
   - Show daily event cards with outcomes
   - Link to detailed event pages (`GET /api/events/{id}`)

4. **Agent Profiles**
   - Click agent → navigate to `GET /api/agents/{id}`
   - Show bankroll chart, recent bets, performance breakdown

5. **Current Persona Display**
   - Fetch current week's persona from backend metadata endpoint
   - Display prominently: "This Week: [Persona Name]"
   - Show persona description in info modal

### Frontend Enhancements (Future)

- **Live Pipeline Status**: Show which stage is currently running
- **Bet Reasoning Modal**: Click bet → see full agent reasoning trace
- **Category Filters**: Filter events by politics/finance/sports
- **Performance Charts**: Historical bankroll line charts (use Chart.js/Recharts)

---

## Open Questions & Future Enhancements

### Near-Term (Post-MVP)

1. **User Paper Trading**
   - Allow users to bet alongside agents with fake money
   - Separate leaderboard for humans vs AI
   - Requires: User accounts, bet submission UI, separate `user_bets` collection

2. **Notifications**
   - Email digest after daily pipeline completes
   - Slack/Discord bot with daily results
   - "Agent X just made a huge bet!" alerts

3. **Agent Prompt Iteration**
   - A/B test different persona prompts
   - Track which prompts lead to better performance
   - Community-submitted persona challenges

4. **Multi-Day Events**
   - Support events that close 3-7 days out (longer research time)
   - Weekly "premium" event with 10x bankroll stakes

### Long-Term

1. **Real Money Integration**
   - Agents place real bets on Kalshi (requires trading API access)
   - Legal/compliance considerations
   - Risk management (cap exposure per agent)

2. **Agent Learning**
   - Meta-agents that analyze performance and adapt strategies
   - Reinforcement learning from outcomes
   - Would require separate "adaptive" agent category

3. **Multi-Platform Markets**
   - Expand beyond Kalshi to Polymarket, Metaculus, etc.
   - Cross-market arbitrage opportunities
   - More diverse event types

4. **Social Features**
   - User comments on events
   - "Follow" specific agents
   - Prediction contests (guess which agent wins)

---

## Implementation Checklist

### Phase 1: Backend Foundation (Week 1-2)

- [ ] Set up FastAPI project structure
- [ ] Configure MongoDB connection (Motor + Pymongo)
- [ ] Implement Pydantic models for all collections
- [ ] Set up Logfire integration
- [ ] Create .env configuration (API keys)
- [ ] Implement Kalshi API client
- [ ] Implement OpenRouter API client
- [ ] Implement Exa AI API client

### Phase 2: Pipeline - Stage 1 (Week 2)

- [ ] Implement event ingestion logic
- [ ] Fetch ~20 events from Kalshi API
- [ ] Build LLM-based event selection (prompt LLM to choose 5 most interesting)
- [ ] Test with live Kalshi API (dry run)
- [ ] Write events to MongoDB

### Phase 3: Pipeline - Stage 2 (Week 2-3)

- [ ] Implement research agent with Exa AI
- [ ] Design intelligence brief template
- [ ] Test brief generation on sample events
- [ ] Store briefs in MongoDB

### Phase 4: Pipeline - Stage 3 (Week 3)

- [ ] Load persona configs from YAML
- [ ] Implement agent context loading (bankroll + history)
- [ ] Build agent decision prompt template
- [ ] Implement OpenRouter LLM calls for 8 agents
- [ ] Parse and validate JSON responses
- [ ] Store bets in MongoDB
- [ ] Handle timeouts and failures

### Phase 5: Pipeline - Stage 4 (Week 3-4)

- [ ] Implement settlement trigger (cron/scheduler)
- [ ] Fetch outcomes from Kalshi API
- [ ] Calculate PnL with fee deductions
- [ ] Update bets and agent bankrolls
- [ ] Handle VOID events (refunds)

### Phase 6: REST API (Week 4)

- [ ] Implement `/api/leaderboard` endpoint
- [ ] Implement `/api/events` endpoint
- [ ] Implement `/api/events/{id}` endpoint
- [ ] Implement `/api/agents/{id}` endpoint
- [ ] Implement `/api/batches` endpoint
- [ ] Add CORS configuration for frontend

### Phase 7: Frontend Integration (Week 4-5)

- [ ] Replace hardcoded agent data with API calls
- [ ] Implement leaderboard fetching
- [ ] Build event history view
- [ ] Build agent detail pages
- [ ] Add current persona display
- [ ] Polish UI with real data

### Phase 8: Observability & Deployment (Week 5)

- [ ] Configure Logfire dashboards
- [ ] Set up alert rules (email/Slack)
- [ ] Deploy backend to production (Heroku/Railway/Fly.io)
- [ ] Set up MongoDB Atlas production cluster
- [ ] Configure cron jobs for pipeline
- [ ] Deploy frontend to Vercel

### Phase 9: Testing & Refinement (Week 5-6)

- [ ] Run end-to-end tests with real APIs
- [ ] Monitor costs and performance
- [ ] Tune persona prompts based on results
- [ ] Fix bugs and edge cases
- [ ] Load test API endpoints
- [ ] Optimize database queries

### Phase 10: Launch (Week 6)

- [ ] Seed agents with $100k bankrolls
- [ ] Run first production pipeline
- [ ] Monitor closely for 3-5 days
- [ ] Public announcement (Twitter/Reddit/Product Hunt)
- [ ] Gather user feedback

---

## Critical Files to Create

### Phase 1: Foundation (Week 1)

1. **`backend/config.py`** - Pydantic Settings
   - MongoDB connection string
   - API keys (Kalshi, OpenRouter, Exa AI, Logfire)
   - Environment detection (dev/prod)
   - Validation at startup

2. **`backend/database/connection.py`** - Motor client
   - Async MongoDB connection
   - Connection pooling
   - Ping check on startup

3. **`backend/models/pipeline/state.py`** - DailyPipelineState
   - In-memory state object
   - All stage inputs/outputs
   - Tracking fields (timings, errors)

4. **`backend/pipeline/core/base_stage.py`** - BasePipelineStage
   - Abstract base class for all stages
   - `execute()` method signature
   - Automatic logging and timing
   - Error handling wrapper

5. **`backend/pipeline/core/runner.py`** - PipelineRunner
   - Sequential stage execution
   - Progress callbacks
   - Error propagation

6. **`backend/pipeline/core/exceptions.py`** - Exception hierarchy
   - PipelineExecutionError base
   - Retryable vs non-retryable
   - Custom error types per stage

### Phase 2: Stage 1 Refactor (Week 1-2)

7. **`backend/pipeline/stages/ingestion/main.py`** - IngestionStage
   - Implements BasePipelineStage
   - Coordinates kalshi_client and llm_selector
   - Outputs to `pipeline_state.selected_events`

8. **`backend/pipeline/stages/ingestion/kalshi_client.py`**
   - Kalshi API wrapper
   - Fetch ~20 active events
   - Event filtering (markets closing within 24 hours)

9. **`backend/pipeline/stages/ingestion/llm_selector.py`**
   - LLM-based event selection
   - Prompts LLM to choose 5 most interesting events from the 20 fetched
   - Price locking for selected events

### Phase 3: Remaining Stages (Week 2-3)

10. **`backend/pipeline/stages/research/main.py`** - ResearchStage
11. **`backend/pipeline/stages/research/exa_client.py`**
12. **`backend/pipeline/stages/research/brief_generator.py`**
13. **`backend/pipeline/stages/betting/main.py`** - BettingStage
14. **`backend/pipeline/stages/betting/agent_runner.py`**
15. **`backend/pipeline/stages/settlement/main.py`** - SettlementStage
16. **`backend/pipeline/stages/settlement/payout_calculator.py`**

### Phase 4: Celery + Scheduling (Week 3)

17. **`backend/celery_config.py`** - Celery app configuration
18. **`backend/tasks/pipeline_tasks.py`** - Daily pipeline task
19. **`backend/tasks/settlement_tasks.py`** - Dynamic settlement scheduling

### Phase 5: Repositories (Week 3-4)

20. **`backend/database/repositories/base.py`** - BaseRepository
21. **`backend/database/repositories/events.py`** - EventRepository
22. **`backend/database/repositories/agents.py`** - AgentRepository
23. **`backend/database/repositories/bets.py`** - BetRepository

### Phase 6: API Layer (Week 4)

24. **`backend/api/routes/leaderboard.py`** - Leaderboard endpoint
25. **`backend/api/routes/events.py`** - Events endpoints
26. **`backend/api/routes/agents.py`** - Agent profile endpoints

### Additional Critical Files

27. **`backend/models/database/agent.py`** - Agent MongoDB schema
28. **`backend/models/database/event.py`** - Event MongoDB schema
29. **`backend/models/database/bet.py`** - Bet MongoDB schema
30. **`backend/models/database/daily_batch.py`** - DailyBatch MongoDB schema
31. **`backend/models/api/leaderboard.py`** - Leaderboard API response models
32. **`backend/models/pipeline/decisions.py`** - BetDecision, EventData models
33. **`backend/personas/conservative_value.yaml`** - Example persona
34. **`backend/utils/logging.py`** - Logfire integration
35. **`backend/pipeline/__init__.py`** - Factory function: create_daily_pipeline()

### Frontend

1. `frontend/lib/api.ts` - API client for backend
2. `frontend/app/agents/[id]/page.tsx` - Agent detail page
3. `frontend/app/events/[id]/page.tsx` - Event detail page
4. `frontend/components/leaderboard-live.tsx` - Live leaderboard component

---

## Success Metrics

### Week 1 (MVP Launch)
- [ ] Pipeline runs successfully for 3 consecutive days
- [ ] All 8 agents make decisions without errors
- [ ] Settlement calculates correctly (verified against manual calculations)
- [ ] Frontend displays live data from backend API
- [ ] Total cost <$3/day

### Month 1
- [ ] 30 consecutive successful pipeline runs
- [ ] Agent bankrolls show realistic variance (no single agent dominates >50% of capital)
- [ ] At least 100 total events settled
- [ ] Frontend has 100+ unique visitors
- [ ] Zero critical bugs requiring emergency fixes

### Month 3
- [ ] Agent performance diverges (clear winners/losers emerging)
- [ ] User engagement: 500+ weekly active visitors
- [ ] Community interest: Featured on AI/prediction market forums
- [ ] Profitable agents identified for further study
- [ ] Persona rotation shows strategy impact (can compare weeks)

---

## Conclusion

This spec defines a **production-ready** AI prediction market simulation system with:

✅ **Clear architecture**: Daily batch pipeline with 4 distinct stages orchestrated by PipelineRunner
✅ **Robust orchestration**: BasePipelineStage interface + in-memory DailyPipelineState for clean data flow
✅ **Async task execution**: Celery + Redis for reliable distributed processing with automatic retries
✅ **Comprehensive schema**: Normalized MongoDB collections with proper indexes + repository pattern
✅ **Clean separation**: 3-tier models (database, API, pipeline) for maintainability
✅ **Cost-effective**: ~$70/month for MVP operation with full observability
✅ **Observable**: Pydantic + Logfire for full visibility (automatic LLM call tracking)
✅ **Scalable**: Monolithic start with clear module boundaries, can scale horizontally via Celery workers
✅ **Testable**: Unit tests with mocks + integration tests + incremental testing approach
✅ **Flexible**: Persona rotation system for strategy experimentation
✅ **User-friendly**: Read-only leaderboard frontend for spectator experience

**Key Improvements Over Initial Design**:
- ✅ **Pipeline orchestration pattern** from proven pythonserver architecture
- ✅ **In-memory state management** for faster execution and atomic commits
- ✅ **Celery integration** for production-grade task scheduling (replaces vague "cron or cloud scheduler")
- ✅ **Repository pattern** for testable database layer
- ✅ **Custom exception hierarchy** with retry logic for resilience
- ✅ **Hybrid write strategy** balancing performance with data safety

**Next step**: Begin Phase 1 implementation (backend foundation) starting with:
1. `config.py` - Pydantic Settings
2. `pipeline/core/base_stage.py` - BasePipelineStage abstract class
3. `pipeline/core/runner.py` - PipelineRunner orchestrator
4. `models/pipeline/state.py` - DailyPipelineState dataclass

Then proceed to refactor Stage 1 (ingestion) as proof of concept before applying pattern to remaining stages.
