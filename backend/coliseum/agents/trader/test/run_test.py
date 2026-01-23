#!/usr/bin/env python3
"""
Trader Agent Test Runner

Runs the Trader agent in isolation with verbose output to verify functionality.
Does NOT save data to the data folder - purely for testing and debugging.

IMPORTANT: This test runs in paper trading mode only. No real trades are executed.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate
    python -m coliseum.agents.trader.test.run_test

    # With specific analysis to execute:
    python -m coliseum.agents.trader.test.run_test --analysis-id "analysis_abc123"
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
logger = logging.getLogger("trader.test")

# Reduce noise from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


async def run_trader_test(
    analysis_id: str | None = None,
    paper_mode: bool = True,
) -> None:
    """Execute a Trader order in test mode (paper trading only).

    Args:
        analysis_id: Specific analysis ID to execute (optional)
        paper_mode: Always True for testing - no real trades
    """
    if not paper_mode:
        logger.error("SAFETY: paper_mode must be True for testing. Forcing paper mode.")
        paper_mode = True
    
    logger.info("=" * 60)
    logger.info("TRADER AGENT TEST (PAPER MODE)")
    logger.info("=" * 60)
    logger.info(f"Analysis ID: {analysis_id or 'None (will use sample)'}")
    logger.info(f"Paper mode: {paper_mode}")
    logger.info("-" * 60)

    # TODO: Implement Trader agent test
    # 1. Create TraderDependencies with Kalshi client (paper mode)
    # 2. Create sample analysis or load from file
    # 3. Run risk validation
    # 4. Simulate order execution
    # 5. Print execution results without saving
    
    logger.warning("Trader agent test not yet implemented")
    logger.info("To implement: Add Trader agent logic and tools")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE - No trades were executed, no data was saved")
    logger.info("=" * 60)


def main() -> None:
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the Trader agent in isolation (paper mode only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with sample analysis
    python -m coliseum.agents.trader.test.run_test

    # Execute a specific analysis
    python -m coliseum.agents.trader.test.run_test --analysis-id "analysis_abc123"

Note: This test ALWAYS runs in paper mode. No real trades are ever executed.
        """,
    )
    parser.add_argument(
        "--analysis-id",
        type=str,
        default=None,
        help="Specific analysis ID to execute",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_trader_test(
                analysis_id=args.analysis_id,
                paper_mode=True,  # Always paper mode for safety
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
