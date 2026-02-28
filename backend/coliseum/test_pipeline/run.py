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
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_file)

# Ensure backend is in path for direct execution
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from coliseum.test_pipeline.config import TEST_DATA_DIR
from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian.main import (
    _find_positions_without_opportunity_id,
    reconcile_closed_positions,
)
from coliseum.agents.guardian.models import GuardianResult
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
import coliseum.config as config_module
from coliseum.config import get_settings
from coliseum.observability import initialize_logfire
from coliseum.services.kalshi import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.files import (
    find_opportunity_file_by_id,
    get_opportunity_strategy_by_id,
    load_opportunity_from_file,
)
from coliseum.storage.state import load_state
from coliseum.storage.sync import sync_portfolio_from_kalshi


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
            "\n"
            "scout:\n",
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
            "open_positions: []\n",
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
    
    init_test_data_structure()
    logger.info("Test data directory cleaned and reinitialized")


def _override_data_dir() -> None:
    """Override the data directory to use test_data/ for this process.
    
    This modifies the Settings singleton to point to test_data/ instead of data/.
    Must be called before any agent code runs.
    """
    # Clear the settings cache so it will be reloaded with new data_dir
    get_settings.cache_clear()
    
    # Set environment variable to override data_dir
    os.environ["DATA_DIR"] = str(TEST_DATA_DIR)
    
    # Monkey-patch get_settings to use test_data_dir
    
    original_get_settings = config_module.get_settings.__wrapped__
    
    def patched_get_settings():
        settings = original_get_settings()
        # Override data_dir to test directory
        object.__setattr__(settings, 'data_dir', TEST_DATA_DIR)
        return settings
    
    # Replace the cached function
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

async def run_scout_test() -> "ScoutOutput | None":
    """Run Scout agent using production code.

    Returns:
        ScoutOutput with discovered opportunities, or None on failure.
    """
    logger.info("\n" + "=" * 70)
    logger.info("Scout Agent Test")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    # Run the production Scout agent
    settings = get_settings()

    logger.info("Running production Scout agent...")
    logger.info("-" * 70)

    try:
        output = await run_scout(strategy=settings.strategy)

        logger.info("\n" + "=" * 70)
        logger.info("Results")
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
        logger.info(
            f"Scout test complete - {len(output.opportunities)} opportunities saved to test_data/"
        )
        logger.info("=" * 70 + "\n")
        
        return output

    except Exception as e:
        logger.exception(f"Scout test failed: {e}")
        return None


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

    settings = get_settings()
    opp_file = find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")
    strategy = get_opportunity_strategy_by_id(opportunity_id)
    logger.info(f"   Opportunity file: {opp_file}")
    logger.info(f"   Detected strategy: {strategy}")

    try:
        opportunity = await run_analyst(
            opportunity_id=opportunity_id,
            settings=settings,
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

async def run_trader_test(
    opportunity_file: str | None = None,
    verbose: bool = False,
    live: bool = False,
) -> None:
    """Run Trader agent on a specific opportunity file."""
    logger.info("\n" + "=" * 70)
    mode_label = "LIVE EXECUTION" if live else "PAPER MODE"
    logger.info(f"Trader Agent Test ({mode_label})")
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

    opportunity = load_opportunity_from_file(opp_file)
    logger.info(f"   Selected opportunity: {opportunity.id}")
    logger.info(f"   Market: {opportunity.market_ticker}")

    settings = get_settings()
    settings.trading.paper_mode = not live

    if settings.trading.paper_mode:
        logger.info("   Paper mode enabled; skipping Kalshi credential checks.")
    elif not settings.kalshi_api_key or not settings.get_rsa_private_key():
        logger.warning("   Missing Kalshi credentials; skipping live market check.")
        logger.info("   Set KALSHI_API_KEY and KALSHI_PRIVATE_KEY_PATH to run this test.")
        logger.info("\n" + "=" * 70)
        logger.info("Trader test complete (skipped)")
        logger.info("=" * 70 + "\n")
        return
    else:
        logger.warning("   LIVE mode enabled: orders can be placed on your Kalshi account.")

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

    logger.info("\n" + "=" * 70)
    logger.info("Trader test complete")
    logger.info("=" * 70 + "\n")


# =============================================================================
# Guardian Agent Test Runner
# =============================================================================

async def run_guardian_test() -> "GuardianResult | None":
    """Run Guardian agent to reconcile positions.

    Syncs portfolio state from Kalshi (local state in paper mode),
    then detects positions that closed since last sync and moves them
    to closed_positions in state.yaml.

    Returns:
        GuardianResult with reconciliation stats, or None on failure.
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

    settings = get_settings()

    logger.info(f"   Paper mode: {settings.trading.paper_mode}")
    logger.info(f"   Data dir: {settings.data_dir}")
    logger.info("-" * 70)

    kalshi_config = KalshiConfig(paper_mode=True)
    private_key_pem = ""
    if not settings.trading.paper_mode and settings.get_rsa_private_key():
        private_key_pem = settings.get_rsa_private_key()

    try:
        async with KalshiClient(
            config=kalshi_config,
            api_key=settings.kalshi_api_key if private_key_pem else None,
            private_key_pem=private_key_pem or None,
        ) as client:
            pre_sync_state = load_state()
            state = await sync_portfolio_from_kalshi(client)
            logger.info(f"   Synced state: {len(state.open_positions)} open positions")
            logger.info(
                f"   Portfolio: cash=${state.portfolio.cash_balance:.2f}, "
                f"positions=${state.portfolio.positions_value:.2f}"
            )

            fills = await client.get_fills()
            logger.info(f"   Fills from Kalshi: {len(fills)}")

            state, stats = await reconcile_closed_positions(
                old_open=pre_sync_state.open_positions,
                new_state=state,
                fills=fills,
                client=client,
            )

        missing = _find_positions_without_opportunity_id(state)
        for missing_key in missing:
            logger.warning(f"   Position missing opportunity_id: {missing_key}")

        result = GuardianResult(
            positions_synced=len(state.open_positions),
            reconciliation=stats,
            warnings=missing,
        )

        logger.info("\n" + "=" * 70)
        logger.info("Guardian results")
        logger.info("=" * 70)
        logger.info(f"   Positions synced: {result.positions_synced}")
        logger.info(f"   Entries inspected: {stats.entries_inspected}")
        logger.info(f"   Kept open: {stats.kept_open}")
        logger.info(f"   Newly closed: {stats.newly_closed}")
        logger.info(f"   Skipped (no trade): {stats.skipped_no_trade}")
        logger.info(f"   Reconciliation warnings: {stats.warnings}")
        if result.warnings:
            logger.info(f"   Missing opportunity_id: {', '.join(result.warnings)}")

        logger.info("\n" + "=" * 70)
        logger.info("Guardian test complete")
        logger.info("=" * 70 + "\n")

        return result

    except Exception as e:
        logger.exception(f"Guardian test failed: {e}")
        return None


# =============================================================================
# Full Pipeline Runner
# =============================================================================

async def run_full_pipeline() -> None:
    """Run complete pipeline: Scout -> (Analyst -> Trader) per opportunity.

    This demonstrates the full autonomous trading flow in test mode.
    For each opportunity discovered by Scout, runs Analyst then Trader sequentially.
    """
    logger.info("\n" + "=" * 70)
    logger.info("FULL PIPELINE TEST")
    logger.info("=" * 70)
    logger.info("   Running: Scout -> (Analyst -> Trader) for each opportunity")
    logger.info("=" * 70)

    # Initialize test data structure
    init_test_data_structure()

    # Override data directory to use test_data/
    _override_data_dir()

    # Initialize Logfire BEFORE agent imports
    _initialize_test_logfire()

    # Step 1: Scout - Find opportunities
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: Scout - Discovering opportunities")
    logger.info("=" * 70)
    
    settings = get_settings()
    scout_output = await run_scout(strategy=settings.strategy)
    
    if not scout_output or not scout_output.opportunities:
        logger.warning("Scout found no opportunities. Pipeline complete.")
        return
    
    opportunities = scout_output.opportunities
    total_opps = len(opportunities)
    logger.info(f"Scout found {total_opps} opportunities")
    
    settings.trading.paper_mode = True
    
    # Process each opportunity sequentially: Analyst -> Trader
    for i, opp in enumerate(opportunities, 1):
        logger.info("\n" + "=" * 70)
        logger.info(f"PROCESSING OPPORTUNITY {i}/{total_opps}: {opp.market_ticker}")
        logger.info("=" * 70)
        
        # Step 2: Analyst - Research this opportunity
        logger.info(f"\n--- Analyst Agent ({i}/{total_opps}) ---")
        try:
            analyzed_opp = await run_analyst(
                opportunity_id=opp.id,
                settings=settings,
            )
            logger.info(f"   Status: {analyzed_opp.status}")
            logger.info(f"   Edge: {analyzed_opp.edge:+.2%}" if analyzed_opp.edge else "   Edge: N/A")
            logger.info(f"   EV: {analyzed_opp.expected_value:+.2%}" if analyzed_opp.expected_value else "   EV: N/A")
        except Exception as e:
            logger.error(f"   Analyst failed for {opp.id}: {e}")
            continue
        
        # Step 3: Trader - Execute trade decision for this opportunity
        logger.info(f"\n--- Trader Agent ({i}/{total_opps}) ---")
        try:
            trader_output = await run_trader(
                opportunity_id=opp.id,
                settings=settings,
            )
            logger.info(f"   Decision: {trader_output.decision.action}")
            logger.info(f"   Confidence: {trader_output.decision.confidence:.2%}")
            logger.info(f"   Execution: {trader_output.execution_status}")
        except Exception as e:
            logger.error(f"   Trader failed for {opp.id}: {e}")
            continue
        
        logger.info(f"\nCompleted opportunity {i}/{total_opps}")

    # Step 4: Guardian - Reconcile positions
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4: Guardian - Reconciling positions")
    logger.info("=" * 70)

    kalshi_config = KalshiConfig(paper_mode=True)
    private_key_pem = ""
    if not settings.trading.paper_mode and settings.get_rsa_private_key():
        private_key_pem = settings.get_rsa_private_key()

    try:
        async with KalshiClient(
            config=kalshi_config,
            api_key=settings.kalshi_api_key if private_key_pem else None,
            private_key_pem=private_key_pem or None,
        ) as client:
            pre_sync_state = load_state()
            state = await sync_portfolio_from_kalshi(client)
            fills = await client.get_fills()
            state, guardian_stats = await reconcile_closed_positions(
                old_open=pre_sync_state.open_positions,
                new_state=state,
                fills=fills,
                client=client,
            )

        missing = _find_positions_without_opportunity_id(state)

        logger.info(f"   Positions synced: {len(state.open_positions)}")
        logger.info(
            f"   Reconciliation: inspected={guardian_stats.entries_inspected} "
            f"kept_open={guardian_stats.kept_open} "
            f"closed={guardian_stats.newly_closed} "
            f"skipped={guardian_stats.skipped_no_trade}"
        )
        if missing:
            logger.warning(f"   Missing opportunity_id: {', '.join(missing)}")
    except Exception as e:
        logger.error(f"   Guardian failed: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("FULL PIPELINE TEST COMPLETE")
    logger.info("=" * 70)
    logger.info(f"   Processed {total_opps} opportunities sequentially")
    logger.info("   Flow: Scout -> (Analyst -> Trader) for each -> Guardian")
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
    subparsers.add_parser("scout", help="Run Scout agent to find opportunities")

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
    trader_parser.add_argument(
        "--live",
        action="store_true",
        help="Execute with live Kalshi trading (default: paper mode)",
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
            asyncio.run(run_scout_test())
            sys.exit(0)

        elif args.command == "analyst":
            asyncio.run(run_analyst_test(opportunity_id=args.opportunity_id))
            sys.exit(0)

        elif args.command == "trader":
            asyncio.run(
                run_trader_test(
                    opportunity_file=args.opportunity_file,
                    verbose=args.verbose,
                    live=args.live,
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
