"""Coliseum CLI entry point."""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

from coliseum import __version__
from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian import run_guardian
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import get_settings
from coliseum.pipeline import run_pipeline
from coliseum.scheduler import start_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

def _init_logfire() -> None:
    """Initialize Logfire if available, without failing commands."""
    try:
        from coliseum.observability import initialize_logfire

        initialize_logfire(get_settings())
    except Exception as e:
        logger.warning(f"Failed to initialize Logfire: {e}")


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize data directory structure and configuration files."""
    data_dir = Path("data").resolve()

    try:
        data_dir.mkdir(exist_ok=True)
        logger.info(f"Created data directory: {data_dir}")

        subdirs = [
            "opportunities",
            "positions/open",
            "positions/closed",
            "trades",
        ]

        for subdir in subdirs:
            (data_dir / subdir).mkdir(parents=True, exist_ok=True)

        logger.info("Created all subdirectories")

        config_path = data_dir / "config.yaml"
        if not config_path.exists():
            config_template = """# Coliseum Configuration
# This file contains operational parameters for the autonomous trading system.
# API keys and secrets should be stored in .env file, not here.

trading:
  paper_mode: true
  initial_bankroll: 100.00

risk:
  max_position_pct: 0.10
  max_single_trade_usd: 1000.00
  min_edge_threshold: 0.05
  min_ev_threshold: 0.10
  kelly_fraction: 0.25

scheduler:
  scout_full_scan_minutes: 60
  guardian_position_check_minutes: 15
  guardian_news_scan_minutes: 30

scout:
  min_volume: 10000
  min_liquidity_cents: 10
  max_close_hours: 72
  edge_min_close_hours: 96
  edge_max_close_hours: 240
  edge_min_price: 10
  edge_max_price: 90

analyst:
  max_research_time_seconds: 300

guardian:
  profit_target_pct: 0.50
  stop_loss_pct: 0.30

execution:
  use_limit_orders_only: true
  max_slippage_pct: 0.05
  order_check_interval_seconds: 300
  max_reprice_attempts: 3
  reprice_aggression: 0.02
  min_fill_pct_to_keep: 0.25
  max_order_age_minutes: 60
"""
            config_path.write_text(config_template)
            logger.info(f"Created config template: {config_path}")
        else:
            logger.info(f"Config file already exists: {config_path}")

        state_path = data_dir / "state.yaml"
        if not state_path.exists():
            state_template = """# Coliseum Portfolio State
# This file is the single source of truth for the current system state.
# Updated automatically by agents - do not edit manually.

last_updated: null

portfolio:
  total_value: 100.00
  cash_balance: 100.00
  positions_value: 0.00

open_positions: []
"""
            state_path.write_text(state_template)
            logger.info(f"Created state template: {state_path}")
        else:
            logger.info(f"State file already exists: {state_path}")

        print(f"\n✓ Data directory initialized at {data_dir}")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Review and customize data/config.yaml if needed")
        print("3. Run 'python -m coliseum config' to verify configuration")
        print("4. Run 'python -m coliseum run' to start the system\n")

        return 0

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        print(f"\n❌ Initialization failed: {e}\n")
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Display merged configuration."""
    try:
        settings = get_settings()

        print("\n=== Coliseum Configuration ===\n")
        print(f"Data Directory: {settings.data_dir}\n")

        print("Trading:")
        print(f"  Paper Mode: {settings.trading.paper_mode}")
        print(f"  Initial Bankroll: ${settings.trading.initial_bankroll:,.2f}\n")

        print("Risk Management:")
        print(f"  Max Position: {settings.risk.max_position_pct:.0%}")
        print(f"  Max Single Trade: ${settings.risk.max_single_trade_usd:,.2f}")
        print(f"  Min Edge: {settings.risk.min_edge_threshold:.0%}")
        print(f"  Min EV: {settings.risk.min_ev_threshold:.0%}")
        print(f"  Kelly Fraction: {settings.risk.kelly_fraction}\n")

        print("Scheduler (minutes):")
        print(f"  Scout Full Scan: {settings.scheduler.scout_full_scan_minutes}")
        print(f"  Guardian Position Check: {settings.scheduler.guardian_position_check_minutes}")
        print(f"  Guardian News Scan: {settings.scheduler.guardian_news_scan_minutes}\n")

        print("Scout:")
        print(f"  Min Volume: {settings.scout.min_volume:,} contracts")
        print(f"  Min Liquidity: {settings.scout.min_liquidity_cents}¢ spread")
        print(f"  Max Close Hours: {settings.scout.max_close_hours}h\n")

        print("Analyst:")
        print(f"  Max Research Time: {settings.analyst.max_research_time_seconds}s\n")

        print("Guardian:")
        print(f"  Profit Target: {settings.guardian.profit_target_pct:.0%}")
        print(f"  Stop Loss: {settings.guardian.stop_loss_pct:.0%}\n")

        print("Execution:")
        print(f"  Use Limit Orders Only: {settings.execution.use_limit_orders_only}")
        print(f"  Max Slippage: {settings.execution.max_slippage_pct:.0%}")
        print(f"  Order Check Interval: {settings.execution.order_check_interval_seconds}s")
        print(f"  Max Reprice Attempts: {settings.execution.max_reprice_attempts}")
        print(f"  Max Order Age: {settings.execution.max_order_age_minutes} min\n")

        print("API Keys:")
        print(f"  Kalshi: {'✓ Set' if settings.kalshi_api_key else '✗ Not set'}")
        print(f"  RSA Private Key: {'✓ Set' if settings.rsa_private_key else '✗ Not set'}")
        print(f"  Exa AI: {'✓ Set' if settings.exa_api_key else '✗ Not set'}")
        print(f"  OpenRouter: {'✓ Set' if settings.openrouter_api_key else '✗ Not set'}")
        print(f"  Logfire: {'✓ Set' if settings.logfire_token else '✗ Not set'}\n")

        return 0

    except ValidationError as e:
        print("\n❌ Configuration Error:\n")
        for error in e.errors():
            print(f"  • {'.'.join(str(x) for x in error['loc'])}: {error['msg']}")
        print()
        return 1
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        print(f"\n❌ Failed to load configuration: {e}\n")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Display current portfolio status."""
    try:
        settings = get_settings()
        state_path = settings.data_dir / "state.yaml"

        if not state_path.exists():
            print(f"\n❌ State file not found: {state_path}")
            print("Run 'python -m coliseum init' to create it.\n")
            return 1

        with open(state_path, "r") as f:
            state = yaml.safe_load(f)

        print("\n=== Coliseum Portfolio Status ===\n")

        portfolio = state.get("portfolio", {})
        print("Portfolio:")
        print(f"  Total Value: ${portfolio.get('total_value', 0):,.2f}")
        print(f"  Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}")
        print(f"  Positions Value: ${portfolio.get('positions_value', 0):,.2f}\n")

        positions = state.get("open_positions", [])
        print(f"Open Positions: {len(positions)}")
        if positions:
            for i, pos in enumerate(positions[:5], 1):
                print(f"  {i}. {pos.get('market_ticker', 'Unknown')}")
            if len(positions) > 5:
                print(f"  ... and {len(positions) - 5} more")
        else:
            print("  (None)")
        print()

        return 0

    except Exception as e:
        logger.error(f"Failed to read status: {e}")
        print(f"\n❌ Failed to read status: {e}\n")
        return 1


def cmd_scout(args: argparse.Namespace) -> int:
    """Run a manual Scout market scan."""
    _init_logfire()

    try:
        print(f"\n=== Scout Scan ===\n")

        result = asyncio.run(run_scout())

        print(f"✓ Scout scan complete\n")
        print(f"Markets scanned: {result.markets_scanned}")
        print(f"Opportunities found: {result.opportunities_found}")
        print(f"Filtered out: {result.filtered_out}")
        print(f"\nSummary:\n{result.scan_summary}\n")

        if result.opportunities:
            print(f"Queued {len(result.opportunities)} opportunities for Analyst:")
            for opp in result.opportunities[:5]:
                print(f"  • {opp.market_ticker}")
            if len(result.opportunities) > 5:
                print(f"  ... and {len(result.opportunities) - 5} more")
            print()

        return 0

    except Exception as e:
        logger.error(f"Scout scan failed: {e}", exc_info=True)
        print(f"\n❌ Scout scan failed: {e}\n")
        return 1


def cmd_guardian(args: argparse.Namespace) -> int:
    """Run Guardian reconciliation manually."""
    _init_logfire()

    try:
        print("\n=== Guardian Reconciler ===\n")

        result = asyncio.run(run_guardian())

        print("✓ Guardian reconciliation complete\n")
        print(f"Positions Synced: {result.positions_synced}")
        print(f"Entries Inspected: {result.reconciliation.entries_inspected}")
        print(f"Kept Open: {result.reconciliation.kept_open}")
        print(f"Closed: {result.reconciliation.newly_closed}")
        print(f"Skipped (no trade): {result.reconciliation.skipped_no_trade}\n")

        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  • Position missing opportunity_id: {warning}")
            print()

        return 0

    except Exception as e:
        logger.error(f"Guardian failed: {e}", exc_info=True)
        print(f"\n❌ Guardian failed: {e}\n")
        return 1


def cmd_analyst(args: argparse.Namespace) -> int:
    """Run Analyst pipeline (Researcher + Recommender) manually."""
    _init_logfire()

    try:
        opportunity_id = args.opportunity_id
        print(f"\n=== Analyst Pipeline ===\n")
        print(f"Opportunity ID: {opportunity_id}\n")

        settings = get_settings()
        result = asyncio.run(run_analyst(opportunity_id, settings))

        print(f"✓ Analyst pipeline complete\n")
        print(f"Estimated True Probability: {result.estimated_true_probability:.0%}")
        print(f"Current Market Price: {result.current_market_price:.0%}")
        print(f"Edge: {result.edge:+.2%}")
        print(f"Expected Value: {result.expected_value:+.2%}")
        print(f"Suggested Position: {result.suggested_position_pct:.1%}\n")
        print("Trade decision pending (no BUY/NO decision made).\n")

        return 0

    except Exception as e:
        logger.error(f"Analyst failed: {e}", exc_info=True)
        print(f"\n❌ Analyst failed: {e}\n")
        return 1


def cmd_trader(args: argparse.Namespace) -> int:
    """Run Trader agent to execute or reject a trade recommendation."""
    _init_logfire()

    try:
        opportunity_id = args.opportunity_id
        print(f"\n=== Trader Agent ===\n")
        print(f"Opportunity ID: {opportunity_id}\n")

        settings = get_settings()
        result = asyncio.run(run_trader(opportunity_id, settings))

        print(f"✓ Trader decision complete\n")
        print(f"Decision: {result.decision.action}")
        print(f"Confidence: {result.decision.confidence:.0%}")
        print(f"Execution Status: {result.execution_status}\n")
        
        if result.decision.reasoning:
            print(f"Reasoning:\n{result.decision.reasoning}\n")
        

        if result.execution_status in ["filled", "partial"]:
            print(f"Order ID: {result.order_id}")
            print(f"Contracts Filled: {result.contracts_filled}")
            print(f"Fill Price: {result.fill_price:.2%}")
            print(f"Total Cost: ${result.total_cost_usd:.2f}\n")

        return 0

    except Exception as e:
        logger.error(f"Trader failed: {e}", exc_info=True)
        print(f"\n❌ Trader failed: {e}\n")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Start the autonomous trading system."""
    try:
        _init_logfire()

        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        settings = get_settings()

        print("\n=== Coliseum Autonomous Trading System ===\n")
        print(f"Version: {__version__}")
        print(f"Mode: {'PAPER TRADING' if settings.trading.paper_mode else 'LIVE TRADING'}")
        print(f"Bankroll: ${settings.trading.initial_bankroll:,.2f}")
        print(f"Data Directory: {settings.data_dir}\n")

        if args.once:
            print("Running full pipeline once (Scout -> Analyst -> Trader)...\n")
            asyncio.run(run_pipeline(settings))
            print("\nPipeline run complete.\n")
            return 0

        print("Starting scheduler...\n")
        start_scheduler(settings)

        return 0

    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal. Shutting down...\n")
        return 0
    except Exception as e:
        logger.error(f"Failed to start system: {e}", exc_info=True)
        print(f"\nFailed to start: {e}\n")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Coliseum: Autonomous AI trading system for prediction markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Coliseum {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parser_init = subparsers.add_parser(
        "init",
        help="Initialize data directory and configuration files",
    )
    parser_init.set_defaults(func=cmd_init)

    parser_config = subparsers.add_parser(
        "config",
        help="Display merged configuration",
    )
    parser_config.set_defaults(func=cmd_config)

    parser_status = subparsers.add_parser(
        "status",
        help="Display current portfolio status",
    )
    parser_status.set_defaults(func=cmd_status)

    parser_scout = subparsers.add_parser(
        "scout",
        help="Run Scout market scan manually",
    )
    parser_scout.set_defaults(func=cmd_scout)

    parser_guardian = subparsers.add_parser(
        "guardian",
        help="Run Guardian reconciliation manually",
    )
    parser_guardian.set_defaults(func=cmd_guardian)

    parser_analyst = subparsers.add_parser(
        "analyst",
        help="Run Analyst pipeline (Researcher + Recommender) manually",
    )
    parser_analyst.add_argument(
        "--opportunity-id",
        required=True,
        help="Opportunity ID to analyze",
    )
    parser_analyst.set_defaults(func=cmd_analyst)

    parser_trader = subparsers.add_parser(
        "trader",
        help="Run Trader agent to execute or reject a trade recommendation",
    )
    parser_trader.add_argument(
        "--opportunity-id",
        required=True,
        help="Opportunity ID to trade",
    )
    parser_trader.set_defaults(func=cmd_trader)

    parser_run = subparsers.add_parser(
        "run",
        help="Start the autonomous trading system",
    )
    parser_run.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser_run.add_argument(
        "--once",
        action="store_true",
        help="Run the full pipeline once (Scout -> Analyst -> Trader) then exit",
    )
    parser_run.set_defaults(func=cmd_run)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
