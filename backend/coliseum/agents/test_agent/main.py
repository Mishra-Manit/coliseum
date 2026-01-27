"""Test Agent: Scans opportunities and sends Telegram alerts."""

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic_ai import Agent, RunContext

from coliseum.agents.test_agent.models import (
    InterestSelection,
    TestAgentDependencies,
    TestAgentOutput,
)
from coliseum.agents.test_agent.prompts import TEST_AGENT_SYSTEM_PROMPT
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.services.telegram import TelegramClient, create_telegram_client
from coliseum.storage.files import find_opportunity_file_by_id, load_opportunity_from_file
from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)

_agent: Agent[TestAgentDependencies, TestAgentOutput] | None = None


def get_agent() -> Agent[TestAgentDependencies, TestAgentOutput]:
    """Get the singleton Test agent instance."""
    global _agent
    if _agent is None:
        # Ensure OpenAI API key is set
        settings = get_settings()
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        _agent = _create_agent()
        _register_tools(_agent)
    return _agent


def _create_agent() -> Agent[TestAgentDependencies, TestAgentOutput]:
    """Create the Test agent with OpenAI GPT-5."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5),
        output_type=TestAgentOutput,
        deps_type=TestAgentDependencies,
        system_prompt=TEST_AGENT_SYSTEM_PROMPT,
    )


def _register_tools(agent: Agent[TestAgentDependencies, TestAgentOutput]) -> None:
    """Register tools with the Test agent."""

    @agent.tool
    async def list_opportunities(
        ctx: RunContext[TestAgentDependencies],
        lookback_days: int = 7,
    ) -> dict:
        """Scan opportunities directory for the last N days and return summary data.

        Returns a dict with 'opportunities' list containing basic info for each opportunity:
        - id, market_ticker, title, subtitle
        - yes_price, no_price, close_time
        - edge, expected_value, suggested_position_pct
        - status, discovered_at
        """
        try:
            # Use custom data_dir if provided, otherwise use default
            if ctx.deps.data_dir:
                data_dir = Path(ctx.deps.data_dir)
            else:
                data_dir = get_data_dir()
            opps_dir = data_dir / "opportunities"

            if not opps_dir.exists():
                return {
                    "success": False,
                    "error": "Opportunities directory not found",
                    "opportunities": [],
                }

            # Get date directories within lookback window
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            date_dirs = sorted(
                [d for d in opps_dir.iterdir() if d.is_dir()],
                key=lambda d: d.name,
                reverse=True,
            )

            opportunities = []
            for date_dir in date_dirs:
                # Check if directory is within lookback window
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    if dir_date < cutoff_date:
                        continue
                except ValueError:
                    # Skip non-date directories
                    continue

                # Load all .md files in this date directory
                for md_file in date_dir.glob("*.md"):
                    try:
                        opp = load_opportunity_from_file(md_file)

                        timestamp = (
                            opp.discovered_at.isoformat()
                            if opp.discovered_at
                            else None
                        )

                        opportunities.append(
                            {
                                "id": opp.id,
                                "market_ticker": opp.market_ticker,
                                "title": opp.title,
                                "subtitle": opp.subtitle or "",
                                "yes_price": opp.yes_price,
                                "no_price": opp.no_price,
                                "close_time": (
                                    opp.close_time.isoformat() if opp.close_time else None
                                ),
                                "edge": opp.edge,
                                "expected_value": opp.expected_value,
                                "suggested_position_pct": opp.suggested_position_pct,
                                "edge_no": opp.edge_no,
                                "expected_value_no": opp.expected_value_no,
                                "suggested_position_pct_no": opp.suggested_position_pct_no,
                                "status": opp.status,
                                "discovered_at": timestamp,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Error loading {md_file}: {e}")
                        continue

            return {
                "success": True,
                "opportunities": opportunities,
                "count": len(opportunities),
            }

        except Exception as e:
            logger.error(f"Error listing opportunities: {e}")
            return {
                "success": False,
                "error": str(e),
                "opportunities": [],
            }

    @agent.tool
    async def read_opportunity_detail(
        ctx: RunContext[TestAgentDependencies],
        opportunity_id: str,
    ) -> dict:
        """Load full details for a specific opportunity by ID.

        Returns complete opportunity data including:
        - All fields from list_opportunities
        - Full research synthesis (if available)
        - Research sources (if available)
        - Estimated true probability
        - Detailed rationale
        """
        try:
            opp_file = find_opportunity_file_by_id(opportunity_id)
            if not opp_file:
                return {
                    "success": False,
                    "error": f"Opportunity file not found: {opportunity_id}",
                }

            opp = load_opportunity_from_file(opp_file)

            # Get full research markdown from file if available
            research_markdown = ""
            try:
                from coliseum.storage.files import get_opportunity_markdown_body

                research_markdown = get_opportunity_markdown_body(opp_file)
            except Exception:
                pass

            timestamp = opp.discovered_at.isoformat() if opp.discovered_at else None

            return {
                "success": True,
                "id": opp.id,
                "market_ticker": opp.market_ticker,
                "event_ticker": opp.event_ticker,
                "title": opp.title,
                "subtitle": opp.subtitle or "",
                "yes_price": opp.yes_price,
                "no_price": opp.no_price,
                "close_time": opp.close_time.isoformat() if opp.close_time else None,
                "edge": opp.edge,
                "expected_value": opp.expected_value,
                "suggested_position_pct": opp.suggested_position_pct,
                "edge_no": opp.edge_no,
                "expected_value_no": opp.expected_value_no,
                "suggested_position_pct_no": opp.suggested_position_pct_no,
                "estimated_true_probability": opp.estimated_true_probability,
                "current_market_price": opp.current_market_price,
                "status": opp.status,
                "discovered_at": timestamp,
                "rationale": opp.rationale,
                "research_markdown": research_markdown,
            }

        except Exception as e:
            logger.error(f"Error reading opportunity {opportunity_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @agent.tool
    async def send_telegram_alert(
        ctx: RunContext[TestAgentDependencies],
        message: str,
    ) -> dict:
        """Send a Telegram alert with the opportunity summary.

        Args:
            message: The alert message to send (should be the 1-sentence summary)

        Returns:
            Dict with success status and message_id if successful
        """
        try:
            # Check if in dry-run mode
            if ctx.deps.dry_run:
                logger.info(f"[DRY RUN] Would send Telegram: {message}")
                return {
                    "success": True,
                    "message_id": None,
                    "recipient": "dry_run",
                    "dry_run": True,
                }

            result = await ctx.deps.telegram_client.send_alert(message)

            if result.success:
                return {
                    "success": True,
                    "message_id": result.message_id,
                    "recipient": result.recipient,
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Unknown error",
                }

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return {
                "success": False,
                "error": str(e),
            }


async def run_test_agent(
    settings: Settings | None = None,
    dry_run: bool = False,
    data_dir: str | None = None,
) -> TestAgentOutput:
    """Run the Test Agent to select and alert on most interesting opportunity.

    Args:
        settings: Optional Settings instance (defaults to get_settings())
        dry_run: If True, skip sending Telegram alert (for testing)
        data_dir: Optional custom data directory (for testing with test_data)

    Returns:
        TestAgentOutput with selection, telegram status, and metadata
    """
    if settings is None:
        settings = get_settings()

    logger.info("Starting Test Agent")

    # Create Telegram client
    async with create_telegram_client(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    ) as telegram_client:
        deps = TestAgentDependencies(
            telegram_client=telegram_client,
            config=settings,
            data_dir=data_dir,
            dry_run=dry_run,
        )

        # Build prompt
        prompt = """Your task is to find and alert on the most interesting trading opportunity.

Use the tools to:
1. List all opportunities from the last 7 days
2. Evaluate them based on edge, EV, timing, and novelty
3. Read full details for the top candidates
4. Select the ONE most interesting opportunity
5. Send a compelling 1-sentence Telegram alert

Remember: Your interest_reason must be exactly 1 sentence and under 200 characters.
"""

        # Run agent
        agent = get_agent()
        result = await agent.run(prompt, deps=deps)
        output: TestAgentOutput = result.output

        logger.info(
            f"Test Agent selected: {output.selection.selected_opportunity_id} "
            f"({output.opportunities_evaluated} opportunities evaluated)"
        )
        logger.info(f"Reason: {output.selection.interest_reason}")
        logger.info(f"Confidence: {output.selection.confidence:.1%}")

        if dry_run:
            logger.info("[DRY RUN] Mode - Telegram was not actually sent")

        logger.info(f"Telegram sent: {output.telegram_sent}")
        if output.telegram_message_id:
            logger.info(f"Telegram message ID: {output.telegram_message_id}")

        return output
