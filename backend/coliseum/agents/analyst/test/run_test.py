#!/usr/bin/env python3
"""
Analyst Pipeline Test Runner

Runs the full Analyst pipeline (Researcher + Recommender) with verbose output.
By default, creates a modeled opportunity with sample data and saves output.

Usage:
    # From backend/ directory (activate venv first):
    source venv/bin/activate
    python -m coliseum.agents.analyst.test.run_test

    # Or create a test opportunity first with Scout, then analyze it:
    python -m coliseum.agents.scout.test.run_test
    python -m coliseum.agents.analyst.test.run_test --opportunity-id <id from scout>

    # Dry-run mode (no file writes):
    python -m coliseum.agents.analyst.test.run_test --dry-run
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add backend to path if running directly
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("analyst.test")

# Reduce noise from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def _resolve_data_dir(data_dir: str, backend_path: Path) -> Path:
    """Resolve data dir relative to backend/ or repo root."""
    path = Path(data_dir)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "backend":
        return (backend_path.parent / path).resolve()
    return (backend_path / path).resolve()


async def run_researcher_test(
    opportunity_id: str | None,
    dry_run: bool = True,
    use_mock_event: bool = True,
    data_dir: str | None = None,
) -> None:
    """Execute a full Analyst pipeline run (Researcher + Recommender).

    Args:
        opportunity_id: Opportunity ID to analyze (optional if using mock event)
        dry_run: If True, don't save files (for testing)
        use_mock_event: If True, create a modeled opportunity for testing
        data_dir: Optional override for data directory (e.g., backend/test_data)
    """
    import os

    from coliseum.agents.analyst import run_analyst
    from coliseum.config import Settings
    from coliseum.storage.files import (
        OpportunitySignal,
        generate_opportunity_id,
        save_opportunity,
        find_opportunity_file,
    )
    from coliseum.storage.state import get_data_dir

    logger.info("=" * 70)
    logger.info("ANALYST PIPELINE TEST (RESEARCHER + RECOMMENDER)")
    logger.info("=" * 70)
    logger.info(f"Opportunity ID: {opportunity_id or '(mock event)'}")
    logger.info(f"Dry-run mode: {dry_run}")
    if data_dir:
        resolved_data_dir = str(_resolve_data_dir(data_dir, backend_path))
        os.environ["DATA_DIR"] = resolved_data_dir
        logger.info(f"Data dir override: {resolved_data_dir}")
    logger.info("-" * 70)

    try:
        # Load settings
        settings = Settings()
        settings.load_yaml_config()
        from coliseum.observability import initialize_logfire
        initialize_logfire(settings)

        if use_mock_event:
            mock_id = generate_opportunity_id()
            mock_suffix = uuid4().hex[:6].upper()
            opportunity = OpportunitySignal(
                id=mock_id,
                event_ticker=f"TEST-EVENT-{mock_suffix}",
                market_ticker=f"TEST-MARKET-{mock_suffix}",
                title="Will Don't Be Dumb have At least 120000 album sales the Hits Daily Double Top 50 Chart for January 23, 2026?",
                subtitle="At least 120,000 albums",
                yes_price=0.10,
                no_price=0.93,
                close_time=datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc),
                rationale=(
                    "Modeled opportunity for Researcher testing with a "
                    "balanced market price and ample time to close."
                ),
                discovered_at=datetime.now(timezone.utc),
                status="pending",
            )
            if not dry_run:
                save_opportunity(opportunity)
            opportunity_id = mock_id

        if not opportunity_id:
            raise ValueError("Opportunity ID is required when mock event is disabled.")

        # Run full analyst pipeline (researcher + recommender)
        analysis = await run_analyst(
            opportunity_id=opportunity_id,
            settings=settings,
            dry_run=dry_run,
        )

        # Extract research data from opportunity file
        from coliseum.storage.files import extract_research_from_opportunity
        analysis_path = find_opportunity_file(analysis.market_ticker)
        research_data = extract_research_from_opportunity(analysis_path) if analysis_path else {}

        # Print results
        logger.info("\n" + "=" * 70)
        logger.info("ANALYST OUTPUT")
        logger.info("=" * 70)
        logger.info(f"Opportunity ID: {analysis.id}")
        logger.info(f"Market Ticker: {analysis.market_ticker}")
        logger.info(f"Sources: {analysis.research_sources_count}")

        synthesis = research_data.get("synthesis", "")
        sources = research_data.get("sources", [])

        if synthesis:
            logger.info("\n--- Research Synthesis ---")
            logger.info(synthesis[:500] + "..." if len(synthesis) > 500 else synthesis)

        if sources:
            logger.info("\n--- Sources (first 5) ---")
            for i, source in enumerate(sources[:5], 1):
                logger.info(f"{i}. {source}")

        logger.info("\n" + "=" * 70)
        logger.info("TRADE EVALUATION")
        logger.info("=" * 70)
        logger.info(f"Action:                {analysis.action or 'PENDING'}")
        logger.info(f"Edge:                  {analysis.edge:+.1%}" if analysis.edge else "Edge:                  N/A")
        logger.info(f"Expected Value:        {analysis.expected_value:+.1%}" if analysis.expected_value else "Expected Value:        N/A")
        logger.info(f"Suggested Position:    {analysis.suggested_position_pct:.1%} of portfolio" if analysis.suggested_position_pct else "Suggested Position:    N/A")
        logger.info(f"Status:                {analysis.status}")

        logger.info("\n" + "=" * 70)
        if dry_run:
            logger.info("TEST COMPLETE - No data was saved to disk (dry-run mode)")
        else:
            analysis_path = find_opportunity_file(analysis.market_ticker)
            data_dir = get_data_dir()
            relative_path = (
                analysis_path.relative_to(data_dir)
                if analysis_path and analysis_path.exists()
                else None
            )
            logger.info("TEST COMPLETE - Data saved to:")
            if relative_path:
                logger.info(f"  - {relative_path}")
            else:
                logger.info("  - (analysis file path not found)")
        logger.info("=" * 70)

    except FileNotFoundError as e:
        logger.error(f"Opportunity file not found: {e}")
        logger.error("Run Scout test first or enable mock event generation.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the full Analyst pipeline (Researcher + Recommender)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with a modeled event and save output
    python -m coliseum.agents.analyst.test.run_test

    # Use an existing opportunity (dry-run, no file writes)
    python -m coliseum.agents.analyst.test.run_test --opportunity-id opp_abc123 --dry-run --no-mock-event

    # Use a test data directory
    python -m coliseum.agents.analyst.test.run_test --opportunity-id opp_abc123 --no-mock-event --data-dir backend/test_data
        """,
    )
    parser.add_argument(
        "--opportunity-id",
        type=str,
        help="Opportunity ID to analyze (from Scout output)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save files to disk (testing mode)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (e.g., backend/test_data)",
    )
    parser.add_argument(
        "--no-mock-event",
        action="store_true",
        help="Disable modeled opportunity creation (requires --opportunity-id)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_researcher_test(
                opportunity_id=args.opportunity_id,
                dry_run=args.dry_run,
                use_mock_event=not args.no_mock_event,
                data_dir=args.data_dir,
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
