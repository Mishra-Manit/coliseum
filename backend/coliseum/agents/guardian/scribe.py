"""Scribe: LLM reflection agent that updates learnings when positions close."""

from __future__ import annotations

import asyncio
import logging

import logfire
from pydantic_ai import Agent

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.guardian.models import LearningReflectionOutput
from coliseum.agents.guardian.prompts import SCRIBE_PROMPT
from coliseum.services.supabase.repositories.learnings import (
    apply_scribe_operations,
    load_learnings_from_db,
)
from coliseum.storage._io import atomic_write
from coliseum.storage.files import find_opportunity_file_by_id, get_opportunity_markdown_body
from coliseum.storage.state import ClosedPosition, get_data_dir

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


async def _load_opportunity_body(opportunity_id: str) -> str | None:
    """Load full opportunity markdown body for richer reflection context."""
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
        outcome = "WIN"
    else:
        pnl_sign = ""
        outcome = "LOSS"
    entry_cents = round(pos.entry_price * 100)
    exit_cents = round(pos.exit_price * 100)

    lines = [
        f"### {pos.market_ticker} ({outcome}, {pnl_sign}${pos.pnl:.2f})",
        f"- Side: {pos.side} | Entry: {entry_cents}c | Exit: {exit_cents}c"
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

    return f"""Analyze the following closed positions and update the learnings.

{trades_section}

---

## Current Learnings (each row has an [#ID] prefix)

{current_learnings}

---

Review the trade outcomes against the current learnings. Return your deletions (row IDs to retire)
and additions (new learnings to add). If no changes are warranted, return empty lists.
"""


def _write_learnings_fallback(content: str) -> None:
    """Write learnings markdown to local file as disaster-recovery fallback."""
    learnings_path = get_data_dir() / "memory" / "learnings.md"
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(learnings_path, content)
    logger.debug("Scribe wrote learnings fallback to %s", learnings_path)


async def run_scribe(newly_closed: list[ClosedPosition]) -> str:
    """Reflect on closed positions and update learnings in DB. Returns the change summary."""
    current_learnings = await load_learnings_from_db()

    unique_opp_ids = [pos.opportunity_id for pos in newly_closed if pos.opportunity_id]
    body_results = await asyncio.gather(
        *[_load_opportunity_body(opp_id) for opp_id in unique_opp_ids]
    )
    opportunity_bodies: dict[str, str | None] = dict(zip(unique_opp_ids, body_results))

    prompt = _build_prompt(newly_closed, opportunity_bodies, current_learnings)

    with logfire.span("scribe reflection", trades=len(newly_closed)):
        agent = get_agent()
        result = await agent.run(prompt)
        output = result.output

    # Apply structured operations to DB
    db_success = False
    try:
        await apply_scribe_operations(output.deletions, output.additions)
        db_success = True
    except Exception as exc:
        logfire.error(
            "Scribe DB operations failed -- learnings lost",
            error=str(exc),
            pending_deletions=output.deletions,
            pending_additions=[
                {"category": a.category, "content": a.content}
                for a in output.additions
            ],
        )

    # Local fallback: only re-fetch and write if DB succeeded (otherwise stale)
    if db_success:
        try:
            updated_learnings = await load_learnings_from_db()
            _write_learnings_fallback(updated_learnings)
        except Exception as exc:
            logger.warning("Scribe local fallback write failed: %s", exc)

    logfire.info(
        "Scribe updated learnings",
        summary=output.summary,
        trades=len(newly_closed),
        deletions=len(output.deletions),
        additions=len(output.additions),
    )

    return output.summary
