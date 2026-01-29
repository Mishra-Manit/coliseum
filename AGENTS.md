# AGENTS.md

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
│   ├── __main__.py          # CLI: python -m coliseum {init|run|scout|analyst|trader|status|config}
│   ├── config.py            # Settings via get_settings()
│   ├── llm_providers.py     # Model enums: OpenAIModel, AnthropicModel, FireworksModel
│   ├── agents/
│   │   ├── scout/           # Market discovery agent
│   │   ├── analyst/         # Research + recommendation agent
│   │   ├── trader/          # Trade execution agent
│   │   ├── guardian/        # Position monitoring agent
│   │   └── calculations.py  # Edge/EV/Kelly math
│   ├── storage/
│   │   ├── state.py         # Portfolio state (state.yaml)
│   │   ├── memory.py        # Agent memory log (memory.md)
│   │   └── files.py         # Opportunity/position file ops
│   └── services/
│       ├── kalshi/          # Kalshi API client
│       └── telegram/        # Telegram notifications
├── data/
│   ├── config.yaml          # Trading config (risk limits, schedules)
│   ├── state.yaml           # Portfolio state (source of truth)
│   ├── memory.md            # Agent trading memory
│   └── opportunities/       # Opportunity markdown files
└── requirements.txt
```

## Essential Commands

```bash
python -m coliseum init      # Initialize data directory
python -m coliseum run       # Start autonomous system
python -m coliseum scout     # Run market scan
python -m coliseum status    # Portfolio status
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

## Bash Guidelines

- Never pipe through `head`, `tail`, `less` (causes buffering issues)
- Use command flags instead: `git log -n 10` not `git log | head -10`