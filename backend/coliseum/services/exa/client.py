"""Async wrapper for Exa AI SDK with retry logic and error handling."""

import asyncio
import logging
from typing import Any

from exa_py import Exa

from .config import ExaConfig
from .exceptions import (
    ExaAPIError,
    ExaAuthError,
    ExaBadRequestError,
    ExaRateLimitError,
    ExaServerError,
)
from .models import ExaAnswerResponse, ExaCitation

logger = logging.getLogger(__name__)


class ExaClient:
    """Async wrapper for Exa AI SDK with retry logic and error handling."""

    def __init__(self, api_key: str, config: ExaConfig | None = None):
        self.api_key = api_key
        self.config = config or ExaConfig()
        self._client: Exa | None = None
        logger.info("Initialized ExaClient")

    async def __aenter__(self) -> "ExaClient":
        """Context manager entry - create Exa client."""
        self._client = Exa(api_key=self.api_key)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup."""
        self._client = None
        logger.info("Closed ExaClient")

    @property
    def client(self) -> Exa:
        """Get Exa client, raising if not in context."""
        if self._client is None:
            raise RuntimeError("ExaClient must be used as async context manager")
        return self._client

    async def _retry_wrapper(self, operation: str, fn: callable) -> Any:
        """Wrap SDK calls with retry logic for 429/5xx errors."""
        retry_count = 0
        last_error: Exception | None = None

        while retry_count < self.config.max_retries:
            try:
                result = fn()
                return result

            except Exception as e:
                error_msg = str(e).lower()

                if "401" in error_msg or "unauthorized" in error_msg:
                    raise ExaAuthError("Authentication failed", status_code=401)
                elif "429" in error_msg or "rate limit" in error_msg:
                    wait_time = 2**retry_count
                    logger.warning(f"Rate limited in {operation}, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                elif "400" in error_msg or "bad request" in error_msg:
                    raise ExaBadRequestError(f"Invalid request: {e}", status_code=400)
                elif any(code in error_msg for code in ["500", "502", "503", "504"]):
                    wait_time = 2**retry_count
                    logger.warning(f"Server error in {operation}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    last_error = e
                    break

        raise ExaAPIError(f"{operation} failed after {retry_count} retries: {last_error}")

    async def answer(
        self,
        question: str,
        include_text: bool | None = None,
        system_prompt: str | None = None,
    ) -> ExaAnswerResponse:
        """Generate an answer to a question with citations.

        Args:
            question: Question to answer
            include_text: Whether to include full text in citations
            system_prompt: Custom system prompt for the LLM
        """
        include_text = (
            include_text if include_text is not None else self.config.answer_include_text
        )
        system_prompt = system_prompt or self.config.default_system_prompt

        def _answer():
            return self.client.answer(
                query=question,
                text=include_text,
                model=self.config.answer_model,
                system_prompt=system_prompt,
            )

        response = await self._retry_wrapper("answer", _answer)

        citations = [
            ExaCitation(url=c.url, title=c.title, text=getattr(c, "text", None))
            for c in response.citations
        ]

        return ExaAnswerResponse(answer=response.answer, citations=citations, query=question)


def create_exa_client(api_key: str) -> ExaClient:
    """Factory function to create ExaClient with default config."""
    return ExaClient(api_key=api_key, config=ExaConfig())
