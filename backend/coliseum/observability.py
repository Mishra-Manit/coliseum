"""Logfire cloud observability initialization and instrumentation."""

import logging
from logging.config import dictConfig

import logfire

from coliseum import __version__
from coliseum.config import Settings

logger = logging.getLogger(__name__)


def initialize_logfire(settings: Settings) -> None:
    """
    Initialize Logfire with comprehensive instrumentation.

    Must be called ONCE at application startup, BEFORE any agent code runs.

    This function configures Logfire cloud tracking and instruments:
    - PydanticAI agents (Scout, Analyst, Trader, Guardian)
    - OpenAI SDK (GPT models, WebSearchTool, token usage)
    - HTTPX clients (Kalshi API, Exa API)
    - Python logging (bridges to Logfire)
    - System metrics (CPU, memory, disk)

    Args:
        settings: Application settings containing Logfire token

    Returns:
        None. Logs success or warning messages.
    """
    if not settings.logfire_token:
        logger.warning("Logfire token not set - observability disabled")
        return

    try:
        # 1. Configure Logfire with cloud token
        logfire.configure(
            token=settings.logfire_token,
            service_name="coliseum",
            service_version=__version__,
            environment="paper" if settings.trading.paper_mode else "live",
        )

        # 2. Instrument PydanticAI agents (Scout, Analyst, Trader, Guardian)
        logfire.instrument_pydantic_ai()

        # 3. Instrument OpenAI SDK (GPT models, WebSearchTool)
        logfire.instrument_openai()

        # 4. Instrument HTTPX (Kalshi API, Exa API)
        logfire.instrument_httpx()

        # 5. Bridge Python logging to Logfire
        # Add LogfireLoggingHandler to root logger
        root_logger = logging.getLogger()
        logfire_handler = logfire.LogfireLoggingHandler()
        root_logger.addHandler(logfire_handler)

        # 6. Collect system metrics (CPU, memory, disk) - optional
        try:
            logfire.instrument_system_metrics()
        except Exception as metrics_error:
            logger.debug(f"System metrics instrumentation skipped: {metrics_error}")

        logger.info("✓ Logfire cloud tracking initialized")

    except Exception as e:
        logger.warning(f"Failed to initialize Logfire: {e}")
        # Continue running - observability is optional
