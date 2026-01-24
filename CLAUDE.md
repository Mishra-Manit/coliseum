# CLAUDE.md

> **CRITICAL**: You must ALWAYS activate the virtual environment before running any code in the `backend/` directory. 
> To do this, run `source venv/bin/activate` from inside the `backend/` directory.
>
> Example: 
> ```bash
> cd backend
> source venv/bin/activate
> python test_storage_integration.py
> ```

This file provides project-specific context for AI coding assistants working with the Coliseum codebase.

## Project Overview

**Coliseum** is an autonomous quantitative trading system that deploys AI agents to trade on [Kalshi](https://kalshi.com) prediction markets. The system operates as a fully autonomous pipeline where specialized PydanticAI agents collaborate to research events, identify opportunities, execute positions, and monitor the portfolio—all with minimal human intervention.

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Autonomous Operation** | Agents run 24/7 with minimal human oversight |
| **Research-Driven** | Every trade backed by deep, grounded research (OpenAI WebSearchTool) |
| **Risk-First** | Hard limits and circuit breakers prevent catastrophic losses |
| **Transparent** | Full audit trail of every decision and trade |
| **File-Based Storage** | Human-readable YAML/Markdown, git-friendly, no database |

---

## Technology Stack

### Backend (`backend/`)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Agent Framework** | PydanticAI | Type-safe agents with structured outputs |
| **Language** | Python 3.11+ | Agent execution, CLI |
| **Storage** | YAML + Markdown + JSONL | Human-readable persistence in `data/` |
| **State** | `state.yaml` | Single source of truth for portfolio |
| **Scheduler** | APScheduler | In-process scheduled jobs (no Celery/Redis) |
| **Observability** | Pydantic Logfire | LLM tracing, performance monitoring |

### AI/ML Services

| Service | Provider | Use Case |
|---------|----------|----------|
| **Primary LLM** | Anthropic (Claude Sonnet) | Agent reasoning, analysis |
| **Fast LLM** | Anthropic (Claude Haiku) | Quick decisions, monitoring |
| **Research** | OpenAI (GPT-5-Mini with WebSearchTool) | Market research with web search |
| **Real-time Search** | Perplexity API | Breaking news, current events |

### External APIs

| API | Purpose |
|-----|---------|
| **Kalshi Markets** | Read market data (public) |
| **Kalshi Trading** | Execute trades (API Key + Private Key auth) |
| **OpenAI** | Research with web search (GPT-5-Mini) |
| **Telegram Bot** | Real-time alerts and notifications |

---

## Directory Structure

```
backend/
├── coliseum/                 # Main agent package
│   ├── __main__.py           # CLI entry point
│   ├── config.py             # Load config.yaml + .env
│   ├── scheduler.py          # APScheduler setup
│   │
│   ├── agents/               # PydanticAI agent definitions
│   │   ├── scout.py          # Market discovery agent
│   │   ├── analyst.py        # Research + recommendation agent
│   │   ├── trader.py         # Trade execution agent
│   │   ├── guardian.py       # Position monitoring agent
│   │   ├── risk.py           # Risk management logic
│   │   └── calculations.py   # Edge/EV/Kelly calculations
│   │
│   ├── storage/              # File-based persistence
│   │   ├── state.py          # Portfolio state (state.yaml)
│   │   └── files.py          # Atomic file operations
│   │
│   └── services/             # External API clients
│       ├── kalshi.py         # Kalshi API (public + trading)
│       └── exa/              # Exa AI (deprecated - not currently used)
│           └── ...           # Legacy code maintained for reference
│
├── data/                     # Runtime data (git-ignored portions)
│   ├── config.yaml           # System configuration
│   ├── state.yaml            # Portfolio state (source of truth)
│   ├── opportunities/        # Opportunity files (progressive enrichment)
│   ├── positions/open/       # Active positions
│   ├── positions/closed/     # Historical positions
│   └── trades/               # JSONL trade ledger
│
├── mess_around/              # Exploration scripts (preserved)
│   └── explore_kalshi_api.py
│
└── requirements.txt
```

---

## Development Commands

### Environment Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # REQUIRED before any backend work
pip install -r requirements.txt
```

> **IMPORTANT**: Always activate the virtual environment before running any backend code.

### Running the System

```bash
# Initialize data directory structure
python -m coliseum init

# Start autonomous trading system
python -m coliseum run

# Run individual agents manually
python -m coliseum scout --scan-type full
python -m coliseum scout --scan-type quick
python -m coliseum analyst --opportunity-id opp_abc123
python -m coliseum guardian --check-positions
python -m coliseum trader --recommendation-id rec_abc123

# Portfolio management
python -m coliseum portfolio status
python -m coliseum positions list
python -m coliseum positions close TICKER-ABC-123

# Configuration
python -m coliseum config show
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_risk.py -v

# Run with coverage
pytest --cov=coliseum
```

---

## Agent Architecture

### The Four Agents

```
Scout ──(NewOpportunity)──▶ Analyst ──(TradeRecommendation)──▶ Trader
                                                                  │
                              ┌───────────────────────────────────┘
                              │
Guardian ◀──(OpenPosition)────┘
    │
    └──(ExitSignal)──▶ Trader ──(ClosePosition)──▶ Kalshi
```

| Agent | Mission | Schedule |
|-------|---------|----------|
| **Scout** 🔍 | Discover high-quality opportunities from Kalshi | Every 15-60 min |
| **Analyst** 📊 | Research opportunities, generate trade recommendations | On-demand |
| **Trader** 💰 | Execute trades with risk management | On-demand |
| **Guardian** 🛡️ | Monitor positions, trigger exits | Every 15-30 min |

### PydanticAI Agent Pattern

When creating or modifying agents, follow this structure:

```python
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# 1. Define structured output
class AgentOutput(BaseModel):
    """Typed output from the agent."""
    result: str
    confidence: float

# 2. Define dependencies (injected context)
class AgentDeps(BaseModel):
    kalshi_client: KalshiAPI
    config: AgentConfig

# 3. Create the agent
agent = Agent(
    model="anthropic:claude-sonnet-4-20250514",
    result_type=AgentOutput,
    deps_type=AgentDeps,
    system_prompt="Your system prompt here...",
)

# 4. Define tools with @agent.tool decorator
@agent.tool
async def my_tool(ctx: RunContext[AgentDeps], param: str) -> dict:
    """Tool description for the LLM."""
    return await ctx.deps.kalshi_client.some_method(param)
```

---

## Risk Management Rules

### Hard Limits (Never Bypass)

| Limit | Threshold | Action |
|-------|-----------|--------|
| **Max Position Size** | 10% of portfolio | Reject trade |
| **Max Single Trade** | $1,000 | Reject trade |
| **Max Open Positions** | 10 | Reject new positions |
| **Daily Loss Limit** | 5% of portfolio | Halt trading for day |
| **Min Edge Threshold** | 5% | Skip trade |
| **Min EV Threshold** | 10% | Skip trade |

### Order Execution

> **CRITICAL**: Never use market orders. All trades MUST use limit orders with slippage protection.

- Calculate slippage before every trade
- Reject trade if slippage destroys edge
- Use "working order" loop: place → wait → reprice → cancel after 3 attempts

---

## Code Style Guidelines

### Python Conventions

- **Type hints**: Required on all function signatures
- **Pydantic models**: Use for all structured data (configs, API responses, agent outputs)
- **Async**: Prefer `async/await` for I/O operations
- **Docstrings**: Google-style docstrings for public functions

### File Operations

Always use atomic writes to prevent corruption:

```python
import tempfile
import shutil

def save_state(state: dict) -> None:
    """Atomically save state to prevent corruption."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        yaml.dump(state, f)
        temp_path = f.name
    shutil.move(temp_path, DATA_DIR / "state.yaml")  # Atomic rename
```

### Trade Logging

Append trades to JSONL ledger (never overwrite):

```python
def log_trade(trade: dict) -> None:
    today = date.today().isoformat()
    ledger_path = DATA_DIR / "trades" / f"{today}.jsonl"
    with open(ledger_path, "a") as f:
        f.write(json.dumps(trade) + "\n")
```

---

## Key Files Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `backend/DESIGN.md` | Full system specification | Before any architectural changes |
| `backend/data/config.yaml` | Trading configuration | Before modifying risk limits |
| `backend/data/state.yaml` | Live portfolio state | Read-only for status checks |
| `backend/coliseum/agents/risk.py` | Risk validation logic | Before any trade execution changes |

---

## Common Patterns

### Loading Configuration

```python
from coliseum.config import load_config, load_state

config = load_config()  # From data/config.yaml
state = load_state()    # From data/state.yaml
```

---

## Warnings & Gotchas

### Kalshi API Authentication

The trading API requires RSA signature authentication. The private key must be:
- PEM format
- Path specified in `.env` as `KALSHI_PRIVATE_KEY_PATH`
- Never committed to git

### Paper Trading Mode

Always test in paper mode first:

```yaml
# data/config.yaml
trading:
  paper_mode: true  # ALWAYS start with this
```

### State File Concurrency

The `state.yaml` file is the single source of truth. If running multiple processes:
- Only ONE process should write to `state.yaml`
- Use file locking if parallel access is needed
---

## Documentation & Research

Before implementing features that interact with external libraries or APIs:

1. **Read `backend/DESIGN.md`** for the canonical specification
2. **Check existing implementations** in `coliseum/services/` for patterns
3. **Reference Kalshi API docs** for market/trading endpoints
4. **Use Exa AI documentation** for research integration patterns

---

## Testing Philosophy

| Test Type | Location | Purpose |
|-----------|----------|---------|
| **Unit tests** | `tests/test_*.py` | Isolated function testing |
| **Integration tests** | `tests/integration/` | API client testing (with mocks) |
| **Paper trading** | Live system | 2+ weeks before going live |

Before going live:
- [ ] Paper trading profitable for 2+ weeks
- [ ] Risk limits tested with edge cases
- [ ] Manual override tested
