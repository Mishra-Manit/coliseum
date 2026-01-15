"""
Exa AI API Client

Wrapper for Exa AI Answer endpoint for research.

Methods:
- answer(query): Execute research query via Exa Answer API
- get_research(queries): Batch research queries for an event

Standard scope: 3-5 calls per event, ~15 minutes, ~2000 tokens output
"""

import os
import asyncio
from typing import Optional, Any
from dataclasses import dataclass

import logfire
from exa_py import Exa


@dataclass
class ExaAnswerResult:
    """Result from Exa Answer API call."""
    answer: str
    citations: list[dict[str, Any]]
    raw_result: Any


class ExaClient:
    """Client for Exa AI Answer API using exa_py SDK."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Exa client.

        Args:
            api_key: Exa API key. If not provided, reads from EXA_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        key = api_key or os.getenv("EXA_API_KEY")
        if not key:
            raise ValueError(
                "Exa API key is required. Provide via api_key parameter or "
                "EXA_API_KEY environment variable."
            )
        self.exa = Exa(api_key=key)

    async def answer(self, query: str, text: bool = True, timeout: float = 30.0) -> ExaAnswerResult:
        """Get an AI-synthesized answer to a research query.

        Args:
            query: The research question to answer
            text: Whether to include full text in citations
            timeout: Maximum time in seconds to wait for response (default: 30.0)

        Returns:
            ExaAnswerResult with answer text and source citations

        Raises:
            ConnectionError: If network connection fails
            asyncio.TimeoutError: If request times out
            Exception: For other API errors
        """
        with logfire.span("exa.answer", query=query[:100]):
            try:
                # Run synchronous exa.answer() in thread pool with timeout
                result: Any = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.exa.answer,
                        query=query,
                        text=text,
                    ),
                    timeout=timeout
                )

                # Parse citations into a clean format
                citations = []
                for citation in result.citations:
                    citations.append({
                        "title": getattr(citation, "title", ""),
                        "url": getattr(citation, "url", ""),
                        "text": getattr(citation, "text", ""),
                        "published_date": getattr(citation, "publishedDate", None),
                        "author": getattr(citation, "author", None),
                    })

                logfire.info(
                    "Exa answer completed",
                    query_preview=query[:50],
                    answer_length=len(result.answer),
                    citation_count=len(citations)
                )

                return ExaAnswerResult(
                    answer=result.answer,
                    citations=citations,
                    raw_result=result
                )

            except asyncio.TimeoutError as e:
                logfire.error("Exa timeout error", error=str(e), timeout=timeout)
                raise
            except ConnectionError as e:
                logfire.error("Exa connection error", error=str(e))
                raise
            except Exception as e:
                logfire.error(
                    "Exa API error",
                    error_type=type(e).__name__,
                    error=str(e),
                    query=query[:50]
                )
                raise

    def format_answer_with_sources(self, result: ExaAnswerResult) -> str:
        """Format an Exa answer result as a readable string with sources.

        Args:
            result: ExaAnswerResult from answer() call

        Returns:
            Formatted string with answer and numbered source citations
        """
        lines = [f"Answer: {result.answer}\n"]
        
        if result.citations:
            lines.append("\nSources:")
            for i, citation in enumerate(result.citations, 1):
                lines.append(f"  {i}. {citation.get('title', 'Untitled')}")
                lines.append(f"     URL: {citation.get('url', 'N/A')}")

        return "\n".join(lines)
