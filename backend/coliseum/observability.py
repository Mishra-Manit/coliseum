"""Logfire cloud observability initialization and instrumentation."""

import logging
from decimal import Decimal
from logging.config import dictConfig

import logfire
from genai_prices import types as genai_types
from genai_prices.data_snapshot import get_snapshot, set_custom_snapshot

from coliseum import __version__
from coliseum.config import Settings

logger = logging.getLogger(__name__)

_logfire_initialized = False


def initialize_logfire(settings: Settings) -> None:
    """
    Initialize Logfire with comprehensive instrumentation.

    Idempotent — safe to call multiple times; only the first call takes effect.
    Must be called at application startup, BEFORE any agent code runs.
    """
    global _logfire_initialized
    if _logfire_initialized:
        return
    _logfire_initialized = True
    if not settings.logfire_token:
        logger.warning("Logfire token not set - observability disabled")
        logfire.configure(send_to_logfire=False)
        return

    try:
        if settings.trading.paper_mode:
            environment = "paper"
        else:
            environment = "live"

        # 1. Configure Logfire with cloud token
        logfire.configure(
            token=settings.logfire_token,
            service_name="coliseum",
            service_version=__version__,
            environment=environment,
            console=False,
        )

        # 2. Register custom model pricing for models not yet in genai-prices
        _register_custom_pricing()

        # 3. Instrument PydanticAI agents (Scout, Analyst, Trader, Guardian)
        logfire.instrument_pydantic_ai()

        # 4. Instrument OpenAI SDK (GPT models, WebSearchTool)
        logfire.instrument_openai()

        # 5. Instrument HTTPX (Kalshi API, Exa API)
        logfire.instrument_httpx()

        # 6. Bridge Python logging to Logfire
        # Add LogfireLoggingHandler to root logger
        root_logger = logging.getLogger()
        logfire_handler = logfire.LogfireLoggingHandler()
        root_logger.addHandler(logfire_handler)

        logging.getLogger("httpx").setLevel(logging.WARNING)

        # 7. Collect system metrics (CPU, memory, disk) - optional
        try:
            logfire.instrument_system_metrics()
        except Exception as metrics_error:
            logger.debug(f"System metrics instrumentation skipped: {metrics_error}")

        logger.info("✓ Logfire cloud tracking initialized")

    except Exception as e:
        logger.warning(f"Failed to initialize Logfire: {e}")
        # Continue running - observability is optional


def _register_custom_pricing() -> None:
    """Inject pricing for models not yet in the genai-prices database."""
    snap = get_snapshot()

    grok_420_price = genai_types.ModelPrice(
        input_mtok=Decimal("2"),
        cache_read_mtok=Decimal("0.2"),
        output_mtok=Decimal("6"),
    )
    custom_models = [
        genai_types.ModelInfo(
            id="grok-4.20-0309-reasoning",
            match=genai_types.ClauseEquals(equals="grok-4.20-0309-reasoning"),
            prices=grok_420_price,
        ),
        genai_types.ModelInfo(
            id="grok-4.20-0309-non-reasoning",
            match=genai_types.ClauseEquals(equals="grok-4.20-0309-non-reasoning"),
            prices=grok_420_price,
        ),
    ]

    for provider in snap.providers:
        if provider.id != "x-ai":
            continue
        existing_ids = {m.id for m in provider.models}
        added = []
        for model in custom_models:
            if model.id not in existing_ids:
                provider.models.append(model)
                added.append(model.id)
        if added:
            provider._lookup_cache = {}
            snap._lookup_cache = {}
            set_custom_snapshot(snap)
            logger.info(f"Registered custom pricing for: {', '.join(added)}")
        break
