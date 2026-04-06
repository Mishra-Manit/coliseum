"""Coliseum CLI entry point."""

import argparse
import asyncio
import functools
import logging
import sys
from pathlib import Path
import uvicorn

from pydantic import ValidationError

from coliseum import __version__
from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian import run_guardian
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import get_settings
from coliseum.observability import initialize_logfire
from coliseum.pipeline import run_pipeline
from coliseum.runtime import bootstrap_runtime
from coliseum.services.supabase.repositories.portfolio import load_state_from_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

bootstrap_runtime()


def _cli_command(label: str):
    """Decorator that wraps CLI commands with consistent error handling."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(args: argparse.Namespace) -> int:
            try:
                return fn(args)
            except KeyboardInterrupt:
                print(f"\n\nInterrupted.\n")
                return 0
            except Exception as e:
                logger.error("%s failed: %s", label, e, exc_info=True)
                print(f"\n❌ {label} failed: {e}\n")
                return 1

        return wrapper

    return decorator


def _init_logfire() -> None:
    """Initialize Logfire if available, without failing commands."""
    try:
        initialize_logfire(get_settings())
    except Exception as e:
        logger.warning(f"Failed to initialize Logfire: {e}")


@_cli_command("Initialization")
def cmd_init(args: argparse.Namespace) -> int:
    """Initialize data directory structure and configuration files."""
    data_dir = Path("data").resolve()

    data_dir.mkdir(exist_ok=True)
    logger.info(f"Created data directory: {data_dir}")

    config_path = data_dir / "config.yaml"
    if not config_path.exists():
        config_template = """# Coliseum Configuration
# This file contains operational parameters for the autonomous trading system.
# API keys and secrets should be stored in .env file, not here.

trading:
  paper_mode: true
  contracts: 5

scout:
  market_fetch_limit: 20000
  min_close_hours: 0
  max_close_hours: 48
  min_price: 92
  max_price: 96
  max_spread_cents: 3
  min_volume: 1000

guardian:
  profit_target_pct: 0.70
  stop_loss_pct: 0.10
  max_hold_days: 5

execution:
  max_slippage_pct: 0.05
  order_check_interval_seconds: 120
  max_reprice_attempts: 3
  reprice_aggression: 0.02
  min_fill_pct_to_keep: 0.25
  max_order_age_minutes: 60

daemon:
  heartbeat_interval_minutes: 60
  guardian_interval_minutes: 15
  max_consecutive_failures: 5

telegram_send_alerts: true
"""
        config_path.write_text(config_template)
        logger.info(f"Created config template: {config_path}")
    else:
        logger.info(f"Config file already exists: {config_path}")

    print(f"\n✓ Data directory initialized at {data_dir}")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Review and customize data/config.yaml if needed")
    print("3. Run 'python -m coliseum config' to verify configuration")
    print("4. Run 'python -m coliseum pipeline' to run the pipeline once\n")

    return 0


@_cli_command("Configuration")
def cmd_config(args: argparse.Namespace) -> int:
    """Display merged configuration."""
    try:
        settings = get_settings()

        print("\n=== Coliseum Configuration ===\n")
        print(f"Data Directory: {settings.data_dir}\n")

        print("Trading:")
        print(f"  Paper Mode: {settings.trading.paper_mode}\n")

        print("Scout:")
        print(f"  Price Band: {settings.scout.min_price}-{settings.scout.max_price}¢")
        print(
            "  Close Window: "
            f"{settings.scout.min_close_hours}-{settings.scout.max_close_hours}h"
        )
        print(f"  Max Spread: {settings.scout.max_spread_cents}¢")
        print(f"  Min Volume: {settings.scout.min_volume:,} contracts\n")

        print("Guardian:")
        print(f"  Stop Loss Price: {settings.guardian.stop_loss_price:.2f}\n")

        print("Execution:")
        print(f"  Max Slippage: {settings.execution.max_slippage_pct:.0%}")
        print(f"  Order Check Interval: {settings.execution.order_check_interval_seconds}s")
        print(f"  Max Reprice Attempts: {settings.execution.max_reprice_attempts}")
        print(f"  Max Order Age: {settings.execution.max_order_age_minutes} min\n")

        print("Daemon:")
        print(f"  Heartbeat Interval: {settings.daemon.heartbeat_interval_minutes}m")
        print(f"  Guardian Interval: {settings.daemon.guardian_interval_minutes}m")
        print(f"  Max Consecutive Failures: {settings.daemon.max_consecutive_failures}\n")

        print("API Keys:")
        if settings.kalshi_api_key:
            kalshi_status = "✓ Set"
        else:
            kalshi_status = "✗ Not set"
        print(f"  Kalshi: {kalshi_status}")

        if settings.rsa_private_key:
            rsa_status = "✓ Set"
        else:
            rsa_status = "✗ Not set"
        print(f"  RSA Private Key: {rsa_status}")

        if settings.logfire_token:
            logfire_status = "✓ Set"
        else:
            logfire_status = "✗ Not set"
        print(f"  Logfire: {logfire_status}\n")

        return 0

    except ValidationError as e:
        print("\n❌ Configuration Error:\n")
        for error in e.errors():
            print(f"  • {'.'.join(str(x) for x in error['loc'])}: {error['msg']}")
        print()
        return 1


@_cli_command("Status")
def cmd_status(args: argparse.Namespace) -> int:
    """Display current portfolio status."""
    state = asyncio.run(load_state_from_db())

    print("\n=== Coliseum Portfolio Status ===\n")

    print("Portfolio:")
    print(f"  Total Value: ${state.portfolio.total_value:,.2f}")
    print(f"  Cash Balance: ${state.portfolio.cash_balance:,.2f}")
    print(f"  Positions Value: ${state.portfolio.positions_value:,.2f}\n")

    positions = state.open_positions
    print(f"Open Positions: {len(positions)}")
    if positions:
        for i, pos in enumerate(positions[:5], 1):
            print(f"  {i}. {pos.market_ticker}")
        if len(positions) > 5:
            print(f"  ... and {len(positions) - 5} more")
    else:
        print("  (None)")
    print()

    return 0


@_cli_command("Scout scan")
def cmd_scout(args: argparse.Namespace) -> int:
    """Run a manual Scout market scan."""
    _init_logfire()

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


@_cli_command("Guardian")
def cmd_guardian(args: argparse.Namespace) -> int:
    """Run Guardian reconciliation manually."""
    _init_logfire()

    print("\n=== Guardian Reconciler ===\n")

    result = asyncio.run(run_guardian())

    print("✓ Guardian reconciliation complete\n")
    print(f"Positions Synced: {result.positions_synced}")
    print(f"Entries Inspected: {result.reconciliation.entries_inspected}")
    print(f"Kept Open: {result.reconciliation.kept_open}")
    print(f"Closed: {result.reconciliation.newly_closed}")
    print(f"Stop-Loss Exits: {result.reconciliation.stop_loss_exits}")
    print(f"Warnings: {result.reconciliation.warnings}\n")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  • Position missing opportunity_id: {warning}")
        print()

    return 0


@_cli_command("Analyst")
def cmd_analyst(args: argparse.Namespace) -> int:
    """Run Analyst pipeline (Researcher + Recommender) manually."""
    _init_logfire()

    opportunity_id = args.id
    print(f"\n=== Analyst Pipeline ===\n")
    print(f"Opportunity ID: {opportunity_id}\n")

    settings = get_settings()
    result = asyncio.run(run_analyst(opportunity_id, settings))

    print(f"✓ Analyst pipeline complete\n")
    print(f"Status: {result.status}")
    if result.research_completed_at:
        research_status = "yes"
    else:
        research_status = "no"
    print(f"Research Completed: {research_status}")

    if result.recommendation_completed_at:
        recommendation_status = "yes"
    else:
        recommendation_status = "no"
    print(f"Recommendation Completed: {recommendation_status}\n")
    print("Trade decision pending (no BUY/NO decision made).\n")

    return 0


@_cli_command("Trader")
def cmd_trader(args: argparse.Namespace) -> int:
    """Run Trader agent to execute or reject a trade recommendation."""
    _init_logfire()

    opportunity_id = args.id
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


@_cli_command("API server")
def cmd_api(args: argparse.Namespace) -> int:
    """Start the dashboard API server (no trading daemon)."""

    print(f"\n=== Coliseum Dashboard API ===\n")
    print(f"Starting server on http://{args.host}:{args.port}")
    if args.reload:
        reload_status = "enabled"
    else:
        reload_status = "disabled"
    print(f"Auto-reload: {reload_status}\n")

    uvicorn.run(
        "coliseum.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )

    return 0


@_cli_command("Daemon")
def cmd_daemon(args: argparse.Namespace) -> int:
    """Start the autonomous daemon with integrated dashboard API."""
    _init_logfire()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()

    print("\n=== Coliseum Autonomous Daemon ===")
    print(f"\nVersion: {__version__}")
    if settings.trading.paper_mode:
        daemon_mode = "PAPER TRADING"
    else:
        daemon_mode = "LIVE TRADING"
    print(f"Mode: {daemon_mode}")
    print(f"Data Directory: {settings.data_dir}")
    print(f"Heartbeat Interval: {settings.daemon.heartbeat_interval_minutes}m")
    print(f"Guardian Interval: {settings.daemon.guardian_interval_minutes}m")
    print(f"Max Consecutive Failures: {settings.daemon.max_consecutive_failures}")
    print(f"Dashboard: http://{args.host}:{args.port}")
    print("\nStarting daemon + dashboard... (Ctrl+C to stop)\n")

    uvicorn.run(
        "coliseum.api.server:daemon_app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="warning",
    )

    print("\nDaemon stopped cleanly.\n")
    return 0


@_cli_command("Pipeline")
def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run the full pipeline once (Guardian -> Scout -> Analyst -> Trader)."""
    _init_logfire()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()

    print("\n=== Coliseum Autonomous Trading System ===\n")
    print(f"Version: {__version__}")
    if settings.trading.paper_mode:
        pipeline_mode = "PAPER TRADING"
    else:
        pipeline_mode = "LIVE TRADING"
    print(f"Mode: {pipeline_mode}")
    print(f"Data Directory: {settings.data_dir}\n")

    print("Running full pipeline once (Guardian -> Scout -> Analyst -> Trader)...\n")
    asyncio.run(run_pipeline(settings))
    print("\nPipeline run complete.\n")
    return 0


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
        "--id",
        required=True,
        help="Opportunity ID to analyze (e.g. opp_abc12345)",
    )
    parser_analyst.set_defaults(func=cmd_analyst)

    parser_trader = subparsers.add_parser(
        "trader",
        help="Run Trader agent to execute or reject a trade recommendation",
    )
    parser_trader.add_argument(
        "--id",
        required=True,
        help="Opportunity ID to trade (e.g. opp_abc12345)",
    )
    parser_trader.set_defaults(func=cmd_trader)

    parser_api = subparsers.add_parser(
        "api",
        help="Start the dashboard API server only (no trading daemon)",
    )
    parser_api.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser_api.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port to bind to (default: 9000)",
    )
    parser_api.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser_api.set_defaults(func=cmd_api)

    parser_daemon = subparsers.add_parser(
        "daemon",
        help="Start the autonomous daemon with integrated dashboard API",
    )
    parser_daemon.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind dashboard to (default: 0.0.0.0)",
    )
    parser_daemon.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port to bind dashboard to (default: 9000)",
    )
    parser_daemon.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser_daemon.set_defaults(func=cmd_daemon)

    parser_pipeline = subparsers.add_parser(
        "pipeline",
        help="Run the full pipeline once (testing/debug)",
    )
    parser_pipeline.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser_pipeline.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
