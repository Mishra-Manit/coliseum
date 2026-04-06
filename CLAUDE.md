# CLAUDE.md

## Spec Version

- Current version: `1.8.0`
- Versioning scheme: `MAJOR.MINOR.PATCH` (semantic versioning)

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
│   ├── daemon.py            # Long-lived autonomous daemon with heartbeat loop
│   ├── memory/              # Prompt memory + journal/error helpers
│   ├── agents/
│   │   ├── agent_factory.py # Agent construction helpers
│   │   ├── shared_tools.py  # Tools shared across agents
│   │   ├── scout/           # Market discovery agent
│   │   ├── analyst/         # Research + recommendation agent
│   │   │   ├── researcher/  # Web research sub-agent
│   │   │   └── recommender/ # Flip-risk recommendation sub-agent
│   │   ├── trader/          # Trade execution agent
│   │   └── guardian/        # Position monitoring agent
│   ├── api/
│   │   └── server.py        # FastAPI dashboard server
│   ├── services/
│   │   ├── supabase/        # SQLAlchemy models + async DB session
│   │   ├── kalshi/          # Kalshi API client
│   │   ├── exa/             # Exa AI web search client
│   │   └── telegram/        # Telegram notifications
│   ├── storage/
│   │   ├── state.py         # Legacy/local portfolio helpers being replaced
│   │   ├── files.py         # Legacy/local opportunity file ops being replaced
│   │   └── sync.py          # Legacy/local reconciliation helpers being replaced
├── alembic/                 # Alembic migration environment
├── alembic.ini              # Alembic configuration
├── data/
│   ├── config.yaml          # Trading config (risk limits, schedules)
│   ├── state.yaml           # Legacy local state file (being phased out)
│   └── opportunities/       # Legacy local opportunity files (being phased out)
└── requirements.txt
```

## Essential Commands

```bash
python -m coliseum init                   # Initialize data directory
python -m coliseum daemon                 # Start trading daemon + dashboard (production)
python -m coliseum pipeline               # Run full pipeline once (testing/debug)
python -m coliseum api                    # Start dashboard API only (no daemon)
python -m coliseum scout                  # Run Scout manually
python -m coliseum analyst --id <id>      # Run Analyst pipeline manually
python -m coliseum trader --id <id>       # Run Trader agent manually
python -m coliseum guardian               # Run Guardian reconciliation manually
python -m coliseum status                 # Portfolio status
python -m coliseum config                 # Display merged configuration
alembic current                           # Show current DB migration revision
alembic upgrade head                      # Apply all pending DB migrations
alembic upgrade head --sql                # Preview migration SQL without applying
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

**Database access:**
```python
from coliseum.services.supabase.db import get_db_session

async with get_db_session() as session:
    ...
```

**DB schema changes must go through Alembic**:
1. Update SQLAlchemy models in `backend/coliseum/services/supabase/models.py`
2. Generate or edit the Alembic revision in `backend/alembic/versions/`
3. Apply with `alembic upgrade head`

## Code Style

- Type hints required on all functions
- Pydantic models for all structured data
- One-line docstrings (no verbose Args/Returns)
- **Never** use `# ====` section separators
- Inline comments: only for "why", never "what"
- **No inline imports**: All imports must be at the top of the file. Never place `import` or `from ... import` inside functions, methods, or conditionals. Always assume imports will succeed.

## Critical Rules

1. **Paper mode first**: `trading.paper_mode: true` in config.yaml
2. **Limit orders only**: Never use market orders
3. **Supabase is now the shared source of truth for bot state**: opportunities, portfolio state, positions, trades, decisions, and run-cycle data should persist online so multiple instances stay in sync
4. **RSA key for Kalshi**: Set `RSA_PRIVATE_KEY_PATH` in .env
5. **Alembic required for schema changes**: After any structural change to `backend/coliseum/services/supabase/models.py`, generate an Alembic migration and keep `online_db.md` in sync
6. **Never hand-write Alembic migrations**: Always use `alembic revision --autogenerate -m "description"` to generate migration files, then review the output. Never create migration files manually.
7. **Pipeline test always in paper mode**: After any backend pipeline change, validate by running `python -m coliseum pipeline`. **Never** set `trading.paper_mode: false` when testing — doing so places real-money orders on Kalshi. Confirm `paper_mode: true` in `backend/data/config.yaml` before every test run.
8. **Use the correct Supabase Postgres URL**: `SUPABASE_DB_URL` must be a working Postgres connection string in `.env` before running Alembic commands

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
3. When uncertain between two bump levels, choose the higher one.
5. Leave all changes in the main branch for me to review and merge; do not self-commit after running subagents.
