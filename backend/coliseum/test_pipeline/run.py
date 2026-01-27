#!/usr/bin/env python3
"""
Test Pipeline Runner

Runs agents using the production code but with test_data/ as the data directory.
This enables end-to-end pipeline testing with isolated data storage.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate

    # Run individual agents:
    python -m coliseum.test_pipeline scout
    python -m coliseum.test_pipeline scout --dry-run  # No file persistence
    python -m coliseum.test_pipeline analyst --opportunity-id opp_123  # Required (no-op if omitted)
    python -m coliseum.test_pipeline trader --opportunity-file KXBTCD-26JAN2317-T89999.99.md
    python -m coliseum.test_pipeline guardian

    # Run full pipeline:
    python -m coliseum.test_pipeline run --full

    # Clean test data:
    python -m coliseum.test_pipeline clean
"""

import argparse
import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# Ensure backend is in path for direct execution
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from coliseum.test_pipeline.config import TEST_DATA_DIR


# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_pipeline")
logger.setLevel(logging.INFO)

# Reduce noise from HTTP and OpenAI libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


# =============================================================================
# Logfire Initialization Helper
# =============================================================================

def _initialize_test_logfire() -> None:
    """Initialize Logfire for test pipeline runs."""
    try:
        from coliseum.observability import initialize_logfire
        from coliseum.config import get_settings
        settings = get_settings()
        initialize_logfire(settings)
    except Exception as e:
        logger.warning(f"Test pipeline Logfire initialization skipped: {e}")


# =============================================================================
# Test Data Directory Management
# =============================================================================

def init_test_data_structure() -> None:
    """Initialize the test data directory structure (mirrors data/)."""
    # Create subdirectories matching data/ structure
    subdirs = [
        "opportunities",
        "positions/open",
        "positions/closed",
        "trades",
    ]

    for subdir in subdirs:
        (TEST_DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # Create minimal config.yaml if it doesn't exist
    config_path = TEST_DATA_DIR / "config.yaml"
    if not config_path.exists():
        config_path.write_text(
            "# Test configuration\n"
            "trading:\n"
            "  paper_mode: true\n"
            "  initial_bankroll: 100.0\n"
            "\n"
            "scout:\n"
            "  max_opportunities_per_scan: 5\n",
            encoding="utf-8",
        )

    # Create state.yaml if it doesn't exist
    state_path = TEST_DATA_DIR / "state.yaml"
    if not state_path.exists():
        state_path.write_text(
            "last_updated: null\n"
            "portfolio:\n"
            "  total_value: 100.0\n"
            "  cash_balance: 100.0\n"
            "  positions_value: 0.0\n"
            "daily_stats:\n"
            "  date: null\n"
            "  starting_value: 100.0\n"
            "  current_pnl: 0.0\n"
            "  current_pnl_pct: 0.0\n"
            "  trades_today: 0\n"
            "open_positions: []\n"
            "risk_status:\n"
            "  daily_loss_limit_hit: false\n"
            "  trading_halted: false\n"
            "  capital_at_risk_pct: 0.0\n",
            encoding="utf-8",
        )

    logger.info(f"Initialized test data structure at {TEST_DATA_DIR}")


def clean_test_data() -> None:
    """Clear all test data from test_data/ directory."""
    logger.info("\n" + "=" * 70)
    logger.info("Cleaning test data...")
    logger.info("=" * 70)

    if not TEST_DATA_DIR.exists():
        logger.info("Test data directory does not exist. Nothing to clean.")
        return

    # Count files before cleaning
    file_count = sum(1 for _ in TEST_DATA_DIR.rglob("*") if _.is_file())

    # Remove all contents but keep the directory
    for item in TEST_DATA_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    logger.info(f"Removed {file_count} files from {TEST_DATA_DIR}")
    logger.info("Test data directory cleaned successfully")


def _override_data_dir() -> None:
    """Override the data directory to use test_data/ for this process.
    
    This modifies the Settings singleton to point to test_data/ instead of data/.
    Must be called before any agent code runs.
    """
    # Clear the settings cache so it will be reloaded with new data_dir
    from coliseum.config import get_settings
    get_settings.cache_clear()
    
    # Set environment variable to override data_dir
    os.environ["DATA_DIR"] = str(TEST_DATA_DIR)
    
    # Monkey-patch get_settings to use test_data_dir
    import coliseum.config as config_module
    
    original_get_settings = config_module.get_settings.__wrapped__
    
    def patched_get_settings():
        settings = original_get_settings()
        # Override data_dir to test directory
        object.__setattr__(settings, 'data_dir', TEST_DATA_DIR)
        return settings
    
    # Replace the cached function
    from functools import lru_cache
    config_module.get_settings = lru_cache()(patched_get_settings)
    
    logger.info(f"Data directory overridden to: {TEST_DATA_DIR}")


def _select_opportunity_file(opportunities_dir: Path, opportunity_file: str | None) -> Path:
    """Select a test opportunity file by name or newest file in directory."""
    if opportunity_file:
        candidate = Path(opportunity_file)
        if not candidate.is_absolute():
            candidate = opportunities_dir / opportunity_file
        if candidate.exists():
            return candidate

        matches = sorted(
            opportunities_dir.rglob(Path(opportunity_file).name),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if matches:
            return matches[0]

        raise FileNotFoundError(f"Opportunity file not found: {candidate}")

    candidates = sorted(
        opportunities_dir.rglob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No opportunity files found in {opportunities_dir}")
    return candidates[0]


# =============================================================================
# Scout Agent Test Runner
# =============================================================================

async def run_scout_test(dry_run: bool = False) -> None:
    """Run Scout agent using production code.

    Args:
        dry_run: If True, skip file persistence.
                 The agent runs and returns results, but nothing is saved to disk.
                 If False, saves to test_data/ directory (isolated from production).
    """
    mode_label = "[DRY RUN] " if dry_run else ""
    
    logger.info("\n" + "=" * 70)
    logger.info(f"{mode_label}Scout Agent Test")
    logger.info("=" * 70)

    # Initialize test data structure (needed for config even in dry-run)
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    # Now import and run the production Scout agent
    from coliseum.agents.scout import run_scout

    logger.info(f"{mode_label}Running production Scout agent...")
    if dry_run:
        logger.info("   (No files will be saved - dry run mode)")
    logger.info("-" * 70)

    try:
        output = await run_scout(dry_run=dry_run)

        logger.info("\n" + "=" * 70)
        logger.info(f"{mode_label}Results")
        logger.info("=" * 70)
        logger.info(f"   Markets scanned: {output.markets_scanned}")
        logger.info(f"   Opportunities found: {output.opportunities_found}")
        logger.info(f"   Filtered out: {output.filtered_out}")
        logger.info("-" * 70)
        logger.info(f"   Summary: {output.scan_summary}")
        logger.info("-" * 70)

        if output.opportunities:
            logger.info(f"\n   OPPORTUNITIES ({len(output.opportunities)}):")
            logger.info("-" * 70)
            for i, opp in enumerate(output.opportunities, 1):
                logger.info(f"\n   Opportunity {i}/{len(output.opportunities)}")
                logger.info(f"      ID: {opp.id}")
                logger.info(f"      Market: {opp.market_ticker}")
                logger.info(f"      Title: {opp.title[:65]}...")
                logger.info(f"      Prices: YES {opp.yes_price * 100:.0f}c | NO {opp.no_price * 100:.0f}c")
                logger.info(f"      Close Time: {opp.close_time}")
        else:
            logger.warning("\n   No opportunities found!")

        logger.info("\n" + "=" * 70)
        if dry_run:
            logger.info(f"{mode_label}Scout test complete - {len(output.opportunities)} opportunities found (not saved)")
        else:
            logger.info(f"Scout test complete - {len(output.opportunities)} opportunities saved to test_data/")
        logger.info("=" * 70 + "\n")

    except Exception as e:
        logger.exception(f"Scout test failed: {e}")
        raise


# =============================================================================
# Analyst Agent Test Runner
# =============================================================================

async def run_analyst_test(opportunity_id: str | None = None) -> None:
    """Run Analyst agent on opportunities.

    Args:
        opportunity_id: Specific opportunity ID to analyze. If None, skip processing.
    """
    logger.info("\n" + "=" * 70)
    logger.info("Analyst Agent Test")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    if opportunity_id:
        logger.info(f"   Processing specific opportunity: {opportunity_id}")

    logger.info("-" * 70)

    if not opportunity_id:
        logger.info("   No opportunity_id provided (queue removed).")
        logger.info("   Nothing to process for analyst test.")
        logger.info("\n" + "=" * 70)
        logger.info("Analyst test complete (no-op)")
        logger.info("=" * 70 + "\n")
        return

    from coliseum.agents.analyst import run_analyst
    from coliseum.config import get_settings

    settings = get_settings()

    try:
        opportunity = await run_analyst(
            opportunity_id=opportunity_id,
            settings=settings,
            dry_run=False,
        )
    except Exception as e:
        logger.exception(f"Analyst test failed: {e}")
        raise

    logger.info("\n" + "=" * 70)
    logger.info("Analyst results")
    logger.info("=" * 70)
    logger.info(f"   Market: {opportunity.market_ticker}")
    logger.info(f"   Status: {opportunity.status}")
    logger.info(f"   Edge: {opportunity.edge:+.2%}" if opportunity.edge is not None else "   Edge: N/A")
    logger.info(
        f"   Expected Value: {opportunity.expected_value:+.2%}"
        if opportunity.expected_value is not None
        else "   Expected Value: N/A"
    )
    logger.info(
        f"   Suggested Size: {opportunity.suggested_position_pct:.1%}"
        if opportunity.suggested_position_pct is not None
        else "   Suggested Size: N/A"
    )

    logger.info("\n" + "=" * 70)
    logger.info("Analyst test complete")
    logger.info("=" * 70 + "\n")


# =============================================================================
# Trader Agent Test Runner
# =============================================================================

async def run_trader_test(opportunity_file: str | None = None, verbose: bool = False) -> None:
    """Run Trader agent on a specific opportunity file."""
    logger.info("\n" + "=" * 70)
    logger.info("Trader Agent Test (DRY RUN, PAPER MODE)")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    logger.info("-" * 70)
    opportunities_dir = TEST_DATA_DIR / "opportunities"
    opp_file = _select_opportunity_file(opportunities_dir, opportunity_file)
    from coliseum.storage.files import load_opportunity_from_file

    opportunity = load_opportunity_from_file(opp_file)
    logger.info(f"   Selected opportunity: {opportunity.id}")
    logger.info(f"   Market: {opportunity.market_ticker}")

    from coliseum.agents.trader import run_trader
    from coliseum.config import get_settings

    settings = get_settings()
    settings.trading.paper_mode = True

    if settings.trading.paper_mode:
        logger.info("   Paper mode enabled; skipping Kalshi credential checks.")
    elif not settings.kalshi_api_key or not settings.get_rsa_private_key():
        logger.warning("   Missing Kalshi credentials; skipping live market check.")
        logger.info("   Set KALSHI_API_KEY and KALSHI_PRIVATE_KEY_PATH to run this test.")
        logger.info("\n" + "=" * 70)
        logger.info("Trader test complete (skipped)")
        logger.info("=" * 70 + "\n")
        return

    if verbose:
        os.environ["COLISEUM_AGENT_TRACE"] = "1"
        logger.info("   Verbose agent trace enabled (tool calls/results).")
    else:
        os.environ.pop("COLISEUM_AGENT_TRACE", None)

    try:
        output = await run_trader(
            opportunity_id=opportunity.id,
            settings=settings,
        )
    except Exception as e:
        logger.exception(f"Trader test failed: {e}")
        raise

    logger.info("\n" + "=" * 70)
    logger.info("Trader results")
    logger.info("=" * 70)
    logger.info(f"   Decision: {output.decision.action}")
    logger.info(f"   Confidence: {output.decision.confidence:.2%}")
    logger.info(f"   Execution status: {output.execution_status}")
    if output.decision.reasoning:
        logger.info(f"   Reasoning: {output.decision.reasoning}")
    if output.decision.verification_summary:
        logger.info(f"   Verification summary: {output.decision.verification_summary}")

    logger.info("\n" + "=" * 70)
    logger.info("Trader test complete")
    logger.info("=" * 70 + "\n")


# =============================================================================
# Guardian Agent Test Runner
# =============================================================================

async def run_guardian_test() -> None:
    """Run Guardian agent to check positions.

    Monitors all open positions and generates exit signals if needed.
    """
    logger.info("\n" + "=" * 70)
    logger.info("Guardian Agent Test")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    # Check for open positions
    positions_dir = TEST_DATA_DIR / "positions" / "open"

    if positions_dir.exists():
        open_positions = list(positions_dir.glob("*.yaml")) + list(positions_dir.glob("*.md"))
        logger.info(f"   Found {len(open_positions)} open positions")
    else:
        logger.info("   No open positions found")

    logger.info("-" * 70)

    # TODO: Implement actual Guardian agent when main.py is ready
    logger.warning("   Guardian agent not yet implemented in main.py")
    logger.info("   To implement: Create Guardian agent with position monitoring tools")
    logger.info("   Expected behavior: Check P/L, news, generate exit signals if triggered")

    logger.info("\n" + "=" * 70)
    logger.info("Guardian test complete (stub implementation)")
    logger.info("=" * 70 + "\n")


# =============================================================================
# Full Pipeline Runner
# =============================================================================

async def run_full_pipeline() -> None:
    """Run complete pipeline: Scout -> Analyst -> Trader -> Guardian.

    This demonstrates the full autonomous trading flow in test mode.
    """
    logger.info("\n" + "=" * 70)
    logger.info("FULL PIPELINE TEST")
    logger.info("=" * 70)
    logger.info("   Running: Scout -> Analyst -> Trader -> Guardian")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    # Step 1: Scout - Find opportunities
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1/4: Scout")
    logger.info("=" * 70)
    await run_scout_test()

    # Step 2: Analyst - Research opportunities
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2/4: Analyst")
    logger.info("=" * 70)
    await run_analyst_test(opportunity_id=None)

    # Step 3: Trader - Execute analysis reports
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3/4: Trader")
    logger.info("=" * 70)
    await run_trader_test(opportunity_file=None)

    # Step 4: Guardian - Monitor positions
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4/4: Guardian")
    logger.info("=" * 70)
    await run_guardian_test()

    logger.info("\n" + "=" * 70)
    logger.info("FULL PIPELINE TEST COMPLETE")
    logger.info("=" * 70)
    logger.info("   Scout: Found opportunities and saved to test_data/opportunities/")
    logger.info("   Analyst: Skipped (requires --opportunity-id)")
    logger.info("   Trader: Skipped (requires --opportunity-file)")
    logger.info("   Guardian: Completed")
    logger.info("=" * 70 + "\n")


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for the test pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="Test Pipeline Runner - Run agents with test data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run Scout agent test (saves to test_data/)
    python -m coliseum.test_pipeline scout

    # Run Scout agent test without file persistence (debugging)
    python -m coliseum.test_pipeline scout --dry-run

    # Run Analyst agent test (requires opportunity ID)
    python -m coliseum.test_pipeline analyst --opportunity-id opp_abc12345

    # Run Trader agent test (paper mode)
    python -m coliseum.test_pipeline trader
    python -m coliseum.test_pipeline trader --opportunity-file KXBTCD-26JAN2317-T89999.99.md

    # Run Guardian agent test
    python -m coliseum.test_pipeline guardian

    # Run full pipeline
    python -m coliseum.test_pipeline run --full

    # Clean test data
    python -m coliseum.test_pipeline clean
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scout command
    scout_parser = subparsers.add_parser("scout", help="Run Scout agent to find opportunities")
    scout_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run agent without saving files (debugging mode)",
    )

    # Analyst command
    analyst_parser = subparsers.add_parser("analyst", help="Run Analyst agent to research opportunities")
    analyst_parser.add_argument(
        "--opportunity-id",
        type=str,
        default=None,
        help="Specific opportunity ID to analyze (no-op if omitted)",
    )

    # Trader command
    trader_parser = subparsers.add_parser("trader", help="Run Trader agent to execute analyses")
    trader_parser.add_argument(
        "--opportunity-file",
        type=str,
        default=None,
        help="Opportunity file name or path (default: newest in test_data/opportunities/)",
    )
    trader_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log tool calls and results from the trader agent",
    )

    # Guardian command
    subparsers.add_parser("guardian", help="Run Guardian agent to monitor positions")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument(
        "--full",
        action="store_true",
        help="Run full pipeline: Scout -> Analyst -> Trader -> Guardian",
    )

    # Clean command
    subparsers.add_parser("clean", help="Clean all test data")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "scout":
            asyncio.run(run_scout_test(dry_run=args.dry_run))
            sys.exit(0)

        elif args.command == "analyst":
            asyncio.run(run_analyst_test(opportunity_id=args.opportunity_id))
            sys.exit(0)

        elif args.command == "trader":
            asyncio.run(
                run_trader_test(
                    opportunity_file=args.opportunity_file,
                    verbose=args.verbose,
                )
            )
            sys.exit(0)

        elif args.command == "guardian":
            asyncio.run(run_guardian_test())
            sys.exit(0)

        elif args.command == "run":
            if args.full:
                asyncio.run(run_full_pipeline())
            else:
                logger.error("Please specify --full to run the complete pipeline")
                sys.exit(1)
            sys.exit(0)

        elif args.command == "clean":
            clean_test_data()
            sys.exit(0)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
