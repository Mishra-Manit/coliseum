"""News & Events Summary Agent service."""

import logging
import time
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Event, EventSummary
from utils.llm_agent import create_agent, run_agent

logger = logging.getLogger(__name__)


class SummaryService:
    """
    Generates comprehensive event summaries using AI with Perplexity search.
    Creates standardized context for all AI models to use.
    """

    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self):
        self.perplexity_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close the HTTP client."""
        await self.perplexity_client.aclose()

    async def generate_event_summary(
        self,
        db: AsyncSession,
        event_id: UUID,
    ) -> EventSummary:
        """
        Generate a comprehensive summary for an event.

        Process:
        1. Retrieve event details
        2. Execute web searches via Perplexity
        3. Compile key factors and data points
        4. Generate structured summary
        """
        start_time = time.time()

        # Get event
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Check if summary already exists
        existing = await db.execute(
            select(EventSummary).where(EventSummary.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Summary already exists for event {event_id}")

        # Generate search queries based on event
        search_queries = self._generate_search_queries(event)

        # Execute Perplexity search
        search_results = await self._execute_perplexity_search(
            event, search_queries
        )

        # Compile into structured summary
        summary_data = await self._compile_summary(event, search_results)

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Create summary record
        summary = EventSummary(
            event_id=event_id,
            summary_text=summary_data["summary_text"],
            key_factors=summary_data["key_factors"],
            recent_news=summary_data["recent_news"],
            relevant_data=summary_data["relevant_data"],
            sources_used=summary_data.get("sources", []),
            search_queries=search_queries,
            agent_model="perplexity-sonar",
            generation_time_ms=generation_time_ms,
        )
        db.add(summary)
        await db.commit()
        await db.refresh(summary)

        logger.info(
            f"Generated summary for event {event.title} in {generation_time_ms}ms"
        )
        return summary

    def _generate_search_queries(self, event: Event) -> list[str]:
        """Generate relevant search queries for the event."""
        queries = [
            f"{event.title} latest news",
            f"{event.title} prediction analysis",
            f"{event.title} expert opinions",
        ]

        # Add category-specific queries
        if "election" in event.category.lower():
            queries.append(f"{event.title} polling data")
        elif "sports" in event.category.lower():
            queries.append(f"{event.title} betting odds")
        elif "finance" in event.category.lower() or "crypto" in event.category.lower():
            queries.append(f"{event.title} market analysis")

        return queries[:5]  # Limit to 5 queries

    async def _execute_perplexity_search(
        self,
        event: Event,
        queries: list[str],
    ) -> dict[str, Any]:
        """Execute Perplexity search to gather context."""
        try:
            # Combine queries into a comprehensive prompt
            combined_query = f"""
            Research the following prediction market question and provide comprehensive analysis:

            Question: {event.question}
            Title: {event.title}
            Category: {event.category}
            Context: {event.market_context or 'No additional context'}

            Please provide:
            1. Latest news and developments related to this question
            2. Key factors that could influence the outcome
            3. Expert opinions or analysis if available
            4. Relevant statistics or data points
            5. Historical context if applicable

            Focus on factual, recent information that would help predict the outcome.
            """

            response = await self.perplexity_client.post(
                self.PERPLEXITY_API_URL,
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": combined_query,
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            sources = data.get("citations", [])

            return {
                "content": content,
                "sources": sources,
            }

        except httpx.HTTPError as e:
            logger.error(f"Perplexity search failed: {e}")
            return {
                "content": f"Unable to fetch latest information. Event context: {event.market_context or 'No context available'}",
                "sources": [],
            }

    async def _compile_summary(
        self,
        event: Event,
        search_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Compile search results into structured summary using OpenRouter."""
        compilation_prompt = f"""
        You are a prediction market analyst. Based on the following research,
        create a structured analysis for AI models to use when betting.

        Event: {event.title}
        Question: {event.question}
        Category: {event.category}
        Current Market Price: {float(event.current_price) * 100:.1f}% YES

        Research Results:
        {search_results.get('content', 'No research available')}

        Create a JSON response with this exact structure:
        {{
            "summary_text": "A 2-3 paragraph comprehensive summary of the situation",
            "key_factors": [
                {{"factor": "Description of key factor 1", "impact": "positive/negative/neutral"}},
                {{"factor": "Description of key factor 2", "impact": "positive/negative/neutral"}}
            ],
            "recent_news": [
                {{"headline": "News headline", "summary": "Brief summary", "date": "approximate date"}},
            ],
            "relevant_data": {{
                "market_sentiment": "bullish/bearish/neutral",
                "confidence_level": "high/medium/low",
                "key_statistics": ["stat 1", "stat 2"]
            }}
        }}

        Respond ONLY with valid JSON, no other text.
        """

        try:
            result = await run_agent(
                prompt=compilation_prompt,
                model="anthropic/claude-3.5-sonnet",
                max_tokens=2000,
            )

            # Parse JSON response
            import json
            summary_data = json.loads(result)
            summary_data["sources"] = search_results.get("sources", [])
            return summary_data

        except Exception as e:
            logger.error(f"Summary compilation failed: {e}")
            # Return fallback structure
            return {
                "summary_text": search_results.get("content", "No summary available"),
                "key_factors": [],
                "recent_news": [],
                "relevant_data": {},
                "sources": search_results.get("sources", []),
            }

    async def get_summary(
        self, db: AsyncSession, event_id: UUID
    ) -> Optional[EventSummary]:
        """Get existing summary for an event."""
        result = await db.execute(
            select(EventSummary).where(EventSummary.event_id == event_id)
        )
        return result.scalar_one_or_none()


# Singleton instance
summary_service = SummaryService()
