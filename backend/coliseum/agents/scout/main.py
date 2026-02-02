"""Scout Agent: Market discovery and opportunity filtering."""

import logging
from datetime import datetime, timezone
from typing import Literal

from pydantic_ai import Agent, RunContext, WebSearchTool

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.shared_tools import register_get_current_time
from coliseum.config import Settings, Strategy, get_settings
from coliseum.llm_providers import AnthropicModel, FireworksModel, OpenAIModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.memory import (
    MemoryEntry,
    append_memory_entry,
    get_seen_tickers,
    is_market_seen,
)

from .models import ScoutDependencies, ScoutOutput
from .prompts import SCOUT_SYSTEM_PROMPT, SCOUT_SURE_THING_PROMPT

logger = logging.getLogger(__name__)

# Strategy-specific constants
EDGE_FILTERS = {"min_close_hours": 96, "max_close_hours": 240, "min_price": 10, "max_price": 90}
SURE_THING_FILTERS = {"min_close_hours": 0, "max_close_hours": 48, "min_price": 92, "max_price": 96, "max_spread_cents": 3}


def _create_scout_agent(strategy: Strategy = Strategy.EDGE) -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent with strategy-specific prompt."""
    prompt = SCOUT_SURE_THING_PROMPT if strategy == Strategy.SURE_THING else SCOUT_SYSTEM_PROMPT
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_MINI),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=prompt,
        builtin_tools=[WebSearchTool()],
    )


def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput], strategy: Strategy = Strategy.EDGE) -> None:
    """Register tools with the Scout agent."""
    filters = SURE_THING_FILTERS if strategy == Strategy.SURE_THING else EDGE_FILTERS

    @agent.tool
    async def fetch_markets_closing_soon(
        ctx: RunContext[ScoutDependencies],
    ) -> list[dict]:
        """Fetch markets closing within the configured time window.

        Returns:
            List of market dictionaries with ticker, title, volume, prices, spread, close_time
        """
        min_close_hours = filters["min_close_hours"]
        max_close_hours = filters["max_close_hours"]
        min_price = filters["min_price"]
        max_price = filters["max_price"]
        min_volume = 5000
        market_fetch_limit = ctx.deps.settings.scout.market_fetch_limit

        markets = await ctx.deps.kalshi_client.get_markets_closing_in_range(
            min_hours=min_close_hours,
            max_hours=max_close_hours,
            limit=market_fetch_limit,
            status="open",
        )
        logger.info("Scout fetched %d markets closing in %d-%d hours", len(markets), min_close_hours, max_close_hours)

        markets = [m for m in markets if m.volume >= min_volume]
        logger.info("Scout filtered to %d markets with volume >= %d", len(markets), min_volume)

        markets = [
            m
            for m in markets
            if min_price <= (m.yes_ask or 50) <= max_price
            or min_price <= (m.no_ask or 50) <= max_price
        ]
        logger.info("Scout filtered to %d markets with YES or NO in %d-%d%% range", len(markets), min_price, max_price)

        # Apply spread filter only for sure_thing strategy
        max_spread = filters.get("max_spread_cents")
        if max_spread is not None:
            filtered_markets = []
            for m in markets:
                yes_in_range = min_price <= (m.yes_ask or 50) <= max_price
                no_in_range = min_price <= (m.no_ask or 50) <= max_price

                if yes_in_range and m.yes_ask is not None and m.yes_bid is not None:
                    spread = m.yes_ask - m.yes_bid
                    if spread <= max_spread:
                        filtered_markets.append(m)
                elif no_in_range and m.no_ask is not None and m.no_bid is not None:
                    spread = m.no_ask - m.no_bid
                    if spread <= max_spread:
                        filtered_markets.append(m)

            markets = filtered_markets
            logger.info("Scout filtered to %d markets with spread <= %d cents", len(markets), max_spread)

        return [
            {
                "ticker": m.ticker,
                "event_ticker": m.event_ticker,
                "title": m.title,
                "subtitle": m.subtitle,
                "yes_bid": m.yes_bid,
                "yes_ask": m.yes_ask,
                "no_bid": m.no_bid,
                "no_ask": m.no_ask,
                "spread_cents": (m.yes_ask - m.yes_bid) if (m.yes_ask and m.yes_bid) else None,
                "spread_pct": ((m.yes_ask - m.yes_bid) / 100) if (m.yes_ask and m.yes_bid) else None,
                "volume": m.volume,
                "open_interest": m.open_interest,
                "close_time": m.close_time.isoformat() if m.close_time else None,
            }
            for m in markets
        ]

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        """Generate a unique opportunity ID with opp_ prefix."""
        return generate_opportunity_id()

    register_get_current_time(agent)


_edge_factory = AgentFactory(
    create_fn=lambda: _create_scout_agent(Strategy.EDGE),
    register_tools_fn=lambda agent: _register_tools(agent, Strategy.EDGE),
)

_sure_thing_factory = AgentFactory(
    create_fn=lambda: _create_scout_agent(Strategy.SURE_THING),
    register_tools_fn=lambda agent: _register_tools(agent, Strategy.SURE_THING),
)


def get_scout_agent(strategy: Strategy = Strategy.EDGE) -> Agent[ScoutDependencies, ScoutOutput]:
    """Get the singleton Scout agent instance for the given strategy."""
    if strategy == Strategy.SURE_THING:
        return _sure_thing_factory.get_agent()
    return _edge_factory.get_agent()


async def run_scout(
    settings: Settings | None = None,
    dry_run: bool = False,
    strategy: Strategy = Strategy.EDGE,
) -> ScoutOutput:
    """Execute a Scout scan and optionally save opportunities."""
    if settings is None:
        settings = get_settings()

    mode_label = "[DRY RUN] " if dry_run else ""
    logger.info(f"{mode_label}Starting Scout scan (strategy={strategy.value})...")

    # Get currently tracked markets from memory to inject into prompt context
    seen_tickers = get_seen_tickers()
    seen_context = ""
    if seen_tickers:
        seen_context = (
            "\n\nPREVIOUSLY DISCOVERED MARKETS (DO NOT SELECT THESE - already being processed):\n"
            + "\n".join(f"- {ticker}" for ticker in seen_tickers)
        )
        logger.debug(f"Injecting {len(seen_tickers)} seen tickers into prompt context")

    # Scout always reads from production API (market data is public)
    from coliseum.services.kalshi.config import KalshiConfig
    kalshi_config = KalshiConfig(paper_mode=False)
    async with KalshiClient(config=kalshi_config) as client:
        deps = ScoutDependencies(kalshi_client=client, settings=settings)

        # Run the agent with seen markets context
        agent = get_scout_agent(strategy)
        if strategy == Strategy.SURE_THING:
            prompt = (
                f"Scan Kalshi markets for SURE THING opportunities—markets at 92-96% where the outcome is locked in "
                f"or near-decided with no swing risk. "
                f"Find up to {settings.scout.max_opportunities_per_scan} opportunities. "
                f"Only select markets that pass the No-Swing Risk Checklist in the prompt."
                f"{seen_context}"
            )
        else:
            prompt = (
                f"Scan Kalshi markets and identify {settings.scout.max_opportunities_per_scan} "
                f"high-quality trading opportunities. "
                f"Only include markets with significant volume (>10,000 contracts) to ensure liquidity."
                f"{seen_context}"
            )
        result = await agent.run(prompt, deps=deps)

        output: ScoutOutput = result.output

        # Skip persistence in dry-run mode
        if dry_run:
            logger.info(
                f"{mode_label}Scout scan complete: "
                f"{output.opportunities_found} opportunities found "
                f"(not saved - dry run mode)"
            )
            return output

        # Process opportunities and add to memory
        now = datetime.now(timezone.utc)
        skipped_count = 0
        added_count = 0

        for opp in output.opportunities:
            try:
                # Check if already seen (via memory system)
                if is_market_seen(opp.market_ticker):
                    logger.info(
                        f"Skipping duplicate: {opp.market_ticker} (already in memory)"
                    )
                    skipped_count += 1
                    continue

                # Set strategy on opportunity before saving
                opp.strategy = strategy.value

                # Save opportunity file
                save_opportunity(opp)
                logger.info(f"Saved opportunity: {opp.market_ticker}")

                # Add stub entry to memory (will be enriched by Trader)
                memory_entry = MemoryEntry(
                    market_ticker=opp.market_ticker,
                    discovered_at=now,
                    close_time=opp.close_time,
                    status="PENDING",
                )
                append_memory_entry(memory_entry)
                added_count += 1

            except Exception as e:
                logger.error(f"Failed to save opportunity {opp.id}: {e}")

        logger.info(
            f"Scout scan complete: "
            f"{output.opportunities_found} opportunities found, "
            f"{skipped_count} skipped (duplicates), "
            f"{added_count} added to memory"
        )

        return output


def scout_scan_job() -> None:
    """Scheduler job wrapper for market scan (blocking)."""
    import asyncio

    try:
        result = asyncio.run(run_scout())
        logger.info(f"✓ Scout scan: {result.opportunities_found} opportunities")
    except Exception as e:
        logger.error(f"Scout scan failed: {e}", exc_info=True)
