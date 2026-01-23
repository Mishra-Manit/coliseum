"""Recommender Agent: Trade decision making based on research."""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
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
from coliseum.config import Settings
from coliseum.llm_providers import FireworksModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    extract_research_from_opportunity,
    load_opportunity_with_all_stages,
)
from coliseum.storage.state import update_market_status

logger = logging.getLogger(__name__)

_agent: Agent[RecommenderDependencies, RecommenderOutput] | None = None


def get_agent() -> Agent[RecommenderDependencies, RecommenderOutput]:
    global _agent
    if _agent is None:
        _agent = _create_agent()
    return _agent


def _create_agent() -> Agent[RecommenderDependencies, RecommenderOutput]:
    agent = Agent(
        model=get_model_string(FireworksModel.DEEPSEEK_V3_2),
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
        """Load opportunity with research data (synthesis, sources)."""
        opportunity_id = ctx.deps.opportunity_id
        opp_file = _find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

        # Extract market_ticker from frontmatter to load opportunity
        content = opp_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        market_ticker = frontmatter["market_ticker"]

        opportunity = load_opportunity_with_all_stages(market_ticker)
        research_data = extract_research_from_opportunity(opp_file)

        return {
            "id": opportunity.id,
            "event_ticker": opportunity.event_ticker,
            "market_ticker": opportunity.market_ticker,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "synthesis": research_data["synthesis"],
            "sources": research_data["sources"],
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
    opp_file = _find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    # Get market_ticker from frontmatter first
    content = opp_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    market_ticker = frontmatter["market_ticker"]

    opportunity = load_opportunity_with_all_stages(market_ticker)

    # Verify research exists
    if not opportunity.research_completed_at:
        raise ValueError(f"Research not completed for {opportunity_id}")

    # Extract research data from file
    research_data = extract_research_from_opportunity(opp_file)

    # Run recommendation
    deps = RecommenderDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    prompt = _build_decision_prompt(opportunity, research_data)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    # Prepare recommendation section for append
    action_label = output.action if hasattr(output, 'action') and output.action else "PENDING"
    recommendation_section = f"""---

## Trade Evaluation

| Metric | Value |
|--------|-------|
| **Action** | {action_label} |
| **Edge** | {output.edge:+.0%} |
| **Expected Value** | {output.expected_value:+.0%} |
| **Suggested Size** | {output.suggested_position_pct:.1%} of portfolio |
| **Status** | Pending |

### Reasoning

{output.reasoning}"""

    # Prepare frontmatter updates
    frontmatter_updates = {
        "estimated_true_probability": output.estimated_true_probability,
        "current_market_price": output.current_market_price,
        "expected_value": output.expected_value,
        "edge": output.edge,
        "suggested_position_pct": output.suggested_position_pct,
        "recommendation_completed_at": completed_at.isoformat(),
        "action": None,  # No action field in output
        "recommendation_status": "pending",
        "status": "evaluated",
    }

    # Append to opportunity file
    if not dry_run:
        append_to_opportunity(
            market_ticker=opportunity.market_ticker,
            frontmatter_updates=frontmatter_updates,
            body_section=recommendation_section,
            section_header="## Trade Evaluation",
        )

        # Update state.yaml status
        update_market_status(opportunity.market_ticker, "evaluated")

    logger.info(
        f"Recommender completed in {duration:.1f}s - "
        f"Edge: {output.edge:+.0%}, EV: {output.expected_value:+.0%}"
    )

    # Return updated opportunity
    updated_opp = load_opportunity_with_all_stages(opportunity.market_ticker)
    return output, updated_opp


def _find_opportunity_file_by_id(opportunity_id: str) -> Path | None:
    """Find opportunity file by searching for ID in YAML frontmatter."""
    from coliseum.storage.files import get_data_dir

    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"

    if not opps_dir.exists():
        return None

    date_dirs = sorted(opps_dir.iterdir(), reverse=True)
    for date_dir in date_dirs:
        if not date_dir.is_dir():
            continue

        for file_path in date_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")

                if not content.startswith("---"):
                    continue

                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue

                frontmatter = yaml.safe_load(parts[1])
                if frontmatter and frontmatter.get("id") == opportunity_id:
                    return file_path

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue

    return None


def _build_decision_prompt(opportunity: OpportunitySignal, research_data: dict) -> str:
    """Build the evaluation prompt for the agent."""
    sources = research_data.get("sources", [])
    synthesis = research_data.get("synthesis", "")
    sources_md = "\n".join(f"{i+1}. {src}" for i, src in enumerate(sources))

    prompt = f"""Evaluate this research and compute trade metrics (no final trade decision).

## Opportunity Details

**Market**: {opportunity.event_ticker}
**YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)
**Sources**: {len(sources)} credible sources

## Research Synthesis

{synthesis}

## Sources

{sources_md}

## Your Task

1. Use `read_opportunity_research` to load full research details
2. Evaluate the quality and reliability of the research
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
