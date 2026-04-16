<!-- This README describes the original backend skeleton. The system has since evolved into the Coliseum autonomous trading pipeline (Scout → Analyst → Trader ← Guardian). See CLAUDE.md for current architecture and commands. -->

# Coliseum Backend

Autonomous prediction market trading system using PydanticAI agents on Kalshi. The system discovers, researches, and trades prediction market contracts through a multi-agent pipeline: **Scout** (discovery) → **Analyst** (research) → **Trader** (execution) ← **Guardian** (monitoring).

The backend exposes a FastAPI dashboard server, runs a long-lived autonomous daemon with heartbeat monitoring, and persists all state to Supabase (PostgreSQL) so multiple instances stay in sync.

## Architecture

### Agent Pipeline

The core of Coliseum is a sequential agent pipeline orchestrated by `coliseum/pipeline.py`. Each cycle executes:

1. **Guardian (pre-trade)** — Syncs portfolio state from Kalshi, reconciles closed positions, enforces stop-loss exits
2. **Scout** — Fetches markets from Kalshi, filters by price range / spread / volume / close time, selects high-quality trading opportunities
3. **Analyst (per opportunity)** — Two sub-agents run sequentially:
   - **Researcher** — Performs web research on the opportunity using the OpenAI Responses API with WebSearchTool, produces a structured synthesis
   - **Recommender** — Evaluates flip risk and recommends BUY_YES / BUY_NO / ABSTAIN with confidence
4. **Trader (per opportunity)** — Reviews the Analyst's recommendation, decides EXECUTE_BUY_YES / EXECUTE_BUY_NO / REJECT, places limit orders on Kalshi with slippage protection and reprice logic
5. **Guardian (post-trade)** — Reconciles any newly opened positions

The pipeline supports graceful shutdown via `asyncio.Event`, transient error retries on 500/502/503/429 responses, and a pre-trade cash gate that skips Scout/Analyst/Trader when insufficient funds are available.

### Daemon

`coliseum/daemon.py` runs the pipeline as a long-lived process:

- **Heartbeat loop** — Executes full pipeline cycles at a configurable interval (default: 180 min)
- **Guardian intercycles** — Runs Guardian-only checks between full cycles (default: every 2 min) for real-time stop-loss monitoring
- **Market context refresh** — Refreshes market category metadata every N cycles as a background task
- **Telegram alerts** — Sends heartbeat summaries and escalation alerts when the daemon pauses due to consecutive failures
- **Graceful shutdown** — Handles SIGTERM/SIGINT by setting an `asyncio.Event`, allowing in-progress agent runs to complete
- **Auto-pause** — Pauses the daemon after a configurable number of consecutive failures (default: 5), resuming after the next heartbeat interval

### Data Flow

```
Kalshi API ──► Scout (market discovery)
                    │
                    ▼
              OpportunitySignal (domain model)
                    │
                    ▼
              Analyst (research + recommendation)
                    │
                    ▼
              TraderDecision (BUY_YES / BUY_NO / REJECT)
                    │
                    ▼
              Kalshi API (limit order placement)
                    │
                    ▼
              Guardian (position reconciliation + stop-loss)
```

All pipeline state — opportunities, positions, trades, decisions, run cycles, and learnings — is persisted to Supabase via async SQLAlchemy repositories, making it the shared source of truth for multiple bot instances.

### LLM Providers

Agents use PydanticAI with structured output (`result_type`). The system supports hot-swappable LLM providers via `coliseum/llm_providers.py`:

| Provider | Enum | Models | API Prefix |
|----------|------|--------|------------|
| OpenAI | `OpenAIModel` | GPT-5.4, GPT-5.2, GPT-5-mini, GPT-5-nano | `openai-responses:` |
| Anthropic | `AnthropicModel` | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 | `anthropic:` |
| Fireworks | `FireworksModel` | Llama 3.3 70B, Llama 3.1 405B/70B/8B, DeepSeek V3.2, Kimi K2.5 | `fireworks:` |
| xAI | `GrokModel` | Grok 4.20 reasoning/non-reasoning/multi-agent | `xai:` |

The active provider is configured in `config.yaml` under `llm.provider`. Agents use the OpenAI Responses API with `WebSearchTool` for web-enabled research (Scout Researcher, Analyst Researcher).

### Memory System

The `coliseum/memory/` module provides persistent agent memory:

- **Context** (`context.py`) — Loads Kalshi mechanics and market-type-specific reference material into agent prompts
- **Decisions** (`decisions.py`) — Stores and retrieves past trading decisions for reflective learning
- **Journal** (`journal.py`) — Cycle-level summaries with portfolio snapshots, error logs, and agent results
- **Enums** (`enums.py`) — `LearningCategory` and `LearningAddition` types for the Guardian's Scribe sub-agent
- **I/O** (`_io.py`) — File-based persistence utilities for prompt memory

The Guardian's **Scribe** sub-agent reflects on completed trades, identifying learnings to add or stale learnings to soft-delete, creating a self-improving feedback loop.

### Kalshi Integration

`coliseum/services/kalshi/` provides an async HTTP client for the Kalshi trading API:

- **Auth** (`auth.py`) — RSA-signed request authentication using the Kalshi trading API key + private key
- **Client** (`client.py`) — Async `httpx`-based client with connection pooling, supporting market queries, order book retrieval, order placement/cancellation, and position management
- **Models** (`models.py`) — Pydantic models for `Market`, `Position`, `Order`, `OrderBook`, `Balance`
- **Config** (`config.py`) — Base URL, timeout, and connection pool settings
- **Exceptions** (`exceptions.py`) — Typed exceptions: `KalshiAPIError`, `KalshiAuthError`, `KalshiNotFoundError`, `KalshiRateLimitError`
- **Sync** (`sync.py`) — Portfolio sync logic that reconciles Kalshi state with local state

All orders are placed as **limit orders only** (never market orders). The Trader enforces configurable slippage protection (default: 5%) and a reprice logic with up to 3 attempts at increasing aggression (2¢ per reprice).

### Configuration

The system uses a layered configuration: `.env` for secrets + `config.yaml` for trading parameters, merged via Pydantic Settings (`coliseum/config.py`).

Key configuration knobs in `config.yaml`:

```yaml
llm:
  provider: "xai"          # Active LLM provider

trading:
  paper_mode: false          # Set true for paper trading (no real orders)
  contracts: 5               # Default contract quantity per trade

scout:
  market_fetch_limit: 20000  # Max markets to fetch from Kalshi
  min_close_hours: 0         # Min hours until market close
  max_close_hours: 48        # Max hours until market close
  min_price: 92              # Min YES price (cents)
  max_price: 96              # Max YES price (cents)
  max_spread_cents: 3        # Max bid-ask spread
  min_volume: 1000           # Min trading volume

guardian:
  stop_loss_price: 0.75      # Auto-sell positions below this price

execution:
  max_slippage_pct: 0.05     # Reject trade if slippage > 5%
  order_check_interval_seconds: 120
  max_reprice_attempts: 3
  reprice_aggression: 0.02   # Increase limit by 2¢ per reprice
  min_fill_pct_to_keep: 0.25 # Keep partial fills > 25%
  max_order_age_minutes: 60

daemon:
  heartbeat_interval_minutes: 180   # Full pipeline cycle interval
  guardian_interval_minutes: 2      # Guardian-only check interval
  max_consecutive_failures: 5       # Pause threshold
```

## Tech Stack

- **Python 3.12+** with async/await throughout
- **PydanticAI** — LLM agent framework with structured outputs and dependency injection
- **FastAPI** — Dashboard API server
- **httpx** — Async HTTP client for Kalshi API
- **SQLAlchemy (async)** — ORM with async Supabase/PostgreSQL sessions
- **Alembic** — Database migrations (auto-generated, never hand-written)
- **Pydantic** — Data validation, settings management, structured agent outputs
- **Logfire** — Observability, span tracing, and LLM call instrumentation
- **Supabase (PostgreSQL)** — Shared source of truth for all bot state
- **Telegram Bot API** — Real-time alerts and heartbeat notifications

## Project Structure

```
backend/
├── coliseum/
│   ├── __main__.py           # CLI entry point (init, daemon, pipeline, scout, etc.)
│   ├── config.py             # Pydantic Settings singleton (merges .env + config.yaml)
│   ├── llm_providers.py      # Model enums: OpenAI, Anthropic, Fireworks, Grok
│   ├── observability.py      # Logfire initialization
│   ├── pipeline.py           # Full pipeline orchestration (Guardian→Scout→Analyst→Trader→Guardian)
│   ├── runtime.py            # Runtime utilities
│   ├── daemon.py             # Long-lived autonomous daemon with heartbeat loop
│   ├── domain/               # Shared domain models
│   │   ├── opportunity.py    # OpportunitySignal — the core data unit flowing through the pipeline
│   │   ├── portfolio.py      # Portfolio state models
│   │   ├── trade.py          # Trade record models
│   │   └── mappers.py        # Domain ↔ DB mapping utilities
│   ├── memory/               # Prompt memory + journal/error helpers
│   │   ├── context.py        # Kalshi mechanics loader
│   │   ├── decisions.py      # Decision memory helpers
│   │   ├── enums.py          # Memory-related enums (LearningCategory, LearningAddition)
│   │   ├── journal.py        # Journal/error helpers
│   │   └── _io.py            # I/O utilities
│   ├── agents/
│   │   ├── agent_factory.py  # PydanticAI agent construction (OpenAI Responses API + WebSearchTool)
│   │   ├── shared_tools.py   # Tools shared across agents
│   │   ├── scout/            # Market discovery agent
│   │   │   ├── main.py       # Scout orchestration
│   │   │   ├── researcher.py # Web research via WebSearchTool
│   │   │   ├── filters.py    # Market filtering logic (price, spread, volume, close time)
│   │   │   ├── models.py    # ScoutDependencies, ScoutOutput
│   │   │   └── prompts.py   # Scout system prompts
│   │   ├── analyst/          # Research + recommendation agent
│   │   │   ├── main.py       # Analyst orchestration
│   │   │   ├── researcher.py # Analyst web research
│   │   │   ├── web_researcher.py # Web research variant
│   │   │   ├── recommender.py # Flip-risk recommendation sub-agent
│   │   │   ├── market_type_context.py # Market-type-specific context injection
│   │   │   ├── models.py    # AnalystDependencies, ResearcherOutput, RecommenderOutput
│   │   │   ├── shared.py    # Shared analyst utilities
│   │   │   └── prompts.py   # Analyst prompts
│   │   ├── trader/           # Trade execution agent
│   │   │   ├── main.py      # Trader orchestration + Kalshi order placement
│   │   │   ├── models.py    # TraderDependencies, TraderDecision, OrderResult, TraderOutput
│   │   │   └── prompts.py   # Trader prompts
│   │   ├── guardian/         # Position monitoring agent
│   │   │   ├── main.py      # Guardian orchestration (sync + reconcile + stop-loss)
│   │   │   ├── scribe.py    # Learning reflection sub-agent
│   │   │   ├── models.py    # GuardianResult, ReconciliationStats, LearningReflectionOutput
│   │   │   └── prompts.py   # Guardian prompts
│   │   ├── x_sentiment/      # X/Twitter sentiment analysis agent
│   │   └── markets_context/  # Market category context management
│   │       ├── reader.py    # Read market context for prompts
│   │       ├── refresher.py # Background refresh of market categories
│   │       └── seed_data.py # Initial seed data
│   ├── api/
│   │   ├── server.py        # FastAPI dashboard server
│   │   ├── cache.py         # API response caching (TTL-based)
│   │   ├── chart_export.py  # Chart export utilities
│   │   └── parsing.py       # API response parsing
│   ├── services/
│   │   ├── supabase/        # SQLAlchemy models + async DB session
│   │   │   ├── db.py        # Async DB session (get_db_session)
│   │   │   ├── models.py    # SQLAlchemy ORM models
│   │   │   └── repositories/ # Data access layer (opportunities, portfolio, trades, decisions, etc.)
│   │   ├── kalshi/          # Kalshi prediction market API client
│   │   │   ├── auth.py      # RSA-signed request authentication
│   │   │   ├── client.py    # Async httpx client (markets, orders, positions)
│   │   │   ├── config.py    # Kalshi API configuration
│   │   │   ├── exceptions.py # Typed API exceptions
│   │   │   ├── models.py    # Pydantic models (Market, Position, Order, OrderBook, Balance)
│   │   │   └── sync.py      # Portfolio sync logic
│   │   └── telegram/        # Telegram Bot API notifications
│   │       ├── client.py    # Async Telegram client
│   │       ├── config.py    # Telegram configuration
│   │       ├── exceptions.py # Telegram exceptions
│   │       └── models.py    # Pydantic models
│   └── services/exceptions.py # Shared service exceptions
├── alembic/                 # Alembic migration environment
├── alembic.ini              # Alembic configuration
├── config.yaml              # Trading config (risk limits, schedules, LLM provider)
└── requirements.txt         # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```bash
# Supabase (shared source of truth for bot state)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<key>
SUPABASE_DB_URL=postgresql://<user>:<pass>@<host>:5432/postgres

# LLM API keys (at least one provider required)
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
XAI_API_KEY=<key>
FIREWORKS_API_KEY=<key>

# Kalshi trading API
KALSHI_API_KEY=<key>
RSA_PRIVATE_KEY_PATH=./kalshi_private_key.pem

# Observability
LOGFIRE_TOKEN=<token>

# Telegram alerts (optional)
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>
```

### 3. Initialize Data Directory

```bash
python -m coliseum init
```

### 4. Run Database Migrations

```bash
# Ensure SUPABASE_DB_URL is set in .env
alembic current          # Check current migration status
alembic upgrade head     # Apply all pending migrations
```

Schema changes require Alembic — always use `alembic revision --autogenerate -m "description"` and never hand-write migrations.

### 5. Configure Trading Parameters

Edit `backend/config.yaml` to set risk limits, LLM provider, and agent behavior. **Always set `trading.paper_mode: true`** when testing to avoid placing real orders on Kalshi.

### 6. Run the Pipeline

```bash
# Run one full pipeline cycle (for testing/debug)
python -m coliseum pipeline

# Start the autonomous daemon (production)
python -m coliseum daemon

# Start the dashboard API only
python -m coliseum api
```

See the CLI commands section below for the full list of commands.

## CLI Commands

All commands are run from the `backend/` directory with the venv activated:

```bash
python -m coliseum init                   # Initialize data directory
python -m coliseum daemon                 # Start trading daemon + dashboard (production)
python -m coliseum pipeline               # Run full pipeline once (testing/debug)
python -m coliseum api                    # Start dashboard API only (no daemon)
python -m coliseum scout                  # Run Scout agent manually
python -m coliseum analyst --id <id>      # Run Analyst for a specific opportunity
python -m coliseum trader --id <id>       # Run Trader for a specific opportunity
python -m coliseum guardian               # Run Guardian reconciliation
python -m coliseum status                 # Portfolio status summary
python -m coliseum config                 # Display merged configuration
```

Database migration commands:

```bash
alembic current                           # Show current DB migration revision
alembic upgrade head                      # Apply all pending migrations
alembic upgrade head --sql                # Preview migration SQL without applying
```

## Using LLM Agents

Agents are constructed via `coliseum/agents/agent_factory.py` which creates PydanticAI agents with structured output and optional web search capability. The active LLM provider is configured in `config.yaml` under `llm.provider`.

```python
from coliseum.llm_providers import OpenAIModel, get_model_string

# Get the API model string for any supported model
model = get_model_string(OpenAIModel.GPT_5_MINI)  # "openai-responses:gpt-5-mini"
```

Available providers and models (see `coliseum/llm_providers.py`):

- **OpenAI**: GPT-5.4, GPT-5.2, GPT-5-mini, GPT-5-nano (`openai-responses:` prefix)
- **Anthropic**: Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 (`anthropic:` prefix)
- **Fireworks**: Llama 3.3 70B, Llama 3.1 405B/70B/8B, DeepSeek V3.2, Kimi K2.5 (`fireworks:` prefix)
- **xAI**: Grok 4.20 reasoning/non-reasoning/multi-agent (`xai:` prefix)

Agents that perform web research (Scout Researcher, Analyst Researcher) use the OpenAI Responses API with `WebSearchTool`. All agents use Pydantic `result_type` for structured output.

## Development Workflow

### Adding Database Models

1. Update the SQLAlchemy model in `coliseum/services/supabase/models.py`
2. Generate an Alembic migration: `alembic revision --autogenerate -m "add X model"`
3. Review the generated migration file in `alembic/versions/`
4. Apply the migration: `alembic upgrade head`
5. Add a repository in `coliseum/services/supabase/repositories/` for data access

**Important**: Never hand-write Alembic migrations. Always use `--autogenerate` and review the output.

### Adding API Routes

1. Add route handlers in `coliseum/api/server.py`
2. Use `coliseum/api/cache.py` for TTL-based response caching
3. Use `coliseum/api/parsing.py` for API response parsing utilities

### Adding a New Agent

1. Create a new directory under `coliseum/agents/<agent_name>/`
2. Define Pydantic models in `models.py` (dependencies, output)
3. Write prompts in `prompts.py`
4. Implement orchestration in `main.py`
5. Register the agent in the pipeline (`coliseum/pipeline.py`) if it participates in the trading cycle

## Architecture Notes

### Supabase as Source of Truth

All bot state — opportunities, portfolio, positions, trades, decisions, run cycles, and learnings — is persisted to Supabase (PostgreSQL). This enables multiple bot instances to share state and stay in sync. Database access uses async SQLAlchemy sessions via `coliseum/services/supabase/db.py`:

```python
from coliseum.services.supabase.db import get_db_session

async with get_db_session() as session:
    # ... query or persist data
```

### Paper Mode

**Always** run with `trading.paper_mode: true` in `config.yaml` when testing. This prevents real-money order placement on Kalshi. The Trader agent will simulate orders and report `execution_status: "paper"` instead of interacting with the live API.

### Logfire Observability

All pipeline spans and LLM calls are automatically instrumented by Logfire, capturing:
- Pipeline cycle spans (guardian, scout, analyst, trader)
- Agent inputs, outputs, and structured results
- Token counts, costs, and latency
- Error traces and transient retry logs

### Telegram Alerts

When configured, the daemon sends:
- **Heartbeat summaries** — After each pipeline cycle (status, uptime, cycle count)
- **Escalation alerts** — When the daemon pauses due to consecutive failures
- **Trade notifications** — Real-time alerts on trade execution via the Trader's `tldr` field

## Troubleshooting

### Database Connection Issues

- Ensure `SUPABASE_DB_URL` is a valid Postgres connection string in `.env`
- SSL mode is handled automatically by settings
- Check that your Supabase project is active and not paused

### LLM API Errors

- Ensure the API key for your configured `llm.provider` is set in `.env`
- Check `python -m coliseum config` to verify the merged configuration
- Transient errors (500/502/503/429) are retried automatically by the pipeline

### Kalshi API Errors

- Ensure `KALSHI_API_KEY` and `RSA_PRIVATE_KEY_PATH` are set in `.env`
- Verify the RSA key file exists and is readable
- Check `python -m coliseum status` for portfolio state

### Import Errors

- Ensure you're in the `backend/` directory
- Activate the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

The core trading pipeline is fully functional. Potential areas for expansion:

1. **Additional market sources** — Integrate prediction markets beyond Kalshi (Polymarket, Metaculus)
2. **Strategy diversification** — Add new agent strategies beyond the current Scout→Analyst→Trader flow
3. **Risk management** — Enhanced position sizing, portfolio-level risk limits, correlation analysis
4. **Backtesting** — Historical performance simulation using resolved market data
5. **Dashboard enhancements** — Richer analytics, P&L charts, and agent decision drill-downs

## Resources

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [Kalshi API Documentation](https://trading-api.kalshi.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Logfire Documentation](https://logfire.pydantic.dev/)
- [Supabase Documentation](https://supabase.com/docs)
