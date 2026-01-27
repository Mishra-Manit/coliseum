"""Standalone runner for Test Agent."""

import asyncio
import logging
import sys
from argparse import ArgumentParser

from coliseum.agents.test_agent import run_test_agent
from coliseum.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> int:
    """Run the Test Agent and return exit code."""
    parser = ArgumentParser(description="Run the Test Agent")
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Custom data directory (e.g., 'test_data' for testing)",
    )
    args = parser.parse_args()

    # Validate environment
    settings = get_settings()

    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY not set in environment")
        return 1

    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        return 1
    if not settings.telegram_chat_id:
        logger.error("TELEGRAM_CHAT_ID not set in environment")
        return 1

    try:
        # Run agent
        result = await run_test_agent(
            settings=settings,
            data_dir=args.data_dir,
        )

        # Print results
        print("\n" + "=" * 60)
        print("TEST AGENT RESULTS")
        print("=" * 60)
        print(f"\nSelected Opportunity: {result.selection.selected_opportunity_id}")
        print(f"Confidence: {result.selection.confidence:.1%}")
        print(f"\nReason:")
        print(f"  {result.selection.interest_reason}")
        print(f"\nOpportunities Evaluated: {result.opportunities_evaluated}")
        print(f"\nTelegram Status:")
        print(f"  Sent: {result.telegram_sent}")
        if result.telegram_message_id:
            print(f"  Message ID: {result.telegram_message_id}")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Test Agent failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
