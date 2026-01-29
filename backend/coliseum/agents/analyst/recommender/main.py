"""Recommender Agent: Trade decision making based on research."""

import logging
import os
import time
from datetime import datetime, timezone
from pydantic_ai import Agent, RunContext

from coliseum.agents.analyst.recommender.models import (
    RecommenderDependencies,
    RecommenderOutput,
)
from coliseum.agents.analyst.recommender.prompts import RECOMMENDER_SYSTEM_PROMPT
from coliseum.agents.calculations import (
    calculate_edge,
    calculate_expected_value,
    calculate_position_size_pct,
)
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    get_opportunity_markdown_body,
    find_opportunity_file_by_id,
    load_opportunity_from_file,
    update_opportunity_status,
)

logger = logging.getLogger(__name__)

_agent: Agent[RecommenderDependencies, RecommenderOutput] | None = None


def get_agent() -> Agent[RecommenderDependencies, RecommenderOutput]:
    global _agent
    if _agent is None:
        settings = get_settings()
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        _agent = _create_agent()
    return _agent


def _create_agent() -> Agent[RecommenderDependencies, RecommenderOutput]:
    agent = Agent(
        model=get_model_string(OpenAIModel.GPT_5),
        output_type=RecommenderOutput,
        deps_type=RecommenderDependencies,
        system_prompt=RECOMMENDER_SYSTEM_PROMPT,
    )
    _register_tools(agent)
    return agent


def _register_tools(agent: Agent[RecommenderDependencies, RecommenderOutput]) -> None:
    @agent.tool
    def read_opportunity_research(
        ctx: RunContext[RecommenderDependencies],
    ) -> dict:
        """Load opportunity details and full research markdown."""
        opportunity_id = ctx.deps.opportunity_id
        opp_file = find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")
        opportunity = load_opportunity_from_file(opp_file)
        markdown_body = get_opportunity_markdown_body(opp_file)

        return {
            "id": opportunity.id,
            "event_ticker": opportunity.event_ticker,
            "market_ticker": opportunity.market_ticker,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "research_markdown": markdown_body,
        }

    @agent.tool
    def calculate_edge_ev(
        ctx: RunContext[RecommenderDependencies],
        estimated_true_probability: float,
        current_market_price: float,
    ) -> dict:
        """Calculate edge and expected value from probability estimates."""
        try:
            edge = calculate_edge(estimated_true_probability, current_market_price)
            ev = calculate_expected_value(
                estimated_true_probability, current_market_price
            )

            return {
                "edge": round(edge, 4),
                "expected_value": round(ev, 4),
            }
        except ValueError as e:
            logger.error(f"Calculation error: {e}")
            raise

    @agent.tool
    def calculate_position_size(
        ctx: RunContext[RecommenderDependencies],
        estimated_true_probability: float,
        current_market_price: float,
    ) -> dict:
        """Calculate suggested position size using Kelly Criterion (capped at 10%)."""
        try:
            position_pct = calculate_position_size_pct(
                estimated_true_probability, current_market_price
            )

            return {
                "suggested_position_pct": round(position_pct, 4),
            }
        except ValueError as e:
            logger.error(f"Position size calculation error: {e}")
            raise

    @agent.tool
    def get_current_time(ctx: RunContext[RecommenderDependencies]) -> str:
        """Get current UTC time in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


async def run_recommender(
    opportunity_id: str,
    settings: Settings,
    dry_run: bool = False,
) -> tuple[RecommenderOutput, OpportunitySignal]:
    """Run Recommender agent - appends recommendation to opportunity file.

    Args:
        opportunity_id: Opportunity ID to evaluate
        settings: System settings
        dry_run: If True, skip file writes

    Returns:
        tuple of (RecommenderOutput, updated OpportunitySignal)
    """
    start_time = time.time()
    logger.info(f"Starting Recommender for opportunity: {opportunity_id}")

    # Find opportunity file
    opp_file = find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")
    opportunity = load_opportunity_from_file(opp_file)

    # Verify research exists
    if not opportunity.research_completed_at:
        raise ValueError(f"Research not completed for {opportunity_id}")

    # Get full markdown body for context
    markdown_body = get_opportunity_markdown_body(opp_file)

    # Run recommendation
    deps = RecommenderDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    prompt = _build_decision_prompt(opportunity, markdown_body)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output

    # Calculate NO-side metrics (derived from p_no = 1 - p_yes)
    p_no = 1 - output.estimated_true_probability
    no_price = opportunity.no_price
    
    edge_no = calculate_edge(p_no, no_price)
    
    # Handle edge cases where p_no is exactly 0 or 1 (expected_value will raise ValueError)
    try:
        ev_no = calculate_expected_value(p_no, no_price)
    except ValueError:
        # If p_no is 0 or 1, EV is undefined, set to 0
        ev_no = 0.0
    
    # calculate_position_size_pct handles edge cases gracefully (returns 0.0)
    size_no = calculate_position_size_pct(p_no, no_price)
    
    # Update output with NO-side values
    output = output.model_copy(update={
        "edge_no": edge_no,
        "expected_value_no": ev_no,
        "suggested_position_pct_no": size_no,
    })

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    # Prepare recommendation section for append
    action_label = output.action if hasattr(output, 'action') and output.action else "PENDING"
    recommendation_section = f"""---

## Trade Evaluation

| Side | Edge | EV | Suggested Size |
|------|------|-----|----------------|
| **YES** | {output.edge:+.0%} | {output.expected_value:+.0%} | {output.suggested_position_pct:.1%} |
| **NO** | {output.edge_no:+.0%} | {output.expected_value_no:+.0%} | {output.suggested_position_pct_no:.1%} |

**Status**: Pending

### Reasoning

{output.reasoning}"""

    # Prepare frontmatter updates
    frontmatter_updates = {
        # YES-side metrics
        "estimated_true_probability": output.estimated_true_probability,
        "current_market_price": output.current_market_price,
        "expected_value": output.expected_value,
        "edge": output.edge,
        "suggested_position_pct": output.suggested_position_pct,
        # NO-side metrics
        "edge_no": output.edge_no,
        "expected_value_no": output.expected_value_no,
        "suggested_position_pct_no": output.suggested_position_pct_no,
        # Status fields
        "recommendation_completed_at": completed_at.isoformat(),
        "action": None,  # No action field in output
        "status": "recommended",
    }

    # Append to opportunity file
    if not dry_run:
        append_to_opportunity(
            market_ticker=opportunity.market_ticker,
            frontmatter_updates=frontmatter_updates,
            body_section=recommendation_section,
            section_header="## Trade Evaluation",
        )

        # Update opportunity status
        update_opportunity_status(opportunity.market_ticker, "recommended")

    logger.info(
        f"Recommender completed in {duration:.1f}s - "
        f"Edge: {output.edge:+.0%}, EV: {output.expected_value:+.0%}"
    )

    # Return updated opportunity
    updated_opp = load_opportunity_from_file(opp_file)
    return output, updated_opp


def _build_decision_prompt(opportunity: OpportunitySignal, markdown_body: str) -> str:
    """Build the evaluation prompt for the agent."""
    prompt = f"""Evaluate this research and compute trade metrics (no final trade decision).

## Opportunity Details

**Market**: {opportunity.event_ticker}
**YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)

## Full Research Context

{markdown_body}

## Your Task

1. Review the research above carefully
2. Evaluate the quality and reliability of the research (sources, credibility, recency)
3. Based on the evidence, estimate the true probability of YES outcome
4. Use `calculate_edge_ev` to compute edge and expected value
5. Use `calculate_position_size` to determine position sizing
6. Do not make a final BUY/NO decision (leave action unset)

## Evaluation Thresholds

- **Minimum edge**: 5% (flag low edge if below)
- **Minimum confidence**: 60% (flag low confidence if below)
- **Position size**: Kelly Criterion, capped at 10%

## Important

Be disciplined and conservative. When in doubt, avoid overconfidence and call out uncertainty.

Consider:
- Is the research high quality?
- Are sources credible and diverse?
- Is there sufficient edge after accounting for risks?
- If confidence or edge is low, say so explicitly
"""

    return prompt
