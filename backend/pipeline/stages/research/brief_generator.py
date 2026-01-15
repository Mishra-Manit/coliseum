"""
Brief Generator

Creates standardized intelligence briefs using two-step process:
1. Exa AI Answer API for raw research data
2. Claude synthesis for structured brief

Brief Structure:
- Market Question, Resolution Criteria, Close Time, Current Price
- Key Facts (bulleted list)
- Recent Developments
- Historical Context
- Consensus/Expert Views
"""

import asyncio
import logfire
from typing import Any
from pydantic import BaseModel, Field

from pipeline.utils import create_agent
from pipeline.stages.research.exa_client import ExaClient


class IntelligenceBriefOutput(BaseModel):
    """Structured intelligence brief from LLM synthesis.

    Attributes:
        market_question: The prediction market question
        resolution_criteria: How the market will be resolved
        key_facts: List of key factual points (minimum 3)
        recent_developments: List of recent news/events (minimum 2)
        historical_context: List of historical background points
        expert_views: List of expert opinions and analysis
        sources: List of source URLs or citations
    """
    market_question: str = Field(description="The prediction market question")
    resolution_criteria: str = Field(description="Resolution criteria")
    key_facts: list[str] = Field(
        min_length=3,
        description="Key factual points about the event"
    )
    recent_developments: list[str] = Field(
        min_length=2,
        description="Recent news and developments"
    )
    historical_context: list[str] = Field(
        description="Historical background and precedents"
    )
    expert_views: list[str] = Field(
        description="Expert opinions and analysis"
    )
    sources: list[str] = Field(
        description="Source URLs or citations"
    )


SYNTHESIS_SYSTEM_PROMPT = """You are a research analyst synthesizing intelligence briefs for prediction markets.

Create comprehensive, objective briefs in the structured format.
Focus on facts, data, and expert opinions - not predictions.
Organize information clearly and logically.
Ensure all required fields are populated with relevant information.
Include proper source citations."""


class BriefGenerator:
    """Generates intelligence briefs using two-step research and synthesis process."""

    def __init__(self, exa_api_key: str | None = None):
        """Initialize the brief generator with:
        - Exa AI client for research (Answer API)
        - Claude synthesis agent for structured brief (structured output)

        Args:
            exa_api_key: Optional Exa API key. If not provided, reads from EXA_API_KEY env var.
        """
        # Exa client for search/answer queries
        self.exa_client = ExaClient(api_key=exa_api_key)

        # Claude agent for synthesis (returns IntelligenceBriefOutput)
        self.synthesis_agent = create_agent(
            model="anthropic:claude-3-5-sonnet-20241022",
            output_type=IntelligenceBriefOutput,
            system_prompt=SYNTHESIS_SYSTEM_PROMPT,
            temperature=0.1,
            retries=2,
            timeout=30.0
        )

    async def generate_brief(self, event: dict[str, Any]) -> IntelligenceBriefOutput:
        """Generate intelligence brief for one event.

        Args:
            event: Event dictionary with keys:
                - ticker: Kalshi market ticker
                - question: Market question
                - resolution_criteria: How market resolves
                - close_time: When market closes
                - yes_price: Current YES price

        Returns:
            IntelligenceBriefOutput with structured research

        Raises:
            AgentExecutionError: If research or synthesis fails
        """
        with logfire.span("research.generate_brief", event_id=event.get('ticker')):
            logfire.info(
                "Generating intelligence brief",
                ticker=event.get('ticker'),
                question=event.get('question')
            )

            # Step 1: Multi-query research (3-5 Exa AI calls)
            research_results = await self._conduct_research(event)

            # Step 2: Synthesize into structured brief
            brief = await self._synthesize_brief(event, research_results)

            logfire.info(
                "Brief generated",
                ticker=event.get('ticker'),
                fact_count=len(brief.key_facts),
                source_count=len(brief.sources)
            )

            return brief

    async def _conduct_research(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Conduct multi-query research using Exa AI Answer API.

        Executes all queries in parallel for improved performance.

        Args:
            event: Event dictionary

        Returns:
            List of research result dictionaries with 'answer' and 'citations'
        """
        queries = self._generate_search_queries(event)
        research_results = []

        with logfire.span("research.exa_search", query_count=len(queries)):
            logfire.info(f"Starting {len(queries)} parallel search queries")

            # Create tasks for all queries to run in parallel
            tasks = [
                self.exa_client.answer(query)
                for query in queries
            ]

            # Execute all queries in parallel, capturing exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle failures
            for i, (query, result) in enumerate(zip(queries, results), 1):
                if isinstance(result, Exception):
                    logfire.warn(
                        f"Search query {i}/{len(queries)} failed",
                        query=query,
                        error=str(result),
                        error_type=type(result).__name__
                    )
                    # Continue with other queries even if one fails
                    continue

                research_results.append({
                    "answer": result.answer,
                    "citations": result.citations,
                    "query": query
                })

                logfire.info(
                    f"Search completed {i}/{len(queries)}",
                    answer_length=len(result.answer),
                    citation_count=len(result.citations)
                )

        logfire.info(
            "Parallel search complete",
            successful_queries=len(research_results),
            total_queries=len(queries)
        )

        return research_results

    async def _synthesize_brief(
        self,
        event: dict[str, Any],
        research_results: list[dict[str, Any]]
    ) -> IntelligenceBriefOutput:
        """Synthesize research into structured brief.

        Args:
            event: Event dictionary
            research_results: List of research result dicts from Exa AI

        Returns:
            Structured IntelligenceBriefOutput
        """
        with logfire.span("research.synthesis"):
            # Combine all research results
            combined_research_parts = []
            all_sources = []

            for result in research_results:
                combined_research_parts.append(f"Query: {result['query']}")
                combined_research_parts.append(f"Answer: {result['answer']}")

                # Collect sources
                for citation in result.get('citations', []):
                    source_url = citation.get('url', '')
                    source_title = citation.get('title', 'Unknown Source')
                    if source_url:
                        all_sources.append(f"- {source_title}: {source_url}")

                combined_research_parts.append("---")

            combined_research = "\n\n".join(combined_research_parts)
            sources_text = "\n".join(all_sources) if all_sources else "No sources available"

            # Build synthesis prompt
            synthesis_prompt = f"""
Event Question: {event.get('question')}
Resolution Criteria: {event.get('resolution_criteria', 'TBD')}
Close Time: {event.get('close_time')}
Current YES Price: ${event.get('yes_price', 'N/A')}

Research Data:
{combined_research}

Sources Collected:
{sources_text}

Create a structured intelligence brief based on the research above.
Organize the information into key facts, recent developments, historical context, and expert views.
Include source citations from the research.
"""

            result = await self.synthesis_agent.run(synthesis_prompt)
            brief = result.data

            logfire.info(
                "Synthesis completed",
                brief_sections={
                    "key_facts": len(brief.key_facts),
                    "recent_developments": len(brief.recent_developments),
                    "historical_context": len(brief.historical_context),
                    "expert_views": len(brief.expert_views),
                    "sources": len(brief.sources)
                }
            )

            return brief

    def _generate_search_queries(self, event: dict[str, Any]) -> list[str]:
        """Generate 3-5 focused search queries for the event.

        Args:
            event: Event dictionary

        Returns:
            List of search query strings
        """
        question = event.get('question', '')
        category = event.get('category', '')

        # Base queries
        queries = [
            f"{question} recent news 2026",
            f"{question} expert analysis predictions",
            f"{question} historical data trends",
        ]

        # Add category-specific queries
        if 'politics' in category.lower():
            queries.append(f"{question} polls latest data")
        elif 'finance' in category.lower() or 'economics' in category.lower():
            queries.append(f"{question} market analysis forecast")
        elif 'sports' in category.lower():
            queries.append(f"{question} statistics performance")

        # Add one more general query
        queries.append(f"{question} current situation update")

        return queries[:5]  # Limit to 5 queries max

    def format_brief_as_markdown(self, brief: IntelligenceBriefOutput) -> str:
        """Format the brief as markdown for storage.

        Args:
            brief: IntelligenceBriefOutput instance

        Returns:
            Markdown-formatted string
        """
        md_parts = [
            f"# {brief.market_question}",
            "",
            "## Resolution Criteria",
            brief.resolution_criteria,
            "",
            "## Key Facts",
            *[f"- {fact}" for fact in brief.key_facts],
            "",
            "## Recent Developments",
            *[f"- {dev}" for dev in brief.recent_developments],
            "",
            "## Historical Context",
            *[f"- {ctx}" for ctx in brief.historical_context],
            "",
            "## Expert Views",
            *[f"- {view}" for view in brief.expert_views],
            "",
            "## Sources",
            *[f"- {source}" for source in brief.sources],
        ]

        return "\n".join(md_parts)
