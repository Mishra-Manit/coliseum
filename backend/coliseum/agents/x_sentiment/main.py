"""X Sentiment Agent: Searches X posts via Grok for public sentiment on a topic.

Uses the xAI SDK directly (not PydanticAI) because PydanticAI does not yet support
xAI's native x_search tool. Full observability is provided via logfire spans that
capture inputs, outputs, token usage, and latency.
"""

import logging
import time

import logfire
from xai_sdk import AsyncClient
from xai_sdk.chat import system, user
from xai_sdk.tools import x_search

from coliseum.agents.x_sentiment.models import XSentimentOutput
from coliseum.agents.x_sentiment.prompts import X_SENTIMENT_PROMPT
from coliseum.config import get_settings
from coliseum.llm_providers import GrokModel

logger = logging.getLogger(__name__)

_xai_client: AsyncClient | None = None


def _get_xai_client() -> AsyncClient:
    """Return the shared async xAI client, creating it on first call."""
    global _xai_client
    if _xai_client is None:
        settings = get_settings()
        _xai_client = AsyncClient(api_key=settings.xai_api_key, timeout=120)
    return _xai_client


async def run_x_sentiment(topic: str) -> XSentimentOutput:
    """Search X for public sentiment on a topic and return structured analysis.

    Args:
        topic: Natural-language description of the prediction market topic
              and its expected outcome (e.g. "Bitcoin closing above $100k
              on April 10 2026 — market expects YES at 94%").

    Returns:
        Structured sentiment output with classification, analysis, and key posts.
    """
    start_time = time.time()
    model = GrokModel.GROK_4_20_NON_REASONING

    with logfire.span(
        "x_sentiment agent",
        topic=topic,
        model=model.value,
    ):
        client = _get_xai_client()
        chat = client.chat.create(
            model=model.value,
            tools=[x_search()],
            response_format=XSentimentOutput,
            messages=[
                system(X_SENTIMENT_PROMPT),
                user(topic),
            ],
        )

        response = await chat.sample()
        duration = time.time() - start_time

        usage = response.usage
        logfire.info(
            "X sentiment complete",
            duration_seconds=round(duration, 1),
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            total_tokens=usage.total_tokens,
        )

        output = XSentimentOutput.model_validate_json(response.content)

        logfire.info(
            "X sentiment result",
            sentiment=output.sentiment.value,
            key_posts_count=len(output.key_posts),
        )

        return output
