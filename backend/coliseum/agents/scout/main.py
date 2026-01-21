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
from coliseum.storage.state import (
    cleanup_seen_markets,
    get_seen_tickers,
    is_market_seen,
    mark_market_seen,
)

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
            limit=4000,
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

    @agent.tool
    def get_current_time(ctx: RunContext[ScoutDependencies]) -> str:
        """Get the current UTC timestamp in ISO 8601 format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


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
    dry_run: bool = False,
) -> ScoutOutput:
    """Execute a Scout scan and optionally save opportunities.

    Args:
        settings: Optional Settings override. Defaults to get_settings().
        dry_run: If True, skip file persistence and queue operations.
                 Useful for testing agent logic without side effects.

    Returns:
        ScoutOutput with discovered opportunities and scan summary.
    """
    if settings is None:
        settings = get_settings()

    mode_label = "[DRY RUN] " if dry_run else ""
    logger.info(f"{mode_label}Starting Scout scan...")

    # Cleanup expired markets from seen_markets before scanning
    if not dry_run:
        try:
            cleaned = cleanup_seen_markets()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired markets from tracking")
        except Exception as e:
            logger.warning(f"Failed to cleanup seen_markets: {e}")

    # Get currently tracked markets to inject into prompt context
    seen_tickers = get_seen_tickers()
    seen_context = ""
    if seen_tickers:
        seen_context = (
            "\n\nPREVIOUSLY DISCOVERED MARKETS (DO NOT SELECT THESE - already being processed):\n"
            + "\n".join(f"- {ticker}" for ticker in seen_tickers)
        )
        logger.debug(f"Injecting {len(seen_tickers)} seen tickers into prompt context")

    # Create Kalshi client with proper config (respects paper_mode setting)
    from coliseum.services.kalshi.config import KalshiConfig
    kalshi_config = KalshiConfig(paper_mode=settings.trading.paper_mode)
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

        # Save opportunities to disk, mark as seen, and queue for Analyst
        queued_count = 0
        skipped_count = 0
        
        for opp in output.opportunities:
            try:
                # Check if already seen (safety net - LLM might still select duplicates)
                if is_market_seen(opp.market_ticker):
                    logger.info(
                        f"Skipping duplicate: {opp.market_ticker} (already in seen_markets)"
                    )
                    skipped_count += 1
                    continue

                # Save to data/opportunities/
                save_opportunity(opp)

                # Mark as seen to prevent future duplicates
                mark_market_seen(
                    market_ticker=opp.market_ticker,
                    opportunity_id=opp.id,
                    close_time=opp.close_time,
                    status="pending",
                )

                # Queue for Analyst
                queue_for_analyst(opp.id)
                queued_count += 1

                logger.info(
                    f"Queued {opp.priority} priority opportunity: "
                    f"{opp.market_ticker}"
                )
            except Exception as e:
                logger.error(f"Failed to save/queue opportunity {opp.id}: {e}")

        logger.info(
            f"Scout scan complete: "
            f"{output.opportunities_found} opportunities found, "
            f"{queued_count} queued, {skipped_count} skipped (duplicates)"
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
