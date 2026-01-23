# Coliseum: Autonomous Quant Agent System

## Specification Document v2.1 (Streamlined)

---

## Executive Summary

**Coliseum** is an autonomous quantitative trading system that deploys AI agents to trade on Kalshi prediction markets. The system operates as a fully autonomous pipeline where specialized agents collaborate to research events, identify trading opportunities, execute positions, and continuously monitor the portfolio.

### Vision Statement
> *Build a self-sustaining AI trading system that can independently identify high-value prediction market opportunities, execute trades with disciplined risk management, and adapt to changing market conditions—all with minimal human intervention.*

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Autonomous Operation** | Agents run 24/7 with minimal human oversight |
| **Research-Driven** | Every trade is backed by deep, grounded research |
| **Risk-First** | Hard limits and circuit breakers prevent catastrophic losses |
| **Transparent** | Full audit trail of every decision and trade |
| **Adaptable** | Agents learn from outcomes and adjust strategies |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COLISEUM AUTONOMOUS TRADING SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌──────────────┐                                    ┌──────────────┐         │
│    │              │    Opportunities     ┌────────────▶│              │         │
│    │    SCOUT     │───────────────────▶  │             │   GUARDIAN   │         │
│    │    Agent     │                      │             │    Agent     │         │
│    │              │                      │             │              │         │
│    └──────┬───────┘                      │             └──────┬───────┘         │
│           │                              │                    │                 │
│           │ New Events                   │                    │ Exit Signals    │
│           ▼                              │                    ▼                 │
│    ┌──────────────┐                      │             ┌──────────────┐         │
│    │              │    Recommendations   │             │              │         │
│    │   ANALYST    │──────────────────────┼────────────▶│    TRADER    │         │
│    │    Agent     │                      │             │    Agent     │         │
│    │              │                      │             │              │         │
│    └──────────────┘                      │             └──────────────┘         │
│           │                              │                    │                 │
│           │                              │                    │                 │
│    ┌──────┴──────────────────────────────┴────────────────────┴──────┐          │
│    │                    LOCAL FILE STORAGE                           │          │
│    │         Markdown + YAML Files (Human-Readable & Git-Friendly)   │          │
│    └─────────────────────────────────────────────────────────────────┘          │
│           │                              │                    │                 │
│           ▼                              ▼                    ▼                 │
│    ┌─────────────────────────────────────────────────────────────────┐          │
│    │                       EXTERNAL SERVICES                         │          │
│    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │          │
│    │  │ Kalshi  │  │  Exa AI │  │Perplexity│ │  News   │             │          │
│    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘             │          │
│    └─────────────────────────────────────────────────────────────────┘          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```
Scout ──(Creates Opportunity File)──▶ Researcher ──(Appends Research)──▶ Recommender ──(Appends Evaluation)──▶ Trader
                                                                                                                    │
                                                                                   ┌────────────────────────────────┘
                                                                                   │
Guardian ◀──(OpenPosition)─────────────────────────────────────────────────────────┘
   │
   └──(ExitSignal)──▶ Trader ──(ClosePosition)──▶ Kalshi
```

**Key Architecture Decision**: All three stages (Scout, Researcher, Recommender) write to a **single opportunity file**, progressively enriching it with new sections and frontmatter fields. This eliminates the need for separate `research/` and `recommendations/` directories and provides a unified audit trail per event.

---

## Technology Stack

### Core Framework

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Agent Framework** | PydanticAI | Type-safe agents with structured outputs |
| **Backend** | Python 3.11+ (CLI) | Agent execution, local operation |
| **Storage** | Markdown + YAML Files | Human-readable, git-friendly persistence |
| **State** | `state.yaml` | Single source of truth for portfolio state |
| **Scheduler** | APScheduler | In-process scheduled jobs |
| **Observability** | Pydantic Logfire | LLM tracing, performance monitoring |

### AI/ML Services

| Service | Provider | Use Case |
|---------|----------|----------|
| **Primary LLM** | Anthropic (Claude Sonnet 4) | Agent reasoning, analysis |
| **Fast LLM** | Anthropic (Claude Haiku 4) | Quick decisions, monitoring |
| **Deep Reasoning** | Anthropic (Claude Opus 4) | Complex analysis (optional) |
| **Research Answers** | Exa AI | Comprehensive answers with citations |
| **Real-time Search** | Perplexity API | Breaking news, current events |

### External APIs

| API | Purpose | Authentication |
|-----|---------|----------------|
| **Kalshi Markets** | Read market data | API Key (public endpoints) |
| **Kalshi Trading** | Execute trades | API Key + RSA Private Key |
| **Exa AI** | Question answering with cited sources | API Key |
| **Perplexity** | Real-time information | API Key |

---

## Agent Specifications

### 1. Scout Agent 🔍 (IMPLEMENTED)

**Mission**: Continuously discover and filter high-quality trading opportunities from Kalshi markets.

#### Responsibilities
- Scan Kalshi API for new/updated events
- Filter events by liquidity, volume, and close time
- Categorize events by topic (politics, crypto, sports, etc.)
- Identify events suitable for research
- Create opportunity files for Analyst processing

#### Execution Schedule
- **Quick Scan**: Every 15 minutes (checks recent events)
- **Full Scan**: Every 60 minutes (comprehensive market sweep)
- Triggered on-demand via CLI: `python -m coliseum scout`

#### Tools Available

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `get_active_events` | Fetch events from Kalshi API | `services/kalshi.py` |
| `filter_by_volume` | Apply volume/liquidity filters | Built-in logic |
| `categorize_event` | Classify by topic | LLM-based classification |
| `check_close_time` | Filter by time to expiration | Date arithmetic |

#### Output Format
Creates opportunity file at `data/opportunities/{ticker}.md` with:
- Scout assessment (quality, rationale)
- Market snapshot (prices, volume, liquidity)
- Event metadata (title, close date, category)

---

### 2. Analyst Agent 📊 (IMPLEMENTED)

**Mission**: Deeply research opportunities and generate actionable trade recommendations.

The Analyst agent is split into two specialized sub-agents that work sequentially:

#### 2A. Researcher Sub-Agent 🕵️

**Mission**: Conduct comprehensive research on the event and synthesize findings.

##### Responsibilities
- Fetch opportunity details from the stored opportunity file
- Formulate specific research questions for the market
- Use Exa AI to gather grounded answers with citations
- Synthesize research into a structured markdown report
- Append research section and update frontmatter metadata

##### Tools Available

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `fetch_opportunity_details` | Load opportunity data (market info, prices, rationale) | `agents/analyst/researcher/main.py` |
| `exa_answer` | Get answers with citations from Exa AI | `services/exa/client.py` |

##### Output Format
Appends to opportunity file:
- Research synthesis section (markdown)
- Sources list (URLs)
- Frontmatter updates: `research_completed_at`, `research_sources_count`, `research_duration_seconds`

---

#### 2B. Recommender Sub-Agent ⚖️

**Mission**: Evaluate trading opportunity and generate recommendation based on research.

##### Responsibilities
- Calculate edge and expected value using research insights
- Assess trade quality (confidence, risk, opportunity cost)
- Apply risk management filters
- Generate buy/sell recommendation with position sizing
- Append recommendation section to opportunity file

##### Tools Available

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `calculate_edge` | Compute market inefficiency | `agents/calculations.py` |
| `calculate_ev` | Expected value calculation | `agents/calculations.py` |
| `kelly_criterion` | Optimal position sizing | `agents/calculations.py` |
| `risk_check` | Validate against hard limits | `agents/risk.py` |

##### Output Format
Appends to opportunity file:
- Trade evaluation (YES/NO recommendation)
- Edge and EV calculations
- Position sizing (Kelly fraction, contract quantity)
- Reasoning and risk assessment

---

#### Analyst Pipeline Flow

```
Opportunity File (Scout)
         │
         ▼
    Researcher ───(Appends Research)───▶ Opportunity File
         │
         ▼
   Recommender ───(Appends Evaluation)───▶ Opportunity File (Final)
         │
         ▼
    Trader (direct handoff)
```

**See**: [`docs/Research_agent_pipeline.md`](./Research_agent_pipeline.md) for detailed pipeline specification.

---

### 3. Trader Agent 💰 (NOT YET IMPLEMENTED)

**Mission**: Execute trades with disciplined risk management and slippage protection.

#### Planned Responsibilities
- Validate recommendations against current portfolio state
- Calculate slippage-adjusted edge before execution
- Execute trades using limit orders only (never market orders)
- Use "working order" strategy (place → wait → reprice → cancel after 3 attempts)
- Update portfolio state and create position files
- Log all trades to JSONL ledger

#### Execution
- On-demand (direct handoff from Analyst)
- Triggered by: `python -m coliseum trader --recommendation-id <id>`

#### Order Execution (TODO)

The Trader agent will use limit orders only (never market orders) with slippage protection. Orders will be "worked" (place → wait → reprice) rather than fire-and-forget. See implementation in `agents/trader/` when built.

---

### 4. Guardian Agent 🛡️ (NOT YET IMPLEMENTED)

**Mission**: Continuously monitor open positions and trigger exits when conditions warrant.

#### Planned Responsibilities
- Monitor price movements and market conditions
- Track time decay on expiring positions
- Watch for negative news or research invalidation
- Evaluate exit criteria (target profit, stop loss, time-based)
- Generate exit signals for Trader to execute
- Update position health metrics

#### Execution Schedule (Planned)
- **Position Check**: Every 15 minutes
- **News Scan**: Every 30 minutes
- Triggered on-demand: `python -m coliseum guardian --check-positions`

#### Monitoring (TODO)

Position monitoring and exit signal generation will be implemented in `agents/guardian/`. See placeholder in codebase.

---

## File Storage Structure

### Design Principles

1. **Human-Readable**: All files are Markdown or YAML (no binary formats)
2. **Git-Friendly**: Meaningful diffs, easy to track changes
3. **Auditable**: Every decision has a paper trail
4. **Single Source of Truth**: `state.yaml` contains portfolio state
5. **Progressive Enrichment**: Opportunity files grow as agents process them

### Directory Layout

```
backend/data/
├── config.yaml                 # System configuration (risk limits, agent settings)
├── state.yaml                  # Portfolio state (cash, positions, daily PnL)
├── .env                        # API keys (git-ignored)
│
├── opportunities/              # Market opportunities (Scout → Researcher → Recommender)
│   ├── INXD-25JAN31-B4621.md  # Single file per event (progressive enrichment)
│   └── FEDNXT-25MAR-U75.md
│
├── positions/
│   ├── open/                   # Active positions (updated by Guardian)
│   │   └── INXD-25JAN31-B4621.yaml
│   └── closed/                 # Historical positions (archived on exit)
│       └── FEDNXT-25MAR-U75.yaml
│
└── trades/                     # Trade ledger (append-only JSONL)
    ├── 2025-01-14.jsonl
    └── 2025-01-15.jsonl
```

### Single-File Event Tracking

**Key Design**: All agent outputs for a single event are written to **one opportunity file** that grows progressively:

1. **Scout** creates the file with initial assessment
2. **Researcher** appends research section
3. **Recommender** appends evaluation section

This provides:
- Unified audit trail per opportunity
- Easy human review (one file to read)
- Simplified file management (no cross-referencing needed)
- Git-friendly diffs showing decision evolution

### Key File Formats

#### Example: Opportunity File Progression

**After Scout:**
```markdown
---
ticker: INXD-25JAN31-B4621
created_at: 2025-01-14T10:30:00Z
status: scout_complete
event_title: "Will S&P 500 be above 4621 on Jan 31, 2025?"
close_time: 2025-01-31T21:00:00Z
category: finance
scout_quality: high
volume_24h: 15234
liquidity_score: 0.82
current_yes_price: 0.58
current_no_price: 0.42
---

# Will S&P 500 be above 4621 on Jan 31, 2025?

## Scout Assessment

High-quality opportunity identified based on:
- Strong liquidity (score: 0.82)
- High 24h volume (15,234 contracts)
- Event closes in 17 days
- Clear binary outcome

## Market Snapshot

| Metric | Value |
|--------|-------|
| Current YES Price | $0.58 |
| Current NO Price | $0.42 |
| 24h Volume | 15,234 contracts |
| Open Interest | 42,150 contracts |
| Bid-Ask Spread | 0.02 |
```

**After Researcher:**
```markdown
---
# ... (Scout frontmatter preserved)
status: research_complete
researcher_completed_at: 2025-01-14T10:45:00Z
research_confidence: high
---

# ... (Scout content preserved)

## Research Synthesis

Based on comprehensive analysis of S&P 500 historical trends, current economic indicators, and market sentiment:

### Key Facts

- S&P 500 currently at 4,580 (as of Jan 14)
- Target of 4,621 represents +0.9% gain over 17 days
- Historical Jan-Feb average return: +1.2%
- Current volatility: 12.3 (moderate)
- No major earnings reports or Fed meetings until Feb

### Sources

1. **S&P 500 Historical Performance Analysis** (Exa AI)
   - URL: https://example.com/sp500-analysis
   - Key quote: "January historically shows positive returns in 68% of years since 1950"

2. **Real-time Market Sentiment** (Perplexity)
   - Analyst consensus: Neutral to bullish through month-end
   - No major risk events on calendar

### Research Confidence: High
Data quality is excellent with multiple corroborating sources.
```

**After Recommender:**
```markdown
---
# ... (Scout + Researcher frontmatter preserved)
status: recommendation_complete
recommender_completed_at: 2025-01-14T11:00:00Z
recommendation: BUY_YES
edge: 0.12
expected_value: 0.18
position_size_pct: 0.025
contract_quantity: 25
---

# ... (Scout + Researcher content preserved)

## Trade Evaluation

**Recommendation**: BUY YES (25 contracts)

### Reasoning

Market is pricing 58% probability, but research suggests 70% chance of S&P reaching 4,621:
- Historical patterns favor January gains
- Current momentum is positive (+1.8% YTD)
- No major risk events on calendar
- Volatility is moderate and stable

**True Probability Estimate**: 70%
**Market Implied Probability**: 58%
**Edge**: +12 percentage points

### Position Sizing

- **Edge**: 12%
- **Expected Value**: +18%
- **Kelly Fraction**: 1/4 Kelly = 2.5% of portfolio
- **Contract Quantity**: 25 contracts ($14.50 cost basis)
- **Max Loss**: $14.50 (if S&P fails to reach target)
- **Max Gain**: $10.50 (if S&P reaches 4,621)

### Risk Assessment

- Within position size limits (2.5% < 10% max)
- Positive expected value (+18%)
- Acceptable liquidity for entry/exit
- **APPROVED FOR TRADING**
```

---

## Risk Management Framework

### Hard Limits (Circuit Breakers)

These limits are **never bypassed** under any circumstances:

| Limit | Threshold | Action |
|-------|-----------|--------|
| **Max Position Size** | 10% of portfolio | Reject trade immediately |
| **Max Single Trade** | $1,000 | Reject trade immediately |
| **Max Open Positions** | 10 concurrent | Reject trade until position closes |
| **Daily Loss Limit** | 5% of portfolio | Halt all trading for 24 hours |
| **Min Edge Threshold** | 5% | Skip trade (insufficient edge) |
| **Min EV Threshold** | 10% | Skip trade (insufficient expected value) |

### Position-Level Rules

| Rule | Logic | Rationale |
|------|-------|-----------|
| **Slippage Protection** | Reject if slippage destroys 50%+ of edge | Preserve profitable trades only |
| **Liquidity Check** | Require 5x position size in open interest | Ensure ability to exit |
| **Time Decay** | Increase exit urgency as event approaches | Avoid theta decay on losing positions |
| **Stop Loss** | Exit if loss exceeds 2x expected loss | Protect against catastrophic outcomes |

### Trading Calculations

All position sizing uses Kelly Criterion (1/4 Kelly default). See [`calculations.md`](./calculations.md) for mathematical foundations including:
- Edge calculation
- Expected value (EV) calculation
- Kelly Criterion formula
- Slippage-adjusted sizing

---

## File Operations

All file operations use atomic writes (tempfile + rename) to prevent corruption. See `coliseum/storage/` for implementation:

| Module | Purpose |
|--------|---------|
| `state.py` | Portfolio state management (read/write `state.yaml`) |
| `files.py` | Opportunity and position file operations |
| `queue.py` | Analyst queue helpers (TODO: not yet implemented) |

---

## Scheduler & Execution

### Scheduled Jobs

| Job | Frequency | Status |
|-----|-----------|--------|
| Scout quick scan | Every 15 min | ✅ Implemented |
| Scout full scan | Every 60 min | ✅ Implemented |
| Guardian position check | Every 15 min | ❌ Not implemented |
| Guardian news scan | Every 30 min | ❌ Not implemented |

Implementation: `coliseum/scheduler.py` using APScheduler.

---

## Telegram Alerts (TODO: Not Yet Implemented)

Real-time notifications for trades, position changes, and risk events will be sent directly via Telegram Bot API (no local file storage). See `services/telegram.py` stub for future implementation.

Planned alert types:
- Trade executed
- Position opened/closed
- Circuit breaker triggered
- Daily P&L summary

**Note**: Alerts are sent directly via Telegram and are not persisted to local files.

---

## Observability & Monitoring

### Logfire Integration

All agent runs are automatically traced using Pydantic Logfire, providing:
- LLM call latency and token usage
- Agent decision trees
- Tool execution traces
- Error tracking

Configuration: Set `LOGFIRE_TOKEN` in `.env`

### Key Metrics to Track

| Metric | Purpose |
|--------|---------|
| **Win Rate** | % of profitable trades |
| **Average Edge** | Mean edge across all trades |
| **Sharpe Ratio** | Risk-adjusted returns |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Daily P&L** | Track against loss limits |

---

## Implementation Phases
---

### Phase 1: Foundation (Week 1-2)

**Goal**: Core infrastructure—agents can run, Kalshi API works, files persist.

#### 1.1 Project Setup
- [ ] Create `coliseum/` package structure (directories + `__init__.py` files)
- [ ] Create `coliseum/__main__.py` with basic CLI skeleton (`init`, `run`, `status`)
- [ ] Create `coliseum/config.py` to load `data/config.yaml` and `.env`
- [ ] Update `requirements.txt`:
  - Add: `apscheduler>=3.10.4`, `pyyaml>=6.0.1`, `cryptography>=42.0.0`
  - Remove: `celery`, `redis`, `flower`, `kombu` (no longer needed)

#### 1.2 Storage Layer (`coliseum/storage/`)
- [ ] `state.py`: Implement `load_state()`, `save_state()` with atomic writes
- [ ] `files.py`: Implement `save_opportunity()`, `save_recommendation()`, `log_trade()`
- [ ] `queue.py`: Implement `queue_for_analyst()`, `get_pending()`
- [ ] Create `data/config.yaml` template with all configuration options
- [ ] Create `data/state.yaml` initial template (empty portfolio)

#### 1.3 Kalshi API Client (`coliseum/services/kalshi.py`)
- [ ] Migrate `mess_around/explore_kalshi_api.py` → production client
- [ ] Add `KalshiTradingAuth` class (RSA signature generation)
- [ ] Implement authenticated methods:
  - `get_balance()` → Account balance and buying power
  - `get_positions()` → All open positions
  - `place_order(ticker, side, count, type, price)` → Execute trade
  - `cancel_order(order_id)` → Cancel pending order
  - `get_order_status(order_id)` → Check fill status
- [ ] Add paper mode flag (skip actual API calls, simulate fills)

#### 1.4 Scout Agent (`coliseum/agents/scout.py`)
- [ ] Create `ScoutConfig`, `OpportunitySignal` Pydantic models
- [ ] Implement `scout_agent` with PydanticAI
- [ ] Add tools: `fetch_markets`, `check_liquidity`, `categorize_event`
- [ ] Implement `run_scout()` function that writes to `data/opportunities/`
- [ ] Queue discovered opportunities for Analyst


#### 1.6 Phase 1 Verification
| Test | Method |
|------|--------|
| Storage atomic writes | Unit test: write state, crash mid-write, verify no corruption |
| Kalshi API connection | Integration: fetch markets, verify response parsing |
| Scout market discovery | Manual: run scout, inspect `data/opportunities/` output |


---

### Phase 2: Intelligence (Week 3-4)

**Goal**: Analyst pipeline produces high-quality analysis reports backed by research.

#### 2.1 Exa AI Integration (`coliseum/services/exa/`)
- [x] Create `ExaClient` async wrapper for `exa-py` SDK
- [x] Implement `answer(question, include_text, system_prompt)` → `ExaAnswerResponse` with citations
- [x] Add error handling with retry logic (exponential backoff for 429/5xx errors)
- [x] Define Pydantic models: `ExaAnswerResponse`, `ExaCitation`, `ExaConfig`

**Note**: Uses only the Exa `answer` endpoint for comprehensive research responses with built-in citations, eliminating need for separate search/synthesis steps.

#### 2.2 Analyst Pipeline (`coliseum/agents/analyst/`)
- [ ] Create Pydantic models:
  - `ResearcherConfig` (timeout, required sources)
  - `RecommenderConfig` (min edge threshold)
  - Extended `OpportunitySignal` (with research + recommendation fields)
- [ ] Implement Researcher agent (`coliseum/agents/analyst/researcher/main.py`)
- [ ] Implement Recommender agent (`coliseum/agents/analyst/recommender/main.py`)
- [ ] Add tools:
  - Researcher: `exa_answer(question)` → Comprehensive answers with citations
  - Recommender: `read_opportunity_research()` → Extract research from opportunity file
  - Recommender: `calculate_edge_ev(probability, market_price)` → Edge and EV
- [ ] Implement append-based workflow:
  1. Receive opportunity_id from Scout queue
  2. **Researcher**: Load opportunity file, conduct research, append research section
  3. **Recommender**: Load same opportunity file, extract research, append evaluation section
  4. Result: Single opportunity file with all three stages (Scout → Researcher → Recommender)

#### 2.3 Edge/EV Calculations (`coliseum/agents/calculations.py`)
- [ ] `calculate_edge(true_prob, market_prob)` → Edge percentage
- [ ] `calculate_expected_value(win_prob, payout, cost)` → EV per dollar
- [ ] `calculate_kelly_fraction(win_prob, odds, fraction=0.25)` → Position size %

#### 2.4 Analyst Queue Processing
- [ ] Implement `process_analyst_queue()`:
  1. Read pending items from `data/queue/analyst/`
  2. Load opportunity from `data/opportunities/`
  3. Run Analyst pipeline (Researcher -> Recommender)
  4. Append research and recommendation to the opportunity file
  5. If action != `ABSTAIN`, hand off directly to Trader
  6. Delete processed queue item

#### 2.5 Logfire Observability
- [ ] Add `logfire.configure()` to `coliseum/__init__.py`
- [ ] Instrument PydanticAI with `logfire.instrument_pydantic_ai()`
- [ ] Add custom spans for key operations (research, recommendation)

#### 2.6 Phase 2 Verification
| Test | Method |
|------|--------|
| Exa answer endpoint | Unit test: verify comprehensive answers with citations are returned |
| Research brief quality | Manual: inspect generated briefs for source quality and citation accuracy |
| Edge/EV calculations | Unit test: verify math against known examples |
| Full pipeline | Integration: opportunity → research → recommendation |

---

### Phase 3: Execution (Week 5-6)

**Goal**: Trader agent safely executes trades with full risk management and liquidity-aware order execution.

#### 3.1 Risk Management (`coliseum/agents/risk.py`)
- [ ] Create `RiskManager` class with validation methods:
  - `check_position_limit(trade, portfolio)` → Max 10% per position
  - `check_daily_loss(portfolio)` → Max 5% daily loss
  - `check_open_positions(portfolio)` → Max 10 concurrent positions
  - `check_single_trade_cap(trade)` → Max $1,000 per trade
  - `check_edge_threshold(trade)` → Min 5% edge
  - `check_ev_threshold(trade)` → Min 10% EV
- [ ] Implement `validate_trade(trade, portfolio)` → `(passed: bool, reason: str)`

#### 3.2 Order Execution Models (`coliseum/agents/execution.py`)
- [ ] Create Pydantic models:
  - `OrderBookLevel` (price, contracts available)
  - `OrderBookDepth` (bid/ask levels, spreads, aggregate liquidity)
  - `SlippageEstimate` (fill simulation, adjusted edge/EV)
  - `ExecutionConfig` (slippage tolerance, reprice settings, timeouts)
  - `OrderState` enum (initialized, placed, partial, completed, cancelled)
  - `WorkingOrder` (order tracking through execution loop)

#### 3.3 Order Book & Slippage (`coliseum/services/kalshi.py`)
- [ ] Add `get_order_book(ticker)` → Fetch full order book depth from Kalshi
- [ ] Implement `calculate_slippage(order_book, side, contracts, max_price)`:
  - Walk order book levels
  - Calculate volume-weighted average fill price
  - Return `SlippageEstimate` with adjusted edge/EV
- [ ] Implement `size_with_liquidity(kelly_size, order_book, max_slippage)`:
  - Binary search for max size within slippage tolerance
  - Return reduced position size if order book is thin

#### 3.4 Trader Agent (`coliseum/agents/trader.py`)
- [ ] Create Pydantic models:
  - `TraderConfig` (limits, thresholds, paper mode flag)
  - `TradeExecution` (position details, sizing, execution status)
- [ ] Implement `trader_agent` with PydanticAI
- [ ] Add tools:
  - `get_portfolio_state()` → Current positions and P&L
  - `get_order_book_depth(ticker)` → Fetch bid/ask levels
  - `calculate_slippage(order_book, size)` → Estimate fill quality
  - `calculate_position_size(recommendation, order_book)` → Kelly + liquidity
  - `place_limit_order(ticker, side, contracts, limit_price)` → Execute limit order
  - `reprice_order(order_id, new_limit)` → Cancel and replace
  - `record_trade(execution)` → Log to JSONL ledger

#### 3.5 Working Order Execution Loop (`coliseum/agents/trader.py`)
- [ ] Implement order state machine:
  - `INITIALIZED` → `PLACED_LIMIT` → `CHECK_STATUS` → `COMPLETED/PARTIAL/CANCELLED`
- [ ] Implement `work_order(working_order)` loop:
  1. Place limit order at max acceptable price
  2. Wait `check_interval_seconds` (default: 5 min)
  3. Poll fill status from Kalshi
  4. If filled → complete and record
  5. If partial → decide: accept partial or reprice remainder
  6. If unfilled → re-check edge, reprice or cancel
  7. After `max_reprice_attempts` → cancel and log
- [ ] Track all state transitions in `WorkingOrder.state_history`

#### 3.6 Paper Trading Mode
- [ ] When `config.trading.paper_mode: true`:
  - Simulate order book (use snapshot from real data)
  - Simulate partial fills based on order book depth
  - Update `state.yaml` positions as if real
  - Log trades with `paper: true` flag

#### 3.7 Trade Journaling
- [ ] Append all trades to `data/trades/YYYY-MM-DD.jsonl`
- [ ] Include: position ID, recommendation ID, side, contracts, price, edge, EV, slippage, fill_type
- [ ] Store working order history for audit trail
- [ ] Atomically append (no corruption on crash)

#### 3.8 Phase 3 Verification
| Test | Method |
|------|--------|
| Order book parsing | Unit test: parse sample Kalshi order book response |
| Slippage calculation | Unit test: verify avg fill price against manual calculation |
| Slippage edge rejection | Unit test: trade rejected when slippage destroys edge |
| Liquidity sizing | Unit test: position size reduced for thin books |
| Working order loop | Integration: mock partial fill, verify reprice triggered |
| Risk manager blocks bad trades | Unit test: trades exceeding limits are rejected |
| Kelly sizing is correct | Unit test: verify against manual calculations |
| Paper trades logged correctly | Integration: execute paper trade, verify ledger entry |
| State updates correctly | Integration: paper trade, verify `state.yaml` reflects position |

---

### Phase 4: Monitoring (Week 7-8)

**Goal**: Guardian agent watches positions, triggers exits, sends Telegram alerts.

#### 4.1 Guardian Agent (`coliseum/agents/guardian.py`)
- [ ] Create Pydantic models:
  - `GuardianConfig` (check intervals, profit target, stop loss)
  - `PositionHealth` (current state, thesis assessment, recommendation)
  - `ExitSignal` (action, trigger, reasoning, urgency)
- [ ] Implement `guardian_agent` with PydanticAI
- [ ] Add tools:
  - `get_open_positions()` → All positions from `data/positions/open/`
  - `get_current_price(ticker)` → Fetch from Kalshi API
  - `assess_thesis(position, news)` → Re-evaluate original thesis
  - `generate_exit_signal(position, price)` → Profit target / stop loss check
- [ ] Implement position monitoring loop

#### 4.2 Exit Signal Logic
- [ ] Check profit target: Close if P&L >= +50%
- [ ] Check stop loss: Close if P&L <= -30%
- [ ] Check thesis invalidation: LLM re-assesses with new information
- [ ] Check time decay: Reduce position if < 24h to expiry

#### 4.3 Telegram Notifier (`coliseum/services/telegram.py`)
- [ ] Create `TelegramNotifier` class
- [ ] Implement alert methods:
  - `send_trade_executed(trade)` → 🟢 Trade notification
  - `send_position_closed(position, pnl, trigger)` → 🔴 Close notification
  - `send_stop_loss_triggered(position)` → ⚠️ Stop loss alert
  - `send_circuit_breaker(reason, pnl)` → 🚨 Critical alert
  - `send_daily_summary(portfolio)` → 📊 End of day summary
- [ ] Add quiet hours support (only critical alerts during quiet hours)


#### 4.5 Phase 4 Verification
| Test | Method |
|------|--------|
| Telegram messages send | Manual: configure bot, send test message |
| Profit target triggers | Unit test: mock position at +50%, verify exit signal |
| Stop loss triggers | Unit test: mock position at -30%, verify exit signal |
| Guardian loop runs | Integration: start system with open position, verify health checks |

---

### Phase 5: Polish (Week 9+)

**Goal**: CLI interface, production hardening, extended paper trading.

#### 5.1 CLI Interface (`coliseum/__main__.py`)
- [ ] Implement commands:
  ```bash
  python -m coliseum init                    # Initialize data directory
  python -m coliseum run                     # Start full autonomous system
  python -m coliseum scout --scan-type full  # Manual scout scan
  python -m coliseum analyst --opportunity-id OPP123
  python -m coliseum portfolio status        # Show current portfolio
  python -m coliseum positions list          # List open positions
  python -m coliseum positions close TICKER  # Manual position close
  python -m coliseum config show             # Display configuration
  python -m coliseum test-telegram           # Test Telegram connection
  ```
- [ ] Use `argparse` or `click` for CLI framework

#### 5.2 Paper Trading at Scale
- [ ] Run full system in paper mode for 2-4 weeks
- [ ] Track metrics:
  - Hit rate (% of analyses that resolve profitably)
  - Edge accuracy (estimated edge vs actual outcome)
  - Average P&L per trade
  - Sharpe ratio simulation
- [ ] Create `data/metrics/` for performance tracking

#### 5.3 Parameter Tuning
- [ ] Analyze paper trading results
- [ ] Adjust thresholds based on data:
  - Min edge threshold (currently 5%)
  - Min EV threshold (currently 10%)
  - Kelly fraction (currently 0.25)
  - Profit target (currently 50%)
  - Stop loss (currently 30%)
- [ ] Document optimal parameters in `config.yaml`

#### 5.4 Live Trading Transition
- [ ] Create checklist for go-live:
  - [ ] Kalshi account funded
  - [ ] Paper trading profitable for 2+ weeks
  - [ ] All Telegram alerts working
  - [ ] Risk limits verified
  - [ ] Manual override tested
- [ ] Start with reduced limits (e.g., max $100/trade)
- [ ] Gradually increase limits as confidence builds

#### 5.5 Optional: FastAPI Dashboard
- [ ] Create `coliseum/api/dashboard.py`
- [ ] Endpoints:
  - `GET /api/portfolio` → Current state
  - `GET /api/positions` → Open positions
  - `GET /api/opportunities` → Evaluated opportunities (with recommendations)
  - `POST /api/opportunities/{id}/approve` → Manual approval
  - `GET /api/alerts` → Recent alerts
- [ ] Simple static HTML dashboard

#### 5.6 Phase 5 Verification
| Test | Method |
|------|--------|
| CLI commands work | Manual: run each command, verify output |
| Paper trading metrics accurate | Compare logged trades to Kalshi market outcomes |
| Live trade executes | Integration: place small live trade, verify on Kalshi |

---

### Phase 6: Automation & Scheduling (Week 10+)

**Goal**: Full autonomous operation with scheduled jobs and robust alerting.

#### 6.1 Scheduler Implementation (`coliseum/scheduler.py`)
- [ ] Create `AsyncIOScheduler` with jobs:
  - Scout full scan: Every hour at `:00`
  - Scout quick scan: Every 15 minutes
  - Process analyst queue: Every 5 minutes
  - Guardian position check: Every 15 minutes
  - Guardian news scan: Every 30 minutes
  - Daily portfolio snapshot: 4 PM EST
  - Daily summary Telegram: 4:05 PM EST
  - Settlement check: Every 30 minutes
- [ ] Implement `start_scheduler()` and `stop_scheduler()` functions

#### 6.2 Phase 6 Verification
| Test | Method |
|------|--------|
| Scheduler runs jobs | Manual: start scheduler, verify jobs execute on schedule |

---

## Implementation Status

### ✅ Completed (Phase 1-2)

- Scout agent (market discovery)
- Researcher agent (deep research with Exa AI)
- Recommender agent (trade evaluation)
- File-based storage system
- Risk management framework
- Single-file event tracking architecture
- CLI interface for manual execution

### 🚧 In Progress

- Portfolio state management improvements
- Test framework for agent validation

### ❌ Not Yet Implemented

- Trader agent (order execution)
- Guardian agent (position monitoring)
- Telegram alerts
- Automated scheduling (APScheduler integration)
- Paper trading validation (2+ weeks required before live)

See [`IMPLEMENTATION_SUMMARY.md`](./IMPLEMENTATION_SUMMARY.md) for detailed milestone tracking.

---

## Appendix

### Related Documentation

- **[`calculations.md`](./calculations.md)** - Mathematical foundations for edge, EV, and Kelly Criterion
- **[`Research_agent_pipeline.md`](./Research_agent_pipeline.md)** - Detailed Analyst agent (Researcher + Recommender) specification
- **[`IMPLEMENTATION_SUMMARY.md`](./IMPLEMENTATION_SUMMARY.md)** - Completed milestones and progress tracking
- **[`../CLAUDE.md`](../CLAUDE.md)** - Project instructions for AI assistants

### Code References

| Component | Location |
|-----------|----------|
| Scout agent | `coliseum/agents/scout/main.py` |
| Researcher agent | `coliseum/agents/analyst/researcher/` |
| Recommender agent | `coliseum/agents/analyst/recommender/` |
| Risk management | `coliseum/agents/risk.py` |
| Calculations | `coliseum/agents/calculations.py` |
| Kalshi API client | `coliseum/services/kalshi.py` |
| Exa AI client | `coliseum/services/exa/` |
| Storage | `coliseum/storage/` |
| CLI entry point | `coliseum/__main__.py` |

### Environment Variables

Required in `.env` file (see `.env.example`):

```bash
# Kalshi API (required)
KALSHI_API_KEY=your_api_key
KALSHI_PRIVATE_KEY_PATH=/path/to/private_key.pem

# AI Services (required)
ANTHROPIC_API_KEY=your_api_key
EXA_API_KEY=your_api_key

# Observability (optional)
LOGFIRE_TOKEN=your_token
```

**Note**: Trading configuration (risk limits, agent settings) is in `data/config.yaml`, not environment variables.

---

**Document Version**: 2.1 (Streamlined)
**Last Updated**: 2025-01-23
**Purpose**: High-level system design and architecture reference
