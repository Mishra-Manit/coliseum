"""Scout Agent: Market discovery and opportunity filtering."""

import json
import logging

import logfire
from pydantic_ai import Agent, RunContext, WebSearchTool

from coliseum.agents.shared_tools import register_get_current_time
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.state import add_seen_ticker, get_seen_tickers

from .models import ScoutDependencies, ScoutOutput
from .prompts import build_scout_prompt

logger = logging.getLogger(__name__)


def _create_scout_agent(prompt: str) -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent with the provided system prompt."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=prompt,
        builtin_tools=[WebSearchTool()],
    )


def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the Scout agent."""

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        """Generate a unique opportunity ID with opp_ prefix."""
        return generate_opportunity_id()

    register_get_current_time(agent)


async def _prefetch_markets_for_scan(
    client: KalshiClient,
    settings: Settings,
    seen_tickers: set[str] | None = None,
) -> list[dict]:
    """Fetch and pre-filter market dataset once before Scout agent run."""
    scout_settings = settings.scout
    min_close_hours = scout_settings.min_close_hours
    max_close_hours = scout_settings.max_close_hours
    min_price = scout_settings.min_price
    max_price = scout_settings.max_price
    min_volume = scout_settings.min_volume
    max_spread = scout_settings.max_spread_cents

    markets = await client.get_markets_closing_in_range(
        min_hours=min_close_hours,
        max_hours=max_close_hours,
        limit=scout_settings.market_fetch_limit,
        status="open",
    )
    logger.info("Scout prefetch fetched %d markets closing in %d-%d hours", len(markets), min_close_hours, max_close_hours)

    if seen_tickers:
        markets = [m for m in markets if m.ticker not in seen_tickers]
        logger.info("Scout prefetch filtered to %d markets after removing seen tickers", len(markets))

    markets = [m for m in markets if m.volume >= min_volume]
    logger.info("Scout prefetch filtered to %d markets with volume >= %d", len(markets), min_volume)

    markets = [
        m
        for m in markets
        if min_price <= (m.yes_ask or 50) <= max_price
        or min_price <= (m.no_ask or 50) <= max_price
    ]
    logger.info("Scout prefetch filtered to %d markets with YES or NO in %d-%d%% range", len(markets), min_price, max_price)

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
        logger.info("Scout prefetch filtered to %d markets with spread <= %d cents", len(markets), max_spread)

    market_descriptions = [
        (
            f"{m.ticker} - {m.title} | {m.subtitle}"
            if m.title and m.subtitle
            else f"{m.ticker} - {(m.title or m.subtitle or m.event_ticker or 'Unknown event')}"
        )
        for m in markets
    ]
    logger.info(
        "Scout prefetch markets available for research (%d total):\n%s",
        len(markets),
        "\n".join(market_descriptions) if market_descriptions else "No markets available",
    )

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
            "spread_cents": (m.yes_ask - m.yes_bid) if (m.yes_ask is not None and m.yes_bid is not None) else None,
            "spread_pct": ((m.yes_ask - m.yes_bid) / 100) if (m.yes_ask is not None and m.yes_bid is not None) else None,
            "volume": m.volume,
            "open_interest": m.open_interest,
            "close_time": m.close_time.isoformat() if m.close_time else None,
        }
        for m in markets
    ]


def _build_market_context_prompt(prefetched_markets: list[dict]) -> str:
    """Build prompt context containing pre-fetched market dataset."""
    market_count = len(prefetched_markets)
    serialized_markets = json.dumps(prefetched_markets, ensure_ascii=True, separators=(",", ":"))
    return (
        f"\n\nPREFETCHED_MARKETS_COUNT: {market_count}\n"
        "\n\nPREFETCHED_MARKETS_JSON:\n"
        f"{serialized_markets}\n\n"
        "Use this dataset as the complete market universe for this scan. "
        "Set markets_scanned exactly to PREFETCHED_MARKETS_COUNT (equivalently, len(PREFETCHED_MARKETS_JSON)). "
        "Do not self-estimate markets_scanned from researched/evaluated/selected subsets. "
        "Do not claim to have scanned markets outside this provided dataset."
    )


def get_scout_agent(settings: Settings | None = None) -> Agent[ScoutDependencies, ScoutOutput]:
    """Build a Scout agent configured for market scanning."""
    if settings is None:
        settings = get_settings()
    prompt = build_scout_prompt(settings)
    agent = _create_scout_agent(prompt)
    _register_tools(agent)
    return agent


async def run_scout(
    settings: Settings | None = None,
) -> ScoutOutput:
    """Execute a Scout scan and save opportunities."""
    if settings is None:
        settings = get_settings()

    seen_tickers = get_seen_tickers()

    with logfire.span("scout scan"):
        # Scout always reads from production API (market data is public)
        kalshi_config = KalshiConfig(paper_mode=False)
        async with KalshiClient(config=kalshi_config) as client:
            with logfire.span("prefetch markets"):
                prefetched_markets = await _prefetch_markets_for_scan(
                    client,
                    settings,
                    seen_tickers=set(seen_tickers),
                )
                logfire.info("Markets prefetched", count=len(prefetched_markets))

            deps = ScoutDependencies(settings=settings, prefetched_markets=prefetched_markets)

            with logfire.span("agent run", markets=len(prefetched_markets)):
                agent = get_scout_agent(settings)
                scout_cfg = settings.scout
                prompt = (
                    f"Scan Kalshi markets for near-decided opportunities—markets at "
                    f"{scout_cfg.min_price}-{scout_cfg.max_price}% where the outcome "
                    f"is strongly favored with negligible or low reversal risk. "
                    f"Find exactly 1 opportunity—the single least-risky qualifying market. "
                    f"Select markets that pass the Risk Assessment Checklist. Remember: residual uncertainty is normal for open markets—do not skip a market just because the outcome is not yet 100% official. "
                    f"CRITICAL: You MUST return at least 1 opportunity. If no market meets the ideal risk threshold, select the single least-risky available market as a fallback and label it clearly in the rationale."
                    f"{_build_market_context_prompt(prefetched_markets)}"
                )
                result = await agent.run(prompt, deps=deps)

            output: ScoutOutput = result.output

            added_count = 0
            for opp in output.opportunities:
                try:
                    save_opportunity(opp)
                    add_seen_ticker(opp.market_ticker)
                    added_count += 1
                except Exception as e:
                    logfire.error("Failed to save opportunity", opportunity_id=opp.id, error=str(e))

            logfire.info(
                "Scout scan complete",
                opportunities_found=output.opportunities_found,
                added=added_count,
            )

        return output
