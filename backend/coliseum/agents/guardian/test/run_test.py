#!/usr/bin/env python3
"""
Guardian Agent Test Runner

Runs the Guardian agent in isolation with verbose output to verify functionality.
This executes a real reconciliation run and will update local state/memory files.

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
    """Execute one Guardian reconciliation run with verbose logging."""
    logger.info("=" * 60)
    logger.info("GUARDIAN AGENT TEST")
    logger.info("=" * 60)
    logger.info(f"Position ID: {position_id or 'None (will check all)'}")
    logger.info("-" * 60)

    from coliseum.agents.guardian import run_guardian
    from coliseum.config import get_settings

    settings = get_settings()
    result = await run_guardian(settings=settings)

    logger.info("Guardian agent run complete")
    logger.info("Positions synced: %d", result.positions_synced)
    logger.info(
        "Reconciliation: inspected=%d kept_open=%d newly_closed=%d skipped_no_trade=%d warnings=%d",
        result.reconciliation.entries_inspected,
        result.reconciliation.kept_open,
        result.reconciliation.newly_closed,
        result.reconciliation.skipped_no_trade,
        result.reconciliation.warnings,
    )
    if result.warnings:
        logger.warning("Missing memory entries: %s", ", ".join(result.warnings))
    if result.agent_summary:
        logger.info("Agent summary: %s", result.agent_summary)

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
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
