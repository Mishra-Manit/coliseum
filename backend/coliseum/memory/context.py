"""Context assemblers: load memory and format it for injection into agent prompts."""

import logging

from coliseum.memory.decisions import DecisionEntry, load_recent_decisions
from coliseum.memory.learnings import load_learnings
from coliseum.storage.state import PortfolioState, load_state

logger = logging.getLogger(__name__)


def _format_decisions(decisions: list[DecisionEntry]) -> str:
    if not decisions:
        return "  (none)"
    lines = []
    for d in decisions:
        price_str = f"@ {d.price * 100:.0f}¢" if d.price else ""
        status_str = f"({d.execution_status})" if d.execution_status else ""
        reason_str = f' — "{d.reasoning[:80]}"' if d.reasoning else ""
        lines.append(f"  - {d.action} {d.ticker} {price_str} {status_str}{reason_str}")
    return "\n".join(lines)


def _format_portfolio(state: PortfolioState) -> str:
    p = state.portfolio
    positions = len(state.open_positions)
    tickers = ", ".join(pos.market_ticker for pos in state.open_positions) if state.open_positions else "none"
    return (
        f"  Cash: ${p.cash_balance:.2f} | Positions: ${p.positions_value:.2f} "
        f"({positions} open) | Total: ${p.total_value:.2f}\n"
        f"  Open tickers: {tickers}"
    )


def build_scout_context() -> str:
    """Assemble context block for the Scout agent's user prompt."""
    try:
        state = load_state()
        decisions = load_recent_decisions(hours=24)
        learnings = load_learnings(section="Market Patterns")
    except Exception as exc:
        logger.warning("build_scout_context failed: %s", exc)
        return ""

    portfolio_block = _format_portfolio(state)
    decisions_block = _format_decisions(decisions)

    return f"""
## System Memory Context

### Portfolio State
{portfolio_block}

### Recent Decisions (last 24h)
{decisions_block}

### System Learnings — Market Patterns
{learnings}

Use this context to avoid re-researching recently skipped tickers and to understand current portfolio exposure before selecting an opportunity.
"""


def build_analyst_context() -> str:
    """Assemble context block for the Analyst Researcher's and Recommender's prompt."""
    try:
        state = load_state()
    except Exception as exc:
        logger.warning("build_analyst_context failed: %s", exc)
        return ""

    portfolio_block = _format_portfolio(state)
    if state.open_positions:
        lines = [
            f"  - {pos.market_ticker} ({pos.side}, {pos.contracts} contracts @ {pos.average_entry * 100:.0f}¢)"
            for pos in state.open_positions
        ]
        positions_detail = "\n".join(lines)
    else:
        positions_detail = "  (no open positions)"

    return f"""
## Portfolio Context

{portfolio_block}

Open position detail:
{positions_detail}

Account for concentration risk — avoid recommending a position in the same market as an existing holding.
"""


def build_trader_context() -> str:
    """Assemble context block for the Trader agent's prompt."""
    try:
        state = load_state()
        decisions = load_recent_decisions(hours=48)
    except Exception as exc:
        logger.warning("build_trader_context failed: %s", exc)
        return ""

    portfolio_block = _format_portfolio(state)
    decisions_block = _format_decisions(decisions)

    return f"""
## Execution Memory

### Portfolio State
{portfolio_block}

### Recent Decisions (last 48h)
{decisions_block}

Use recent decisions to detect patterns (e.g., repeated fills at lower-than-ask prices, or repeated rejections on similar market types).
"""
