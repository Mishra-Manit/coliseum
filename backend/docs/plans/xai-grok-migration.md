# Plan: xAI Grok Provider Migration

**Date**: 2026-04-07
**Status**: Approved (grill-me complete)
**Goal**: Add xAI Grok 4.20 as an alternative LLM provider, switchable via `config.yaml`, while preserving all existing OpenAI code paths.

---

## 1. Configuration Layer

### 1a. `config.yaml` -- new `llm` section

```yaml
llm:
  provider: "xai"  # or "openai" (default)
```

If the `llm` section is missing entirely, default to `"openai"` so existing deployments keep working.

### 1b. `config.py` -- new `LlmConfig` model

```python
class LlmConfig(BaseModel):
    provider: Literal["openai", "xai"] = "openai"
```

- Add `llm: LlmConfig = Field(default_factory=LlmConfig)` to `Settings`
- Add `xai_api_key: str = ""` to `Settings` (loaded from `XAI_API_KEY` env var)
- Add `"llm"` to the `load_yaml_config()` section merge list

---

## 2. LLM Providers Enum

### `llm_providers.py` -- add xAI model enum

```python
class GrokModel(StrEnum):
    GROK_4_20 = "grok-4.20"
```

Update `get_model_string()` to handle `GrokModel`:

```python
elif isinstance(model, GrokModel):
    return f"xai:{model.value}"
```

---

## 3. Agent Factory (`agent_factory.py`)

This is the core of the migration. Split into provider-specific creation paths.

### 3a. New xAI provider singleton

```python
from pydantic_ai.models.xai import XaiModel as PydanticAIXaiModel, XaiModelSettings
from pydantic_ai.providers.xai import XaiProvider

_xai_provider: XaiProvider | None = None

def _get_xai_provider() -> XaiProvider:
    global _xai_provider
    if _xai_provider is None:
        from xai_sdk import AsyncClient
        settings = get_settings()
        _xai_provider = XaiProvider(xai_client=AsyncClient(api_key=settings.xai_api_key))
    return _xai_provider
```

Rename existing `_get_provider()` to `_get_openai_provider()` for clarity.

### 3b. Provider-specific agent creation

```python
def _create_openai_agent(...) -> Agent[DepsT, OutputT]:
    """Existing OpenAI logic — unchanged."""
    # Current create_agent() body with OpenAIResponsesModel / OpenAIChatModel

def _create_xai_agent(...) -> Agent[DepsT, OutputT]:
    """xAI Grok agent creation."""
    # Uses PydanticAIXaiModel("grok-4.20", provider=_get_xai_provider())
    # XaiModelSettings(timeout=300) — no reasoning_effort (not supported)
    # builtin_tools passed through as-is (WebSearchTool works natively)
```

### 3c. Unified `create_agent()` entry point

```python
def create_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None = None,
    reasoning_effort: str = "medium",        # OpenAI only, ignored on xAI
    builtin_tools: list[Any] | None = None,
    prepend_mechanics: bool = True,
    use_responses_api: bool = True,          # OpenAI only, ignored on xAI
) -> Agent[DepsT, OutputT]:
    settings = get_settings()
    if settings.llm.provider == "xai":
        return _create_xai_agent(prompt, output_type, deps_type, builtin_tools, prepend_mechanics)
    else:
        return _create_openai_agent(prompt, output_type, deps_type, reasoning_effort, builtin_tools, prepend_mechanics, use_responses_api)
```

---

## 4. Scout Researcher (`scout/researcher.py`)

The scout researcher currently bypasses `create_agent()` with manual OpenAI construction (GPT-5.2, reasoning_effort='low').

### Changes

- **OpenAI path**: completely untouched, keeps manual construction
- **xAI path**: route through `create_agent()` factory, uses `grok-4.20` with `WebSearchTool()`
- Add a provider check in `get_web_researcher()`:

```python
def get_web_researcher() -> Agent[None, str]:
    global _web_researcher
    if _web_researcher is None:
        settings = get_settings()
        if settings.llm.provider == "xai":
            _web_researcher = create_agent(
                prompt=_WEB_RESEARCHER_PROMPT,
                output_type=str,
                builtin_tools=[WebSearchTool()],
                prepend_mechanics=False,
            )
        else:
            # Existing manual OpenAI construction (GPT-5.2, reasoning_effort='low')
            ...
    return _web_researcher
```

---

## 5. Search Tooling

- `WebSearchTool()` (PydanticAI builtin) works on both providers
  - On OpenAI: maps to OpenAI's web search
  - On xAI: PydanticAI translates it to xAI's native `web_search()` server-side tool automatically
- X Search: **skipped for now** (PydanticAI v1.72.0 does not support it as a builtin tool yet)
- Exa: already removed from codebase

---

## 6. Agent-by-Agent Impact

| Agent | Search Tools | OpenAI Changes | xAI Behavior |
|-------|-------------|----------------|--------------|
| Scout main | None | None | Routes through `_create_xai_agent`, grok-4.20 |
| Scout researcher | `WebSearchTool()` | None (manual GPT-5.2 preserved) | Routes through factory, grok-4.20 |
| Analyst researcher | `WebSearchTool()` | None | Routes through `_create_xai_agent`, grok-4.20 |
| Analyst recommender | None | None | Routes through `_create_xai_agent`, grok-4.20 |
| Trader | None | None | Routes through `_create_xai_agent`, grok-4.20 |
| Guardian scribe | None | None | Routes through `_create_xai_agent`, grok-4.20 |

---

## 7. What Does NOT Change

- All OpenAI code paths (fully preserved, no modifications)
- Agent system prompts and prompt templates
- Tool registration via `AgentFactory.register_tools_fn`
- `AgentFactory` singleton pattern
- `prepend_mechanics` behavior
- Config sections other than new `llm`
- Database schema (no Alembic migration needed)
- Pipeline orchestration (`pipeline.py`, `daemon.py`)

---

## 8. New Dependencies

```
pip install "pydantic-ai-slim[xai]"
# or: pip install xai-sdk
```

Add `xai-sdk` to `requirements.txt`.

---

## 9. Environment Variables

| Variable | Required When | Description |
|----------|--------------|-------------|
| `OPENAI_API_KEY` | `provider: "openai"` | Existing, unchanged |
| `XAI_API_KEY` | `provider: "xai"` | New, xAI API key from console.x.ai |

---

## 10. Files Modified

| File | Change |
|------|--------|
| `config.yaml` | Add `llm.provider` section |
| `coliseum/config.py` | Add `LlmConfig`, `xai_api_key`, merge `llm` from YAML |
| `coliseum/llm_providers.py` | Add `GrokModel` enum, update `get_model_string()` |
| `coliseum/agents/agent_factory.py` | Add `_get_xai_provider()`, `_create_xai_agent()`, rename `_get_provider()` to `_get_openai_provider()`, update `create_agent()` dispatch |
| `coliseum/agents/scout/researcher.py` | Add provider-conditional path in `get_web_researcher()` |
| `requirements.txt` | Add `xai-sdk` |

---

## 11. Key Technical Notes

- **grok-4.20 is always a reasoning model** -- there is no non-reasoning mode, no `reasoning_effort` parameter
- **`presencePenalty`, `frequencyPenalty`, `stop` are not supported** on Grok reasoning models
- **PydanticAI v1.72.0 has a dedicated `XaiModel`** -- the old `GrokProvider` (OpenAI-compat) is deprecated
- **WebSearchTool works natively on xAI** through PydanticAI's translation layer
- **X Search is not yet supported** in PydanticAI builtins (can be added as a single-line change when PydanticAI ships it)
- **2M token context window** on Grok 4.20 (vs 128K on GPT-5.4)
- **Pricing**: $2/M input, $6/M output (cheaper than GPT-5.4's $2.50/$14)

---

## 12. Testing

1. Set `llm.provider: "xai"` in `config.yaml`
2. Set `XAI_API_KEY` in `.env`
3. Confirm `trading.paper_mode: true`
4. Run `python -m coliseum pipeline` and verify all agents execute without errors
5. Switch back to `llm.provider: "openai"` and verify no regressions
