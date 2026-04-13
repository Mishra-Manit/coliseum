"""Analyst Agent: Orchestration layer for Researcher + Recommender pipeline.

This module orchestrates the three-stage pipeline:
- Researcher + X Sentiment: Run in parallel for speed
- Recommender: Makes trade decisions based on combined research
"""

import asyncio
import logging

import logfire

from coliseum.agents.analyst.recommender import run_recommender
from coliseum.agents.analyst.researcher import run_researcher
from coliseum.agents.analyst.shared import load_opportunity
from coliseum.agents.x_sentiment.main import run_x_sentiment
from coliseum.agents.x_sentiment.models import XSentimentOutput
from coliseum.config import Settings
from coliseum.domain.opportunity import OpportunitySignal
from coliseum.services.supabase.repositories.opportunities import append_x_sentiment_to_research

logger = logging.getLogger(__name__)


def _build_x_sentiment_topic(opportunity: OpportunitySignal) -> str:
    """Build a natural-language topic string from the opportunity for X search."""
    price_pct = round(opportunity.yes_price * 100)
    parts = [opportunity.market_title]
    if opportunity.subtitle:
        parts.append(f"- {opportunity.subtitle}")
    parts.append(f"\u2014 market expects YES at {price_pct}%")
    return " ".join(parts)


async def _run_x_sentiment_safe(
    opportunity: OpportunitySignal,
) -> XSentimentOutput | None:
    """Run X sentiment with error handling so it never blocks the pipeline."""
    try:
        topic = _build_x_sentiment_topic(opportunity)
        return await run_x_sentiment(topic)
    except Exception as e:
        logfire.warning(
            "X sentiment failed, continuing without it",
            opportunity_id=opportunity.id,
            error=str(e),
        )
        logger.warning("X sentiment failed for %s: %s", opportunity.id, e)
        return None


async def run_analyst(
    opportunity_id: str,
    settings: Settings,
) -> OpportunitySignal:
    """Run full Analyst pipeline: (Researcher + X Sentiment) in parallel, then Recommender."""
    logger.info("Analyst starting: %s", opportunity_id)
    with logfire.span("analyst pipeline", opportunity_id=opportunity_id):
        opportunity = await load_opportunity(opportunity_id)

        with logfire.span("research phase", opportunity_id=opportunity_id):
            logger.info("Research phase starting (web + X sentiment in parallel)")

            researcher_task = asyncio.create_task(
                run_researcher(opportunity_id=opportunity_id, settings=settings)
            )
            x_sentiment_task = asyncio.create_task(_run_x_sentiment_safe(opportunity))

            try:
                _, x_sentiment_output = await asyncio.gather(
                    researcher_task, x_sentiment_task
                )
            except Exception:
                x_sentiment_task.cancel()
                await asyncio.gather(x_sentiment_task, return_exceptions=True)
                raise

            if x_sentiment_output is not None:
                try:
                    await append_x_sentiment_to_research(
                        opportunity_id=opportunity_id,
                        x_sentiment_markdown=x_sentiment_output.to_markdown(),
                    )
                except Exception as e:
                    logfire.error(
                        "Failed to persist X sentiment",
                        opportunity_id=opportunity_id,
                        error=str(e),
                    )

            logfire.info("Research phase complete")
            logger.info("Research phase complete")

        with logfire.span("recommender", opportunity_id=opportunity_id):
            logger.info("Recommender starting")
            _, opportunity = await run_recommender(
                opportunity_id=opportunity_id,
                settings=settings,
            )
            logfire.info("Recommendation complete")
            logger.info("Recommender complete: status=%s", opportunity.status)

    logger.info("Analyst complete: %s status=%s", opportunity_id, opportunity.status)
    return opportunity
