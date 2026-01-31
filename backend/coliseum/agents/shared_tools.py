"""Shared tools for PydanticAI agents."""

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic_ai import Agent, RunContext

from coliseum.storage.files import (
    find_opportunity_file_by_id,
    get_opportunity_markdown_body,
    load_opportunity_from_file,
)

logger = logging.getLogger(__name__)


def register_get_current_time[T](agent: Agent[T, Any]) -> None:
    """Register get_current_time tool on any agent."""

    @agent.tool
    def get_current_time(ctx: RunContext[T]) -> str:
        """Get the current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


def register_load_opportunity[T](
    agent: Agent[T, Any],
    deps_attr: str = "opportunity_id",
) -> None:
    """Register basic opportunity loading tool."""

    @agent.tool
    async def load_opportunity(ctx: RunContext[T]) -> dict:
        """Fetch opportunity details (market info, prices, close time, Scout's rationale)."""
        opportunity_id = getattr(ctx.deps, deps_attr)
        file_path = find_opportunity_file_by_id(opportunity_id)
        if not file_path:
            raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

        opportunity = load_opportunity_from_file(file_path)
        return {
            "id": opportunity.id,
            "event_ticker": opportunity.event_ticker,
            "market_ticker": opportunity.market_ticker,
            "title": opportunity.title,
            "subtitle": opportunity.subtitle,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "close_time": opportunity.close_time.isoformat(),
            "rationale": opportunity.rationale,
            "status": opportunity.status,
            "discovered_at": opportunity.discovered_at.isoformat(),
        }


def register_load_opportunity_with_research[T](
    agent: Agent[T, Any],
    deps_attr: str = "opportunity_id",
    include_metrics: bool = False,
) -> None:
    """Register opportunity + research loading tool with optional analyst metrics."""

    @agent.tool
    async def load_opportunity_research(ctx: RunContext[T]) -> dict:
        """Fetch opportunity with full research markdown and optional analyst metrics."""
        opportunity_id = getattr(ctx.deps, deps_attr)
        opp_file = find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

        opportunity = load_opportunity_from_file(opp_file)
        markdown_body = get_opportunity_markdown_body(opp_file)

        result = {
            "id": opportunity.id,
            "event_ticker": opportunity.event_ticker,
            "market_ticker": opportunity.market_ticker,
            "title": opportunity.title,
            "subtitle": opportunity.subtitle,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "close_time": opportunity.close_time.isoformat() if opportunity.close_time else None,
            "research_markdown": markdown_body,
        }

        if include_metrics:
            result.update({
                "estimated_true_probability": opportunity.estimated_true_probability,
                "current_market_price": opportunity.current_market_price,
                "edge": opportunity.edge,
                "expected_value": opportunity.expected_value,
                "suggested_position_pct": opportunity.suggested_position_pct,
                "edge_no": opportunity.edge_no,
                "expected_value_no": opportunity.expected_value_no,
                "suggested_position_pct_no": opportunity.suggested_position_pct_no,
            })

        return result
