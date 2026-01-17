#!/usr/bin/env python3
"""
Scout Agent Test Runner

Runs the Scout agent in isolation with verbose output to verify functionality.
Does NOT save data to the data folder - purely for testing and debugging.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate
    python -m coliseum.agents.scout.test.run_test

    # Or run directly:
    python coliseum/agents/scout/test/run_test.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

# Add backend to path if running directly
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from pydantic_ai import Agent, RunContext

from coliseum.config import Settings, ScoutConfig, get_settings
from coliseum.llm_providers import AnthropicModel, FireworksModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.files import OpportunitySignal, generate_opportunity_id

from coliseum.agents.scout.models import ScoutDependencies, ScoutOutput
from coliseum.agents.scout.prompts import SCOUT_SYSTEM_PROMPT


# Configure verbose logging with better formatting
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to reduce noise
    format="%(asctime)s | %(levelname)-8s | %(message)s",  # Simplified format
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scout.test")
logger.setLevel(logging.INFO)

# Reduce noise from HTTP and OpenAI libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


def _create_test_scout_agent() -> Agent[ScoutDependencies, ScoutOutput]:
    """Create a Scout agent for testing (no persistence)."""
    return Agent(
        model=get_model_string(FireworksModel.GPT_OSS_120B),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=SCOUT_SYSTEM_PROMPT,
    )


def _register_test_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the test Scout agent."""

    @agent.tool
    async def fetch_markets_closing_soon(
        ctx: RunContext[ScoutDependencies],
        max_close_hours: int = 72,
    ) -> list[dict]:
        """Fetch markets closing within the specified time window.

        Args:
            max_close_hours: Maximum hours until market close (default: 72)

        Returns:
            List of market dictionaries with ticker, title, volume, prices, spread, close_time
        """
        logger.info(f"\n🔍 [TOOL] Fetching markets closing within {max_close_hours} hours...")

        markets = await ctx.deps.kalshi_client.get_markets_closing_within_hours(
            hours=max_close_hours,
            limit=10000,  # Increased from 1000 to match successful pagination
            status="open",
        )

        # Filter for minimum volume of 10,000 contracts (use 'volume' not 'volume_24h')
        min_volume = ctx.deps.config.min_volume
        markets_before = len(markets)
        markets = [m for m in markets if m.volume >= min_volume]
        logger.info(f"   ✓ Returning {len(markets)} markets after volume filter (filtered out {markets_before - len(markets)} markets with volume <{min_volume:,})")
        if markets_before > 0 and len(markets) == 0:
            logger.warning(f"   ⚠️  All {markets_before} markets were filtered out by volume threshold!")
            logger.warning(f"   💡 Consider lowering min_volume from {min_volume:,}")

        # Convert to JSON-serializable format for LLM with spread calculations
        result = [
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
                "category": m.category,
            }
            for m in markets
        ]

        # Log sample markets for visibility
        if result:
            logger.info(f"\n   📊 Sample markets (showing {min(3, len(result))}/{len(result)}):")
            for i, m in enumerate(result[:3], 1):
                spread = f"{m['spread_cents']}¢" if m['spread_cents'] else "N/A"
                logger.info(f"      {i}. {m['ticker']}")
                logger.info(f"         Title: {m['title'][:60]}...")
                logger.info(f"         Volume: {m['volume']:,} | Spread: {spread}")
        else:
            logger.warning(f"   ⚠️  No markets to return!")

        return result

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        """Generate a unique opportunity ID with opp_ prefix.

        Returns:
            Unique ID string (e.g., "opp_a1b2c3d4")
        """
        opp_id = generate_opportunity_id()
        logger.debug(f"[TOOL] Generated opportunity ID: {opp_id}")
        return opp_id


async def run_scout_test(
    scan_type: Literal["full", "quick"] = "full",
    max_opportunities: int = 5,
    max_close_hours: int = 72,
) -> ScoutOutput:
    """Execute a Scout scan in test mode (no file persistence).

    Args:
        scan_type: "full" scans all markets, "quick" scans high-volume only
        max_opportunities: Maximum opportunities to find
        max_close_hours: Maximum hours until market close

    Returns:
        ScoutOutput with discovered opportunities and summary
    """
    logger.info("\n" + "=" * 70)
    logger.info("🔍 SCOUT AGENT TEST")
    logger.info("=" * 70)
    logger.info(f"📋 Scan type: {scan_type}")
    logger.info(f"🎯 Max opportunities: {max_opportunities}")
    logger.info(f"⏰ Max close hours: {max_close_hours}")
    logger.info("-" * 70)

    # Load settings to get API keys
    settings = get_settings()
    if settings.fireworks_api_key:
        os.environ["FIREWORKS_API_KEY"] = settings.fireworks_api_key

    # Create test configuration (doesn't load from data folder)
    config = ScoutConfig(
        min_volume=10000,
        min_liquidity_cents=10,
        max_close_hours=max_close_hours,
        max_opportunities_per_scan=max_opportunities,
        quick_scan_min_volume=50000,
    )
    
    logger.info(f"⚙️  Min volume: {config.min_volume:,} | Min liquidity: {config.min_liquidity_cents}¢")

    # Create Kalshi client
    logger.info("\n🔌 Connecting to Kalshi API...")
    async with KalshiClient() as client:
        deps = ScoutDependencies(
            kalshi_client=client,
            config=config,
        )
        logger.info("✅ Kalshi client connected successfully\n")

        # Create and configure agent
        agent = _create_test_scout_agent()
        _register_test_tools(agent)

        prompt = (
            f"Scan Kalshi markets and identify {max_opportunities} "
            f"high-quality trading opportunities. "
            f"Use {scan_type} scan criteria: "
            f"{'high-volume markets only (>50k volume)' if scan_type == 'quick' else 'all markets meeting thresholds'}."
        )

        logger.info(f"🤖 Running Scout agent...")
        logger.info("-" * 70)

        # Run the agent
        start_time = datetime.now()
        result = await agent.run(prompt, deps=deps)
        elapsed = (datetime.now() - start_time).total_seconds()

        output: ScoutOutput = result.output

        # Print results
        logger.info("\n" + "=" * 70)
        logger.info("📊 RESULTS")
        logger.info("=" * 70)
        logger.info(f"⏱️  Execution time: {elapsed:.2f}s")
        logger.info(f"🔍 Markets scanned: {output.markets_scanned}")
        logger.info(f"✨ Opportunities found: {output.opportunities_found}")
        logger.info(f"🚫 Filtered out: {output.filtered_out}")
        logger.info("-" * 70)
        logger.info(f"📝 Summary: {output.scan_summary}")
        logger.info("-" * 70)

        # Print each opportunity
        if output.opportunities:
            logger.info(f"\n🎯 OPPORTUNITIES ({len(output.opportunities)}):")
            logger.info("-" * 70)
            for i, opp in enumerate(output.opportunities, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(opp.priority, "⚪")
                logger.info(f"\n  {emoji} Opportunity {i}/{len(output.opportunities)}")
                logger.info(f"     ID: {opp.id}")
                logger.info(f"     Market: {opp.market_ticker}")
                logger.info(f"     Title: {opp.title[:65]}...")
                logger.info(f"     Category: {opp.category} | Priority: {opp.priority.upper()}")
                logger.info(f"     Prices: YES {opp.yes_price * 100:.0f}¢ | NO {opp.no_price * 100:.0f}¢")
                logger.info(f"     Close Time: {opp.close_time}")
                logger.info(f"     Rationale: {opp.rationale[:120]}...")
        else:
            logger.warning(f"\n⚠️  No opportunities found!")

        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST COMPLETE - No data was saved to disk")
        logger.info("=" * 70 + "\n")

        return output


def main() -> None:
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the Scout agent in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full scan with default settings
    python -m coliseum.agents.scout.test.run_test

    # Run quick scan with fewer opportunities
    python -m coliseum.agents.scout.test.run_test --scan-type quick --max-opportunities 3

    # Scan markets closing within 24 hours
    python -m coliseum.agents.scout.test.run_test --max-close-hours 24
        """,
    )
    parser.add_argument(
        "--scan-type",
        choices=["full", "quick"],
        default="full",
        help="Type of scan to perform (default: full)",
    )
    parser.add_argument(
        "--max-opportunities",
        type=int,
        default=5,
        help="Maximum opportunities to find (default: 5)",
    )
    parser.add_argument(
        "--max-close-hours",
        type=int,
        default=72,
        help="Maximum hours until market close (default: 72)",
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(
            run_scout_test(
                scan_type=args.scan_type,
                max_opportunities=args.max_opportunities,
                max_close_hours=args.max_close_hours,
            )
        )
        sys.exit(0 if result.opportunities else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
