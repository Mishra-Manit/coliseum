"""Scout Agent: Market discovery and opportunity filtering."""

import asyncio
import json
import logging

import logfire
from pydantic_ai import Agent, RunContext, WebSearchTool
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

from coliseum.agents.shared_tools import register_get_current_time, _strip_cite_tokens
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.memory.context import build_scout_context
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.state import add_seen_ticker, get_seen_tickers

from .filters import passes_filter
from .models import ScoutDependencies, ScoutOutput
from .prompts import build_scout_prompt

logger = logging.getLogger(__name__)


def _create_scout_agent(prompt: str) -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent with the provided system prompt."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_4),
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        system_prompt=prompt,
        builtin_tools=[WebSearchTool()],
        model_settings=OpenAIResponsesModelSettings(openai_reasoning_effort="high"),
    )


def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the Scout agent."""

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        """Generate a unique opportunity ID with opp_ prefix."""
        return generate_opportunity_id()

    register_get_current_time(agent)


def _in_price_range(price: int, min_p: int, max_p: int) -> bool:
    """Return True only when price is non-zero and within [min_p, max_p]."""
    return price != 0 and min_p <= price <= max_p


def _spread_ok(bid: int, ask: int, max_spread: int) -> bool:
    """Return True only when there is a real resting bid and spread is within limit."""
    return bid > 0 and (ask - bid) <= max_spread


async def _fetch_event_metadata(
    client: KalshiClient,
    event_tickers: list[str],
) -> dict[str, tuple[str, str]]:
    """Fetch title and category for each event ticker in parallel."""
    results = await asyncio.gather(
        *[client.get_event(et) for et in event_tickers],
        return_exceptions=True,
    )
    failed = [et for et, res in zip(event_tickers, results) if isinstance(res, Exception)]
    if failed:
        logger.warning("Failed to fetch event metadata for %d tickers: %s", len(failed), failed[:5])
    return {
        et: (
            (res.get("title") or "", res.get("category") or "")
            if isinstance(res, dict)
            else ("", "")
        )
        for et, res in zip(event_tickers, results)
    }


def _to_market_dict(
    m: "Market",
    event_meta: dict[str, tuple[str, str]],
) -> dict:
    """Convert a Market model + event metadata into a dict for Scout."""
    title, category = event_meta.get(m.event_ticker, ("", ""))
    return {
        "ticker": m.ticker,
        "event_ticker": m.event_ticker,
        "title": m.title,
        "subtitle": m.subtitle,
        "yes_bid": m.yes_bid,
        "yes_ask": m.yes_ask,
        "no_bid": m.no_bid,
        "no_ask": m.no_ask,
        "spread_cents": (m.yes_ask - m.yes_bid) if m.yes_ask > 0 and m.yes_bid > 0 else None,
        "volume": m.volume,
        "open_interest": m.open_interest,
        "close_time": m.close_time.isoformat() if m.close_time else None,
        "category": category,
        "event_title": title,
    }


async def _prefetch_markets_for_scan(
    client: KalshiClient,
    settings: Settings,
    seen_tickers: set[str] | None = None,
) -> list[dict]:
    """Fetch and pre-filter market dataset before Scout agent run."""
    cfg = settings.scout
    min_p, max_p = cfg.min_price, cfg.max_price
    max_spread = cfg.max_spread_cents

    markets = await client.get_markets_closing_in_range(
        min_hours=cfg.min_close_hours,
        max_hours=cfg.max_close_hours,
        limit=cfg.market_fetch_limit,
        status="open",
    )
    logger.info("Prefetch: %d markets in %d-%dh window", len(markets), cfg.min_close_hours, cfg.max_close_hours)

    if seen_tickers:
        markets = [m for m in markets if m.ticker not in seen_tickers]

    markets = [m for m in markets if m.volume >= cfg.min_volume]

    markets = [
        m for m in markets
        if (
            _in_price_range(m.yes_ask, min_p, max_p)
            and _spread_ok(m.yes_bid, m.yes_ask, max_spread)
        ) or (
            _in_price_range(m.no_ask, min_p, max_p)
            and _spread_ok(m.no_bid, m.no_ask, max_spread)
        )
    ]

    logger.info("Prefetch: %d markets after price/volume/spread filters", len(markets))

    unique_event_tickers = list({m.event_ticker for m in markets if m.event_ticker})
    event_meta = await _fetch_event_metadata(client, unique_event_tickers)

    market_dicts = [_to_market_dict(m, event_meta) for m in markets]

    pre_filter_count = len(market_dicts)
    market_dicts = [md for md in market_dicts if passes_filter(md)]
    logger.info(
        "Prefetch: %d -> %d markets after data-driven filter",
        pre_filter_count,
        len(market_dicts),
    )

    return market_dicts


def _build_market_context_prompt(prefetched_markets: list[dict]) -> str:
    """Build prompt context containing pre-fetched market dataset."""
    market_count = len(prefetched_markets)
    serialized_markets = json.dumps(prefetched_markets, ensure_ascii=True, separators=(",", ":"))
    return (
        f"\n\nPREFETCHED_MARKETS_COUNT: {market_count}\n"
        "\n\nPREFETCHED_MARKETS_JSON:\n"
        f"{serialized_markets}\n\n"
        "Use this dataset as the complete market universe for this scan. "
        "Set markets_scanned exactly to PREFETCHED_MARKETS_COUNT (the number of objects in PREFETCHED_MARKETS_JSON). "
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

    # Paper mode is stateless: skip seen_tickers so every run rediscovers from scratch
    seen_tickers = [] if settings.trading.paper_mode else get_seen_tickers()

    with logfire.span("scout scan"):
        kalshi_config = KalshiConfig()
        async with KalshiClient(config=kalshi_config) as client:
            with logfire.span("prefetch markets"):
                prefetched_markets = await _prefetch_markets_for_scan(
                    client,
                    settings,
                    seen_tickers=set(seen_tickers),
                )
                logfire.info("Markets prefetched", count=len(prefetched_markets))

            deps = ScoutDependencies(settings=settings, prefetched_markets=prefetched_markets)

            with logfire.span("scout agent run", markets=len(prefetched_markets)):
                agent = get_scout_agent(settings)
                scout_cfg = settings.scout
                memory_context = build_scout_context()
                prompt = (
                    f"Scan the pre-filtered Kalshi markets for the single best "
                    f"near-decided opportunity at {scout_cfg.min_price}-{scout_cfg.max_price}% "
                    f"probability. All markets have already passed data-driven category "
                    f"filters—focus on confirming outcomes via web research and selecting "
                    f"the lowest reversal-risk candidate. If no market passes the Risk "
                    f"Assessment Checklist, return 0 opportunities."
                    f"{memory_context}"
                    f"{_build_market_context_prompt(prefetched_markets)}"
                )
                result = await agent.run(prompt, deps=deps)

            output: ScoutOutput = result.output

            # Strip citation tokens leaked by the OpenAI Responses API structured output
            for opp in output.opportunities:
                opp.rationale = _strip_cite_tokens(opp.rationale)
                opp.resolution_source = _strip_cite_tokens(opp.resolution_source)
                opp.evidence_bullets = [_strip_cite_tokens(b) for b in opp.evidence_bullets]
                opp.remaining_risks = [_strip_cite_tokens(r) for r in opp.remaining_risks]

            added_count = 0
            for opp in output.opportunities:
                try:
                    save_opportunity(opp, paper=settings.trading.paper_mode)
                    if not settings.trading.paper_mode:
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
