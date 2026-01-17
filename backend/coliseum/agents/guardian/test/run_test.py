#!/usr/bin/env python3
"""
Guardian Agent Test Runner

Runs the Guardian agent in isolation with verbose output to verify functionality.
Does NOT save data to the data folder - purely for testing and debugging.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate
    python -m coliseum.agents.guardian.test.run_test

    # With specific position to monitor:
    python -m coliseum.agents.guardian.test.run_test --position-id "pos_abc123"
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
logger = logging.getLogger("guardian.test")

# Reduce noise from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


async def run_guardian_test(
    position_id: str | None = None,
) -> None:
    """Execute a Guardian monitoring check in test mode (no file persistence).

    Args:
        position_id: Specific position ID to monitor (optional)
    """
    logger.info("=" * 60)
    logger.info("GUARDIAN AGENT TEST")
    logger.info("=" * 60)
    logger.info(f"Position ID: {position_id or 'None (will check all)'}")
    logger.info("-" * 60)

    # TODO: Implement Guardian agent test
    # 1. Create GuardianDependencies with Kalshi client, news service
    # 2. Load sample positions or create mock positions
    # 3. Run Guardian agent monitoring loop once
    # 4. Print position health assessments and exit signals
    
    logger.warning("Guardian agent test not yet implemented")
    logger.info("To implement: Add Guardian agent logic and tools")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE - No data was saved to disk")
    logger.info("=" * 60)


def main() -> None:
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the Guardian agent in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with all open positions
    python -m coliseum.agents.guardian.test.run_test

    # Monitor a specific position
    python -m coliseum.agents.guardian.test.run_test --position-id "pos_abc123"
        """,
    )
    parser.add_argument(
        "--position-id",
        type=str,
        default=None,
        help="Specific position ID to monitor",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_guardian_test(
                position_id=args.position_id,
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
