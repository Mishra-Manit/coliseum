#!/usr/bin/env python3
"""
Analyst Agent Test Runner

Runs the Analyst agent in isolation with verbose output to verify functionality.
Does NOT save data to the data folder - purely for testing and debugging.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate
    python -m coliseum.agents.analyst.test.run_test

    # With specific opportunity to analyze:
    python -m coliseum.agents.analyst.test.run_test --market-ticker "TICKER-ABC-123"
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path if running directly
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("analyst.test")

# Reduce noise from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


async def run_analyst_test(
    market_ticker: str | None = None,
    research_depth: str = "quick",
) -> None:
    """Execute an Analyst research run in test mode (no file persistence).

    Args:
        market_ticker: Specific market ticker to research (optional)
        research_depth: "quick", "standard", or "deep"
    """
    logger.info("=" * 60)
    logger.info("ANALYST AGENT TEST")
    logger.info("=" * 60)
    logger.info(f"Market ticker: {market_ticker or 'None (will use sample)'}")
    logger.info(f"Research depth: {research_depth}")
    logger.info("-" * 60)

    # TODO: Implement Analyst agent test
    # 1. Create AnalystDependencies with Exa client, Perplexity client
    # 2. Create test opportunity or fetch from Kalshi
    # 3. Run Analyst agent
    # 4. Print research brief and recommendation
    
    logger.warning("Analyst agent test not yet implemented")
    logger.info("To implement: Add Analyst agent logic and tools")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE - No data was saved to disk")
    logger.info("=" * 60)


def main() -> None:
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the Analyst agent in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with sample data
    python -m coliseum.agents.analyst.test.run_test

    # Research a specific market
    python -m coliseum.agents.analyst.test.run_test --market-ticker "TICKER-ABC-123"

    # Use deep research mode
    python -m coliseum.agents.analyst.test.run_test --research-depth deep
        """,
    )
    parser.add_argument(
        "--market-ticker",
        type=str,
        default=None,
        help="Specific market ticker to research",
    )
    parser.add_argument(
        "--research-depth",
        choices=["quick", "standard", "deep"],
        default="quick",
        help="Research depth (default: quick)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_analyst_test(
                market_ticker=args.market_ticker,
                research_depth=args.research_depth,
            )
        )
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
