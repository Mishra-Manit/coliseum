"""Scout Agent: Market discovery and opportunity filtering."""

import os
import logging
from typing import Literal

from pydantic_ai import Agent, RunContext
 
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import AnthropicModel, FireworksModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.queue import queue_for_analyst

from .models import ScoutDependencies, ScoutOutput
from .prompts import SCOUT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def _create_scout_agent() -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent (called lazily to avoid loading API keys at import time)."""
    return Agent(
        model=get_model_string(FireworksModel.DEEPSEEK_V3_2),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=SCOUT_SYSTEM_PROMPT,
    )

def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the Scout agent."""

    @agent.tool
    async def fetch_markets_closing_soon(
        ctx: RunContext[ScoutDependencies],
        max_close_hours: int = 72,
    ) -> list[dict]:
        """Fetch markets closing within the specified time window.

        Returns:
            List of market dictionaries with ticker, title, volume, prices, spread, close_time
        """
        markets = await ctx.deps.kalshi_client.get_markets_closing_within_hours(
            hours=max_close_hours,
            limit=10000,  # Increased from 1000 to match successful pagination
            status="open",
        )
        # Filter for minimum volume of 10,000 contracts (use 'volume' not 'volume_24h')
        min_volume = 10000
        markets = [m for m in markets if m.volume >= min_volume]

        # Filter out extreme probability markets (no actionable edge)
        # Markets >95% or <5% implied probability have little research value
        markets = [m for m in markets if 5 <= (m.yes_ask or 50) <= 95]

        # Convert to JSON-serializable format for LLM with spread calculations
        return [
            {
                "ticker": m.ticker,
                "event_ticker": m.event_ticker,
                "title": m.title,
                "subtitle": m.subtitle,
                "yes_bid": m.yes_bid,
                "yes_ask": m.yes_ask,
                "no_bid": m.no_bid,
                "no_ask": m.no_ask,
                "spread_cents": (m.yes_ask - m.yes_bid) if (m.yes_ask and m.yes_bid) else None,
                "spread_pct": ((m.yes_ask - m.yes_bid) / 100) if (m.yes_ask and m.yes_bid) else None,
                "volume": m.volume,
                "open_interest": m.open_interest,
                "close_time": m.close_time.isoformat() if m.close_time else None,
            }
            for m in markets
        ]

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        """Generate a unique opportunity ID with opp_ prefix.

        Returns:
            Unique ID string (e.g., "opp_a1b2c3d4")
        """
        return generate_opportunity_id()


# Global agent instance (created on first use)
_scout_agent: Agent[ScoutDependencies, ScoutOutput] | None = None


def get_scout_agent() -> Agent[ScoutDependencies, ScoutOutput]:
    """Get the singleton Scout agent instance."""
    global _scout_agent
    if _scout_agent is None:
        # ensure API key is set for pydantic-ai
        settings = get_settings()
        if settings.fireworks_api_key:
            os.environ["FIREWORKS_API_KEY"] = settings.fireworks_api_key

        _scout_agent = _create_scout_agent()
        _register_tools(_scout_agent)
    return _scout_agent


async def run_scout(
    settings: Settings | None = None,
) -> ScoutOutput:
    """Execute a Scout scan and save opportunities."""
    if settings is None:
        settings = get_settings()

    logger.info("Starting Scout scan...")

    # Create Kalshi client with proper config (respects paper_mode setting)
    from coliseum.services.kalshi.config import KalshiConfig
    kalshi_config = KalshiConfig(paper_mode=settings.trading.paper_mode)
    async with KalshiClient(config=kalshi_config) as client:
        deps = ScoutDependencies(
            kalshi_client=client,
            config=settings.scout,
        )



        # Run the agent
        agent = get_scout_agent()
        result = await agent.run(
            f"Scan Kalshi markets and identify {settings.scout.max_opportunities_per_scan} "
            f"high-quality trading opportunities. "
            f"Only include markets with significant volume (>10,000 contracts) to ensure liquidity.",
            deps=deps,
        )

        output: ScoutOutput = result.output

        # Save opportunities to disk and queue for Analyst
        for opp in output.opportunities:
            try:
                # Save to data/opportunities/
                save_opportunity(opp)

                # Queue for Analyst
                queue_for_analyst(opp.id)

                logger.info(
                    f"Queued {opp.priority} priority opportunity: "
                    f"{opp.market_ticker}"
                )
            except Exception as e:
                logger.error(f"Failed to save/queue opportunity {opp.id}: {e}")

        logger.info(
            f"Scout scan complete: "
            f"{output.opportunities_found} opportunities found, "
            f"{len(output.opportunities)} queued"
        )

        return output


def scout_scan_job() -> None:
    """Scheduler job wrapper for market scan (blocking)."""
    import asyncio

    try:
        result = asyncio.run(run_scout())
        logger.info(f"✓ Scout scan: {result.opportunities_found} opportunities")
    except Exception as e:
        logger.error(f"Scout scan failed: {e}", exc_info=True)
