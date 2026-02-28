# AGENTS.md

## Spec Version

- Current version: `1.1.0`
- Versioning scheme: `MAJOR.MINOR.PATCH` (semantic versioning)
- Keep `CLAUDE.md` and `AGENTS.md` on the exact same version at all times

> **CRITICAL**: Always activate the venv before running backend code:
> ```bash
> cd backend && source venv/bin/activate
> ```

## What is Coliseum

Autonomous prediction market trading system using PydanticAI agents on Kalshi. Agents: **Scout** (discovery) → **Analyst** (research) → **Trader** (execution) ← **Guardian** (monitoring).

## Project Structure

```
backend/
├── coliseum/
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Settings via get_settings()
│   ├── llm_providers.py     # Model enums: OpenAIModel, AnthropicModel, FireworksModel
│   ├── observability.py     # Logfire initialization
│   ├── pipeline.py          # Full pipeline orchestration
│   ├── scheduler.py         # APScheduler job definitions
│   ├── agents/
│   │   ├── agent_factory.py # Agent construction helpers
│   │   ├── shared_tools.py  # Tools shared across agents
│   │   ├── scout/           # Market discovery agent
│   │   ├── analyst/         # Research + recommendation agent
│   │   │   ├── researcher/  # Web research sub-agent
│   │   │   └── recommender/ # EV/edge recommendation sub-agent
│   │   │       └── calculations.py  # Edge/EV/Kelly math
│   │   ├── trader/          # Trade execution agent
│   │   └── guardian/        # Position monitoring agent
│   ├── api/
│   │   └── server.py        # FastAPI dashboard server
│   ├── storage/
│   │   ├── state.py         # Portfolio state (state.yaml)
│   │   ├── files.py         # Opportunity/position file ops
│   │   └── sync.py          # State reconciliation helpers
│   └── services/
│       ├── kalshi/          # Kalshi API client
│       ├── exa/             # Exa AI web search client
│       └── telegram/        # Telegram notifications
├── data/
│   ├── config.yaml          # Trading config (risk limits, schedules)
│   ├── state.yaml           # Portfolio state (source of truth)
│   └── opportunities/       # Opportunity markdown files
├── test_data/
│   ├── config.yaml          # Test environment config
│   └── state.yaml           # Test environment state
└── requirements.txt
```

## Essential Commands

```bash
python -m coliseum init                          # Initialize data directory
python -m coliseum run                           # Start autonomous system (scheduler)
python -m coliseum run --once                    # Run full pipeline once then exit
python -m coliseum scout                         # Run market scan manually
python -m coliseum analyst --opportunity-id <id> # Run Analyst pipeline manually
python -m coliseum trader --opportunity-id <id>  # Run Trader agent manually
python -m coliseum guardian                      # Run Guardian reconciliation manually
python -m coliseum status                        # Portfolio status
python -m coliseum config                        # Display merged configuration
python -m coliseum serve                         # Start dashboard API server (port 8000)
# No tests are set up in this repository - do not use pytest
```

## Code Patterns

**Configuration:**
```python
from coliseum.config import get_settings
settings = get_settings()  # Singleton, loads .env + data/config.yaml
```

**LLM Models:**
```python
from coliseum.llm_providers import OpenAIModel, AnthropicModel, get_model_string
model = get_model_string(OpenAIModel.GPT_5_MINI)  # "openai-responses:gpt-5-mini"
```

**File writes must be atomic** (use tempfile + shutil.move).

## Code Style

- Type hints required on all functions
- Pydantic models for all structured data
- One-line docstrings (no verbose Args/Returns)
- **Never** use `# ====` section separators
- Inline comments: only for "why", never "what"

## Critical Rules

1. **Paper mode first**: `trading.paper_mode: true` in config.yaml
2. **Limit orders only**: Never use market orders
3. **state.yaml is source of truth**: Only one process writes to it
4. **RSA key for Kalshi**: Set `RSA_PRIVATE_KEY_PATH` in .env
5. **Config/State sync**: After any structural change to `config.py` (Settings models) or `state.py` (state models), update both the production data files (`backend/data/config.yaml`, `backend/data/state.yaml`) and the test data files (`backend/test_data/config.yaml`, `backend/test_data/state.yaml`) to match the new schema.

## Bash Guidelines

- Never pipe through `head`, `tail`, `less` (causes buffering issues)
- Use command flags instead: `git log -n 10` not `git log | head -10`

## Versioning Rules

Every content change to this file requires a version bump. Choose the bump type based on impact:

- **MAJOR** (`X.0.0`): Breaking policy changes or removed guidance that can change established agent/user workflows.
- **MINOR** (`x.Y.0`): New features, new required workflows, new commands, new constraints, or expanded capabilities.
- **PATCH** (`x.y.Z`): Clarifications, wording updates, typo fixes, formatting-only changes, and non-breaking refinements.

Operational rules:

1. If multiple change types are included in one edit, apply only the highest required bump.
2. Do not skip versions.
3. Keep version numbers identical in `CLAUDE.md` and `AGENTS.md`.
4. When uncertain between two bump levels, choose the higher one.
