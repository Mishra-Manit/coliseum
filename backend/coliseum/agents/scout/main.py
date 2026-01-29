"""Scout Agent: Market discovery and opportunity filtering."""

import os
import logging
from datetime import datetime, timezone
from typing import Literal

from pydantic_ai import Agent, RunContext, WebSearchTool
 
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import AnthropicModel, FireworksModel, OpenAIModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.memory import (
    MemoryEntry,
    append_memory_entry,
    get_seen_tickers,
    is_market_seen,
)

from .models import ScoutDependencies, ScoutOutput
from .prompts import SCOUT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def _create_scout_agent() -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent (called lazily to avoid loading API keys at import time)."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_MINI),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=SCOUT_SYSTEM_PROMPT,
        builtin_tools=[WebSearchTool()],
    )

def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the Scout agent."""

    @agent.tool
    async def fetch_markets_closing_soon(
        ctx: RunContext[ScoutDependencies],
    ) -> list[dict]:
        """Fetch markets closing within the configured time window (4-10 days for edge trading).

        Returns:
            List of market dictionaries with ticker, title, volume, prices, spread, close_time
        """
        # Use config values for time horizon
        min_close_hours = ctx.deps.config.min_close_hours
        max_close_hours = ctx.deps.config.max_close_hours
        
        markets = await ctx.deps.kalshi_client.get_markets_closing_within_hours(
            hours=max_close_hours,
            limit=4000,
            status="open",
        )
        
        # Filter for minimum close time
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        min_close_time = now.timestamp() + (min_close_hours * 3600)
        markets = [m for m in markets if m.close_time and m.close_time.timestamp() >= min_close_time]
        
        # Filter for minimum volume of 10,000 contracts (use 'volume' not 'volume_24h')
        min_volume = 10000
        markets = [m for m in markets if m.volume >= min_volume]

        # Markets >90% or <10% implied probability have little research value
        markets = [m for m in markets if 10 <= (m.yes_ask or 50) <= 90]

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
        """Generate a unique opportunity ID with opp_ prefix."""
        return generate_opportunity_id()

    @agent.tool
    def get_current_time(ctx: RunContext[ScoutDependencies]) -> str:
        """Get the current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


# Global agent instance (created on first use)
_scout_agent: Agent[ScoutDependencies, ScoutOutput] | None = None


def get_scout_agent() -> Agent[ScoutDependencies, ScoutOutput]:
    """Get the singleton Scout agent instance."""
    global _scout_agent
    if _scout_agent is None:
        # ensure API key is set for pydantic-ai
        settings = get_settings()
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        _scout_agent = _create_scout_agent()
        _register_tools(_scout_agent)
    return _scout_agent


async def run_scout(
    settings: Settings | None = None,
    dry_run: bool = False,
) -> ScoutOutput:
    """Execute a Scout scan and optionally save opportunities."""
    if settings is None:
        settings = get_settings()

    mode_label = "[DRY RUN] " if dry_run else ""
    logger.info(f"{mode_label}Starting Scout scan...")

    # Get currently tracked markets from memory to inject into prompt context
    seen_tickers = get_seen_tickers()
    seen_context = ""
    if seen_tickers:
        seen_context = (
            "\n\nPREVIOUSLY DISCOVERED MARKETS (DO NOT SELECT THESE - already being processed):\n"
            + "\n".join(f"- {ticker}" for ticker in seen_tickers)
        )
        logger.debug(f"Injecting {len(seen_tickers)} seen tickers into prompt context")

    # Scout always reads from production API (market data is public)
    from coliseum.services.kalshi.config import KalshiConfig
    kalshi_config = KalshiConfig(paper_mode=False)
    async with KalshiClient(config=kalshi_config) as client:
        deps = ScoutDependencies(
            kalshi_client=client,
            config=settings.scout,
        )

        # Run the agent with seen markets context
        agent = get_scout_agent()
        prompt = (
            f"Scan Kalshi markets and identify {settings.scout.max_opportunities_per_scan} "
            f"high-quality trading opportunities. "
            f"Only include markets with significant volume (>10,000 contracts) to ensure liquidity."
            f"{seen_context}"
        )
        result = await agent.run(prompt, deps=deps)

        output: ScoutOutput = result.output

        # Skip persistence in dry-run mode
        if dry_run:
            logger.info(
                f"{mode_label}Scout scan complete: "
                f"{output.opportunities_found} opportunities found "
                f"(not saved - dry run mode)"
            )
            return output

        # Process opportunities and add to memory
        now = datetime.now(timezone.utc)
        skipped_count = 0
        added_count = 0

        for opp in output.opportunities:
            try:
                # Check if already seen (via memory system)
                if is_market_seen(opp.market_ticker):
                    logger.info(
                        f"Skipping duplicate: {opp.market_ticker} (already in memory)"
                    )
                    skipped_count += 1
                    continue

                # Save opportunity file first
                save_opportunity(opp)
                logger.info(f"Saved opportunity: {opp.market_ticker}")

                # Add stub entry to memory (will be enriched by Trader)
                memory_entry = MemoryEntry(
                    market_ticker=opp.market_ticker,
                    discovered_at=now,
                    close_time=opp.close_time,
                    status="PENDING",
                )
                append_memory_entry(memory_entry)
                added_count += 1

            except Exception as e:
                logger.error(f"Failed to save opportunity {opp.id}: {e}")

        logger.info(
            f"Scout scan complete: "
            f"{output.opportunities_found} opportunities found, "
            f"{skipped_count} skipped (duplicates), "
            f"{added_count} added to memory"
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
