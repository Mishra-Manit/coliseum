"""Recommender Agent: Trade decision making based on research."""

import logging
import time
from datetime import datetime, timezone
from typing import Literal

from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.shared_tools import register_get_current_time
from coliseum.agents.analyst.models import AnalystDependencies, RecommenderOutput
from coliseum.agents.analyst.prompts import (
    RECOMMENDER_SURE_THING_PROMPT,
    RECOMMENDER_SYSTEM_PROMPT,
)
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_and_validate_opportunity,
)
from coliseum.agents.analyst.calculations import (
    calculate_edge,
    calculate_expected_value,
    calculate_position_size_pct,
)
from coliseum.config import Settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    get_opportunity_markdown_body,
    load_opportunity_from_file,
)

logger = logging.getLogger(__name__)


def _create_agent(strategy: str = "edge") -> Agent[AnalystDependencies, RecommenderOutput]:
    prompt = RECOMMENDER_SURE_THING_PROMPT if strategy == "sure_thing" else RECOMMENDER_SYSTEM_PROMPT
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=RecommenderOutput,
        deps_type=AnalystDependencies,
        system_prompt=prompt,
    )


def _register_tools(agent: Agent[AnalystDependencies, RecommenderOutput]) -> None:
    @agent.tool
    def calculate_edge_ev(
        ctx: RunContext[AnalystDependencies],
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
        ctx: RunContext[AnalystDependencies],
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

    register_get_current_time(agent)


_edge_factory = AgentFactory(
    create_fn=lambda: _create_agent("edge"),
    register_tools_fn=_register_tools,
)

_sure_thing_factory = AgentFactory(
    create_fn=lambda: _create_agent("sure_thing"),
    register_tools_fn=_register_tools,
)


def get_agent(strategy: str = "edge") -> Agent[AnalystDependencies, RecommenderOutput]:
    """Get the singleton Recommender agent instance for the given strategy."""
    if strategy == "sure_thing":
        return _sure_thing_factory.get_agent()
    return _edge_factory.get_agent()


async def run_recommender(
    opportunity_id: str,
    settings: Settings,
    strategy: Literal["edge", "sure_thing"] | None = None,
) -> tuple[RecommenderOutput, OpportunitySignal]:
    """Run Recommender agent - appends recommendation to opportunity file."""
    start_time = time.time()
    logger.info(f"Starting Recommender for opportunity: {opportunity_id}")

    opp_file, opportunity, resolved_strategy = load_and_validate_opportunity(
        opportunity_id, strategy
    )
    logger.info(
        f"Recommender strategy resolved: {resolved_strategy} (file={opportunity.strategy})"
    )

    if not opportunity.research_completed_at:
        raise ValueError(f"Research not completed for {opportunity_id}")

    markdown_body = get_opportunity_markdown_body(opp_file)

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    if resolved_strategy == "sure_thing":
        logger.info("Recommender using sure_thing evaluation prompt")
        prompt = _build_sure_thing_decision_prompt(opportunity, markdown_body)
    else:
        logger.info("Recommender using edge evaluation prompt")
        prompt = _build_decision_prompt(opportunity, markdown_body)

    agent = get_agent(resolved_strategy)
    result = await agent.run(prompt, deps=deps)
    output = result.output

    # Calculate NO-side metrics (derived from p_no = 1 - p_yes)
    p_no = 1 - output.estimated_true_probability
    no_price = opportunity.no_price

    edge_no = calculate_edge(p_no, no_price)

    try:
        ev_no = calculate_expected_value(p_no, no_price)
    except ValueError:
        ev_no = 0.0

    size_no = calculate_position_size_pct(p_no, no_price)

    output = output.model_copy(update={
        "edge_no": edge_no,
        "expected_value_no": ev_no,
        "suggested_position_pct_no": size_no,
    })

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    if resolved_strategy == "sure_thing":
        recommendation_section = f"""---

## Trade Evaluation

| Side | Edge | EV | Suggested Size |
|------|------|-----|----------------|
| **YES** |  |  |  |
| **NO** |  |  |  |

**Status**: Pending

### Reasoning

{output.reasoning}"""
        frontmatter_updates = {
            "estimated_true_probability": None,
            "current_market_price": None,
            "expected_value": None,
            "edge": None,
            "suggested_position_pct": None,
            "edge_no": None,
            "expected_value_no": None,
            "suggested_position_pct_no": None,
            "recommendation_completed_at": completed_at.isoformat(),
            "action": None,
            "status": "recommended",
        }
    else:
        recommendation_section = f"""---

## Trade Evaluation

| Side | Edge | EV | Suggested Size |
|------|------|-----|----------------|
| **YES** | {output.edge:+.0%} | {output.expected_value:+.0%} | {output.suggested_position_pct:.1%} |
| **NO** | {output.edge_no:+.0%} | {output.expected_value_no:+.0%} | {output.suggested_position_pct_no:.1%} |

**Status**: Pending

### Reasoning

{output.reasoning}"""
        frontmatter_updates = {
            "estimated_true_probability": output.estimated_true_probability,
            "current_market_price": output.current_market_price,
            "expected_value": output.expected_value,
            "edge": output.edge,
            "suggested_position_pct": output.suggested_position_pct,
            "edge_no": output.edge_no,
            "expected_value_no": output.expected_value_no,
            "suggested_position_pct_no": output.suggested_position_pct_no,
            "recommendation_completed_at": completed_at.isoformat(),
            "action": None,
            "status": "recommended",
        }

    append_to_opportunity(
        market_ticker=opportunity.market_ticker,
        frontmatter_updates=frontmatter_updates,
        body_section=recommendation_section,
        section_header="## Trade Evaluation",
    )

    edge_str = f"{output.edge:+.0%}" if output.edge is not None else "N/A"
    ev_str = f"{output.expected_value:+.0%}" if output.expected_value is not None else "N/A"
    logger.info(f"Recommender completed in {duration:.1f}s - Edge: {edge_str}, EV: {ev_str}")

    updated_opp = load_opportunity_from_file(opp_file)
    return output, updated_opp


def _build_decision_prompt(opportunity: OpportunitySignal, markdown_body: str) -> str:
    """Build the evaluation prompt for the agent."""
    header = format_opportunity_header(opportunity)

    return f"""Evaluate this research and compute trade metrics (no final trade decision).

## Opportunity Details

{header}

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


def _build_sure_thing_decision_prompt(
    opportunity: OpportunitySignal, markdown_body: str
) -> str:
    """Build the evaluation prompt for sure-thing strategy."""
    header = format_opportunity_header(opportunity)

    return f"""Evaluate this sure-thing research and set risk-based trade metrics (no final trade decision).

## Opportunity Details

{header}

## Full Research Context

{markdown_body}

## Your Task

1. Review the research above carefully
2. Identify the overall risk level (HIGH / MEDIUM / LOW) based on the research
3. Set `estimated_true_probability` equal to the market price
4. Set edge/EV to 0.0 (these metrics are not used for sure-thing decisions)
5. Set `suggested_position_pct` to 0.0 (sizing is handled later by Trader)
6. Do not make a final BUY/NO decision (leave action unset)
7. Do not use Kelly sizing or `calculate_position_size`

## Important

- Always set suggested_position_pct to 0.0 in sure-thing mode
- Be disciplined and conservative. When in doubt, downgrade risk
"""
