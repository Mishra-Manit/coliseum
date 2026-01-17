#!/usr/bin/env python3
"""
Minimal test script to isolate the fetch_markets_closing_soon tool.

This script tests ONLY the market fetching tool to understand:
1. How many markets are returned
2. How much data (tokens) each market contains
3. Total data size being sent to the LLM

Usage:
    cd backend
    source venv/bin/activate
    python -m coliseum.agents.scout.test.test_fetch_markets
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path if running directly
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from coliseum.config import ScoutConfig, get_settings
from coliseum.llm_providers import FireworksModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_fetch_markets")

# Reduce noise from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class TestDeps(BaseModel):
    """Minimal dependencies for the test."""
    model_config = {"arbitrary_types_allowed": True}
    kalshi_client: KalshiClient
    config: ScoutConfig


class TestOutput(BaseModel):
    """Simple output - just count and summary."""
    markets_found: int
    summary: str


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars for English text)."""
    return len(text) // 4


def create_test_agent() -> Agent[TestDeps, TestOutput]:
    """Create a minimal agent with ONLY the fetch_markets tool."""
    
    agent = Agent(
        model=get_model_string(FireworksModel.GPT_OSS_120B),
        output_type=TestOutput,
        deps_type=TestDeps,
        system_prompt="You are a test agent. Call fetch_markets_closing_soon to get market data, then summarize what you found.",
    )

    @agent.tool
    async def fetch_markets_closing_soon(
        ctx: RunContext[TestDeps],
        max_close_hours: int = 72,
    ) -> list[dict]:
        """Fetch markets closing within the specified time window.

        Args:
            max_close_hours: Maximum hours until market close (default: 72)

        Returns:
            List of market dictionaries with ticker, title, volume, prices, spread, close_time
        """
        logger.info(f"[TOOL] Fetching markets closing within {max_close_hours} hours...")

        markets = await ctx.deps.kalshi_client.get_markets_closing_within_hours(
            hours=max_close_hours,
            limit=1000,
            status="open",
        )

        logger.info(f"[TOOL] Raw markets from API: {len(markets)}")

        # Apply volume filter - use 'volume' (total) not 'volume_24h' (which is often 0)
        markets = [m for m in markets if m.volume >= 10000]
        logger.info(f"[TOOL] After volume filter (>=10k): {len(markets)}")

        # Convert to JSON-serializable format (same as production) with spread calculations
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

        return result

    return agent


async def run_test(max_close_hours: int = 72) -> None:
    """Run the isolated fetch_markets test."""
    
    print("=" * 70)
    print("FETCH MARKETS TOOL - ISOLATED TEST")
    print("=" * 70)
    print(f"Max close hours: {max_close_hours}")
    print("-" * 70)

    # Load settings for API keys
    settings = get_settings()
    if settings.fireworks_api_key:
        os.environ["FIREWORKS_API_KEY"] = settings.fireworks_api_key

    config = ScoutConfig(
        min_volume=10000,
        min_liquidity_cents=10,
        max_close_hours=max_close_hours,
        max_opportunities_per_scan=5,
    )

    # Use production API for reading market data (demo API has no volume data)
    kalshi_config = KalshiConfig(paper_mode=False)
    
    async with KalshiClient(config=kalshi_config) as client:
        deps = TestDeps(kalshi_client=client, config=config)
        
        # First, let's just call the API directly to see raw data size
        print("\n[1] DIRECT API CALL (no LLM)")
        print("-" * 70)
        
        markets = await client.get_markets_closing_within_hours(
            hours=max_close_hours,
            limit=1000,
            status="open",
        )
        print(f"Raw markets from API: {len(markets)}")
        
        # Apply volume filter - use 'volume' (total) not 'volume_24h' (which is often 0)
        filtered_markets = [m for m in markets if m.volume >= 10000]
        print(f"After volume filter (>=10k): {len(filtered_markets)}")
        
        # Convert to the JSON format that would be sent to LLM with spread calculations
        json_markets = [
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
            for m in filtered_markets
        ]
        
        # Calculate data size
        json_str = json.dumps(json_markets, indent=2)
        json_compact = json.dumps(json_markets)
        
        print(f"\nDATA SIZE ANALYSIS:")
        print(f"  JSON (pretty): {len(json_str):,} chars")
        print(f"  JSON (compact): {len(json_compact):,} chars")
        print(f"  Estimated tokens (pretty): ~{estimate_tokens(json_str):,}")
        print(f"  Estimated tokens (compact): ~{estimate_tokens(json_compact):,}")
        
        # Show sample market
        if json_markets:
            sample = json.dumps(json_markets[0], indent=2)
            print(f"\nSAMPLE MARKET (1 of {len(json_markets)}):")
            print("-" * 40)
            print(sample)
            print("-" * 40)
            print(f"  Chars per market: ~{len(sample)}")
            print(f"  Tokens per market: ~{estimate_tokens(sample)}")
        
        # Show category distribution
        categories: dict[str, int] = {}
        for m in json_markets:
            cat = m.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\nCATEGORY DISTRIBUTION:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        
        # Now run with the LLM agent
        print("\n" + "=" * 70)
        print("[2] LLM AGENT CALL")
        print("=" * 70)
        
        agent = create_test_agent()
        
        prompt = "Fetch the markets closing soon and tell me how many you found. Tell me the most interesting market you found in these results as well."
        print(f"Prompt: {prompt}")
        print("-" * 70)
        
        start_time = datetime.now()
        result = await agent.run(prompt, deps=deps)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\nRESULTS:")
        print(f"  Execution time: {elapsed:.2f}s")
        print(f"  Markets found: {result.output.markets_found}")
        print(f"  Summary: {result.output.summary}")
        
        # Try to get usage info if available
        if hasattr(result, 'usage'):
            print(f"\nTOKEN USAGE:")
            print(f"  {result.usage}")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)


def main() -> None:
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test fetch_markets_closing_soon in isolation")
    parser.add_argument(
        "--max-close-hours",
        type=int,
        default=72,
        help="Maximum hours until market close (default: 72)",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_test(max_close_hours=args.max_close_hours))
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
