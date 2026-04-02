"""Scribe: LLM reflection agent that updates learnings.md when positions close."""

from __future__ import annotations

import logging

import logfire
from pydantic_ai import Agent

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.guardian.models import LearningReflectionOutput
from coliseum.agents.guardian.prompts import SCRIBE_PROMPT
from coliseum.memory.learnings import load_learnings, _get_learnings_path
from coliseum.storage._io import atomic_write
from coliseum.storage.files import find_opportunity_file_by_id, get_opportunity_markdown_body
from coliseum.storage.state import ClosedPosition

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[None, LearningReflectionOutput]:
    return create_agent(
        prompt=SCRIBE_PROMPT,
        output_type=LearningReflectionOutput,
        use_responses_api=False,
    )


_agent_factory: AgentFactory[None, LearningReflectionOutput] = AgentFactory(
    create_fn=_create_agent
)


def get_agent() -> Agent[None, LearningReflectionOutput]:
    """Get the singleton Scribe agent instance."""
    return _agent_factory.get_agent()


def _load_opportunity_body(opportunity_id: str | None) -> str | None:
    """Load full opportunity markdown body for richer reflection context."""
    if not opportunity_id:
        return None
    try:
        opp_file = find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            return None
        return get_opportunity_markdown_body(opp_file)
    except Exception as exc:
        logger.warning("Scribe could not load opportunity body for %s: %s", opportunity_id, exc)
        return None


def _format_trade_block(pos: ClosedPosition, opportunity_body: str | None) -> str:
    """Format a single closed position into a readable block for the prompt."""
    if pos.pnl >= 0:
        pnl_sign = "+"
    else:
        pnl_sign = ""
    if pos.pnl >= 0:
        outcome = "WIN"
    else:
        outcome = "LOSS"
    entry_cents = round(pos.entry_price * 100)
    exit_cents = round(pos.exit_price * 100)

    lines = [
        f"### {pos.market_ticker} ({outcome}, {pnl_sign}${pos.pnl:.2f})",
        f"- Side: {pos.side} | Entry: {entry_cents}¢ | Exit: {exit_cents}¢"
        f" | Contracts: {pos.contracts}",
    ]

    if pos.entry_rationale:
        lines.append(f"- **Entry Rationale**: {pos.entry_rationale}")

    if opportunity_body:
        lines.append("")
        lines.append("**Full Research**:")
        lines.append(opportunity_body)

    return "\n".join(lines)


def _build_prompt(
    newly_closed: list[ClosedPosition],
    opportunity_bodies: dict[str, str | None],
    current_learnings: str,
) -> str:
    """Build the reflection prompt from closed positions and current learnings."""
    trade_blocks = []
    for i, pos in enumerate(newly_closed, start=1):
        body = opportunity_bodies.get(pos.opportunity_id or "", None)
        trade_blocks.append(f"## Trade {i}\n\n{_format_trade_block(pos, body)}")

    trades_section = "\n\n---\n\n".join(trade_blocks)

    return f"""Analyze the following closed positions and update the learnings document.

{trades_section}

---

## Current Learnings

{current_learnings}

---

Update the learnings document based on what these trade outcomes reveal. Return the complete
updated document and a one-sentence summary of what changed.
"""


def _write_learnings(content: str) -> None:
    """Atomically write updated content to learnings.md."""
    learnings_path = _get_learnings_path()
    atomic_write(learnings_path, content)
    logger.debug("Scribe wrote updated learnings to %s", learnings_path)


async def run_scribe(newly_closed: list[ClosedPosition]) -> str:
    """Reflect on closed positions and update learnings.md. Returns the change summary."""
    current_learnings = load_learnings()

    opportunity_bodies: dict[str, str | None] = {
        pos.opportunity_id: _load_opportunity_body(pos.opportunity_id)
        for pos in newly_closed
        if pos.opportunity_id
    }

    prompt = _build_prompt(newly_closed, opportunity_bodies, current_learnings)

    with logfire.span("scribe reflection", trades=len(newly_closed)):
        agent = get_agent()
        result = await agent.run(prompt)
        output = result.output

    _write_learnings(output.updated_learnings_md)
    logfire.info("Scribe updated learnings", summary=output.summary, trades=len(newly_closed))

    return output.summary
