"""Guardian Agent: LLM-orchestrated portfolio reconciler."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.shared_tools import register_get_current_time
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.services.kalshi import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.state import ClosedPosition, PortfolioState, Position, load_state, save_state
from coliseum.storage.sync import (
    extract_fill_count,
    extract_fill_price,
    fetch_market_side_price,
    normalize_kalshi_side,
    sync_portfolio_from_kalshi,
)

from .models import GuardianDependencies, GuardianResult, ReconciliationStats
from .prompts import GUARDIAN_SYSTEM_PROMPT, build_guardian_prompt

logger = logging.getLogger(__name__)


def _get_sell_fill_prices(
    fills: list[dict[str, object]],
    market_ticker: str,
    side: str,
) -> list[tuple[float, int]]:
    """Extract sell fill prices for a specific market and side."""
    prices: list[tuple[float, int]] = []
    for fill in fills:
        ticker = fill.get("ticker") or fill.get("market_ticker")
        if ticker != market_ticker:
            continue
        fill_side = normalize_kalshi_side(str(fill.get("side")) if fill.get("side") else None)
        if fill_side != side:
            continue
        action = fill.get("action")
        if action and str(action).lower() not in {"sell", "s"}:
            continue
        count = extract_fill_count(fill)
        if not count:
            continue
        price = extract_fill_price(fill, side)
        if price is None:
            continue
        prices.append((price, count))
    return prices


def _weighted_average(prices: list[tuple[float, int]]) -> float | None:
    """Compute weighted average price from (price, count) pairs."""
    if not prices:
        return None
    total_cost = sum(price * count for price, count in prices)
    total_count = sum(count for _, count in prices)
    if total_count <= 0:
        return None
    return total_cost / total_count


async def _fetch_market_price(
    client: KalshiClient,
    market_ticker: str,
    side: str,
) -> float | None:
    """Fetch current market price as a fallback for exit price."""
    try:
        return await fetch_market_side_price(client, market_ticker, side)
    except Exception as exc:
        logger.warning("Guardian failed to fetch market for %s: %s", market_ticker, exc)
        return None


async def _compute_exit_outcome(
    pos: Position,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[float, float]:
    """Return (exit_price, pnl) for a position that closed."""
    side = pos.side
    contracts = pos.contracts
    entry_price = pos.average_entry

    exit_prices = _get_sell_fill_prices(fills, pos.market_ticker, side)
    exit_price = _weighted_average(exit_prices)

    if exit_price is None:
        exit_price = await _fetch_market_price(client, pos.market_ticker, side)
        if exit_price is None:
            exit_price = entry_price
            logger.warning("Guardian using entry price as estimate for %s", pos.market_ticker)
        else:
            logger.warning("Guardian using market price estimate for %s", pos.market_ticker)

    if side == "YES":
        pnl = (exit_price - entry_price) * contracts
    else:
        pnl = (entry_price - exit_price) * contracts

    return exit_price, pnl


async def reconcile_closed_positions(
    old_open: list[Position],
    new_state: PortfolioState,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[PortfolioState, ReconciliationStats]:
    """Detect positions that closed since last sync and move them to closed_positions."""
    new_open_keys = {(pos.market_ticker, pos.side) for pos in new_state.open_positions}
    stats = ReconciliationStats()
    newly_closed: list[ClosedPosition] = []

    for pos in old_open:
        stats.entries_inspected += 1
        key = (pos.market_ticker, pos.side)
        if key in new_open_keys:
            stats.kept_open += 1
            continue

        exit_price, pnl = await _compute_exit_outcome(pos, fills, client)
        newly_closed.append(
            ClosedPosition(
                market_ticker=pos.market_ticker,
                side=pos.side,
                contracts=pos.contracts,
                entry_price=pos.average_entry,
                exit_price=exit_price,
                pnl=pnl,
                opportunity_id=pos.opportunity_id,
                strategy=pos.strategy,
                traded_at=pos.traded_at,
                closed_at=datetime.now(timezone.utc),
                reasoning=pos.reasoning,
            )
        )
        stats.newly_closed += 1
        logger.info(
            "Guardian closed %s exit_price=%.4f pnl=$%.2f",
            pos.market_ticker,
            exit_price,
            pnl,
        )

    updated_state = PortfolioState(
        portfolio=new_state.portfolio,
        open_positions=new_state.open_positions,
        closed_positions=new_state.closed_positions + newly_closed,
        seen_tickers=new_state.seen_tickers,
    )
    save_state(updated_state)
    return updated_state, stats


def _find_positions_without_opportunity_id(state: PortfolioState) -> list[str]:
    """Find open positions that have no opportunity_id (not opened by our pipeline)."""
    return [
        f"{pos.market_ticker}:{pos.side}"
        for pos in state.open_positions
        if not pos.opportunity_id
    ]


def _create_guardian_agent() -> Agent[GuardianDependencies, GuardianResult]:
    """Create the Guardian agent for portfolio sync and reconciliation."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=GuardianResult,
        deps_type=GuardianDependencies,
        system_prompt=GUARDIAN_SYSTEM_PROMPT,
    )


def _register_tools(agent: Agent[GuardianDependencies, GuardianResult]) -> None:
    """Register tools used by Guardian for Kalshi sync and reconciliation."""

    @agent.tool
    async def sync_portfolio_from_kalshi_tool(
        ctx: RunContext[GuardianDependencies],
    ) -> dict[str, object]:
        """Sync local state.yaml from live Kalshi portfolio account data."""
        ctx.deps.pre_sync_open_positions = load_state().open_positions
        state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
        ctx.deps.synced_state = state
        return {
            "positions_synced": len(state.open_positions),
            "cash_balance": state.portfolio.cash_balance,
            "positions_value": state.portfolio.positions_value,
            "total_value": state.portfolio.total_value,
        }

    @agent.tool
    async def fetch_recent_fills(
        ctx: RunContext[GuardianDependencies],
        limit: int = 500,
    ) -> dict[str, object]:
        """Fetch recent account fills for closed position reconciliation."""
        fills = await ctx.deps.kalshi_client.get_fills(limit=limit)
        ctx.deps.fills = fills
        return {"fills_count": len(fills)}

    @agent.tool
    async def reconcile_closed_positions_tool(
        ctx: RunContext[GuardianDependencies],
    ) -> dict[str, object]:
        """Detect positions closed since last sync and move them to closed_positions in state.yaml."""
        if ctx.deps.synced_state is None:
            ctx.deps.pre_sync_open_positions = load_state().open_positions
            ctx.deps.synced_state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
        if ctx.deps.fills is None:
            ctx.deps.fills = await ctx.deps.kalshi_client.get_fills(limit=500)

        updated_state, stats = await reconcile_closed_positions(
            old_open=ctx.deps.pre_sync_open_positions,
            new_state=ctx.deps.synced_state,
            fills=ctx.deps.fills,
            client=ctx.deps.kalshi_client,
        )
        ctx.deps.synced_state = updated_state
        ctx.deps.reconciliation = stats
        return stats.model_dump()

    @agent.tool
    async def find_positions_without_opportunity_id_tool(
        ctx: RunContext[GuardianDependencies],
    ) -> list[str]:
        """Find open positions that have no opportunity_id (not opened by our pipeline)."""
        if ctx.deps.synced_state is None:
            ctx.deps.synced_state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
        return _find_positions_without_opportunity_id(ctx.deps.synced_state)

    @agent.tool
    async def summarize_synced_portfolio_tool(
        ctx: RunContext[GuardianDependencies],
    ) -> dict[str, object]:
        """Get a concise summary of synced portfolio state and open positions."""
        if ctx.deps.synced_state is None:
            ctx.deps.synced_state = await sync_portfolio_from_kalshi(ctx.deps.kalshi_client)
        state = ctx.deps.synced_state
        return {
            "positions_synced": len(state.open_positions),
            "cash_balance": state.portfolio.cash_balance,
            "positions_value": state.portfolio.positions_value,
            "total_value": state.portfolio.total_value,
            "open_positions": [
                {
                    "market_ticker": pos.market_ticker,
                    "side": pos.side,
                    "contracts": pos.contracts,
                    "average_entry": pos.average_entry,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                }
                for pos in state.open_positions
            ],
        }

    register_get_current_time(agent)


_guardian_factory = AgentFactory(
    create_fn=_create_guardian_agent,
    register_tools_fn=_register_tools,
)


def get_guardian_agent() -> Agent[GuardianDependencies, GuardianResult]:
    """Get the singleton Guardian agent instance."""
    return _guardian_factory.get_agent()


async def _run_guardian_fallback(client: KalshiClient) -> GuardianResult:
    """Run deterministic fallback reconciliation if agent orchestration fails."""
    pre_sync_state = load_state()
    state = await sync_portfolio_from_kalshi(client)
    fills = await client.get_fills(limit=500)
    updated_state, stats = await reconcile_closed_positions(
        old_open=pre_sync_state.open_positions,
        new_state=state,
        fills=fills,
        client=client,
    )
    missing = _find_positions_without_opportunity_id(updated_state)
    return GuardianResult(
        positions_synced=len(updated_state.open_positions),
        reconciliation=stats,
        warnings=missing,
        agent_summary="Fallback deterministic reconciliation executed after agent error.",
    )


async def run_guardian(settings: Settings | None = None) -> GuardianResult:
    """Run Guardian reconciliation cycle via LLM tool orchestration."""
    settings = settings or get_settings()
    if settings.trading.paper_mode and not settings.get_rsa_private_key():
        logger.warning("Guardian skipped -- no real Kalshi data")
        return GuardianResult(agent_summary="Guardian skipped due to missing Kalshi auth.")

    kalshi_config = KalshiConfig(paper_mode=settings.trading.paper_mode)
    private_key_pem = "" if settings.trading.paper_mode else settings.get_rsa_private_key()

    async with KalshiClient(
        config=kalshi_config,
        api_key=settings.kalshi_api_key,
        private_key_pem=private_key_pem,
    ) as client:
        deps = GuardianDependencies(
            kalshi_client=client,
            settings=settings,
        )
        agent = get_guardian_agent()
        try:
            result = await agent.run(build_guardian_prompt(), deps=deps)
            output = result.output
        except Exception as exc:
            logger.error("Guardian agent orchestration failed: %s", exc, exc_info=True)
            output = await _run_guardian_fallback(client)

    for missing_key in output.warnings:
        logger.warning("Guardian position missing opportunity_id: %s", missing_key)

    logger.info("Guardian synced %d positions from Kalshi", output.positions_synced)
    logger.info(
        "Guardian entries inspected=%d kept_open=%d closed=%d",
        output.reconciliation.entries_inspected,
        output.reconciliation.kept_open,
        output.reconciliation.newly_closed,
    )

    return output


def guardian_job() -> None:
    """Scheduler job wrapper for Guardian reconciliation."""
    try:
        result = asyncio.run(run_guardian())
        logger.info(
            "Guardian: %d positions synced, %d closed",
            result.positions_synced,
            result.reconciliation.newly_closed,
        )
    except Exception as exc:
        logger.error("Guardian run failed: %s", exc, exc_info=True)
