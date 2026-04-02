"""Scout Agent: Market discovery and opportunity filtering."""

import asyncio
import json
import logging

import logfire
from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import create_agent
from coliseum.agents.shared_tools import register_get_current_time, _strip_cite_tokens
from coliseum.config import Settings, get_settings
from coliseum.memory.context import build_scout_context
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.services.kalshi.models import Market
from coliseum.services.supabase.repositories.opportunities import save_opportunity_to_db
from coliseum.services.supabase.repositories.seen_tickers import (
    add_seen_ticker_to_db,
    get_seen_tickers_from_db,
)
from coliseum.storage.files import save_opportunity, generate_opportunity_id
from coliseum.storage.state import add_seen_ticker

from .filters import passes_filter
from .models import ScoutDependencies, ScoutOutput
from .prompts import build_scout_prompt
from .researcher import get_web_researcher

logger = logging.getLogger(__name__)


def _create_scout_agent(prompt: str) -> Agent[ScoutDependencies, ScoutOutput]:
    """Create the Scout agent with the provided system prompt."""
    return create_agent(
        prompt=prompt,
        output_type=ScoutOutput,
        deps_type=ScoutDependencies,
        reasoning_effort="medium",
        prepend_mechanics=False,
    )


def _register_research_tool(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register the web research delegation tool on the Scout agent."""

    @agent.tool
    async def research_market(ctx: RunContext[ScoutDependencies], query: str) -> str:
        """Search the web for a specific query and return a comprehensive research synthesis."""
        researcher = get_web_researcher()
        result = await researcher.run(query, usage=ctx.usage)
        return result.output


def _register_tools(agent: Agent[ScoutDependencies, ScoutOutput]) -> None:
    """Register tools with the Scout agent."""

    @agent.tool
    def generate_opportunity_id_tool(ctx: RunContext[ScoutDependencies]) -> str:
        return generate_opportunity_id()

    register_get_current_time(agent)
    _register_research_tool(agent)


def _side_is_tradeable(
    bid_cents: int,
    ask_cents: int,
    min_price_cents: int,
    max_price_cents: int,
    max_spread_cents: int,
) -> bool:
    """Return True when a side has a real bid, valid price, and acceptable spread."""
    if ask_cents == 0 or bid_cents <= 0:
        return False
    if not min_price_cents <= ask_cents <= max_price_cents:
        return False
    return (ask_cents - bid_cents) <= max_spread_cents


def _entry_view(
    market: Market,
    min_price_cents: int,
    max_price_cents: int,
    max_spread_cents: int,
) -> dict | None:
    """Return the actionable side for Scout, or None if neither side qualifies."""
    if _side_is_tradeable(
        market.yes_bid,
        market.yes_ask,
        min_price_cents,
        max_price_cents,
        max_spread_cents,
    ):
        return {
            "entry_side": "yes",
            "entry_bid_cents": market.yes_bid,
            "entry_ask_cents": market.yes_ask,
            "entry_price_cents": market.yes_ask,
            "entry_spread_cents": market.yes_ask - market.yes_bid,
        }

    if _side_is_tradeable(
        market.no_bid,
        market.no_ask,
        min_price_cents,
        max_price_cents,
        max_spread_cents,
    ):
        return {
            "entry_side": "no",
            "entry_bid_cents": market.no_bid,
            "entry_ask_cents": market.no_ask,
            "entry_price_cents": market.no_ask,
            "entry_spread_cents": market.no_ask - market.no_bid,
        }

    return None


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


def _build_prefetched_market(
    market: Market,
    event_meta: dict[str, tuple[str, str]],
    entry_view: dict,
) -> dict:
    """Build the Scout candidate payload for one prefetched market."""
    event_title, category = event_meta.get(market.event_ticker, ("", ""))
    if market.close_time:
        close_time_iso = market.close_time.isoformat()
    else:
        close_time_iso = None
    return {
        "ticker": market.ticker,
        "event_ticker": market.event_ticker,
        "market_title": market.title,
        "subtitle": market.subtitle,
        "yes_bid": market.yes_bid,
        "yes_ask": market.yes_ask,
        "no_bid": market.no_bid,
        "no_ask": market.no_ask,
        "volume": market.volume,
        "open_interest": market.open_interest,
        "close_time": close_time_iso,
        "category": category,
        "event_title": event_title,
        **entry_view,
    }


async def _prefetch_markets_for_scan(
    client: KalshiClient,
    settings: Settings,
    seen_tickers: set[str] | None = None,
) -> list[dict]:
    """Fetch and pre-filter market dataset before Scout agent run."""
    cfg = settings.scout

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

    candidate_markets: list[tuple[Market, dict]] = []
    for market in markets:
        entry_view = _entry_view(
            market,
            min_price_cents=cfg.min_price,
            max_price_cents=cfg.max_price,
            max_spread_cents=cfg.max_spread_cents,
        )
        if entry_view is not None:
            candidate_markets.append((market, entry_view))

    logger.info("Prefetch: %d markets after baseline filters", len(candidate_markets))

    unique_event_tickers = list({market.event_ticker for market, _ in candidate_markets if market.event_ticker})
    event_meta = await _fetch_event_metadata(client, unique_event_tickers)

    prefetched_markets = []
    for market, entry_view in candidate_markets:
        _, category = event_meta.get(market.event_ticker, ("", ""))
        if not passes_filter(category, market.event_ticker, entry_view["entry_price_cents"]):
            continue
        prefetched_markets.append(_build_prefetched_market(market, event_meta, entry_view))

    logger.info(
        "Prefetch: %d -> %d markets after historical safety filter",
        len(candidate_markets),
        len(prefetched_markets),
    )

    return prefetched_markets


def _build_market_context_prompt(prefetched_markets: list[dict]) -> str:
    """Build prompt context containing pre-fetched market dataset."""
    market_count = len(prefetched_markets)
    serialized_markets = json.dumps(prefetched_markets, ensure_ascii=True, separators=(",", ":"))
    return (
        f"\n\nPREFETCHED_MARKETS_COUNT: {market_count}\n"
        "\n\nPREFETCHED_MARKETS_JSON:\n"
        f"{serialized_markets}\n\n"
        "Use this dataset as the complete market universe for this scan. "
        "Each object already includes the actionable entry side, entry pricing, and entry spread for Scout. "
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
    if settings.trading.paper_mode:
        seen_tickers = []
    else:
        seen_tickers = await get_seen_tickers_from_db()

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
                    f"Review the prefiltered Scout candidates and find the single best "
                    f"near-decided opportunity in the {scout_cfg.min_price}-{scout_cfg.max_price}% "
                    f"band. These markets already passed baseline liquidity checks and "
                    f"historical safety-bucket filtering. Use entry_side and entry_*_cents "
                    f"fields as the actionable trade context. Return 0 opportunities only "
                    f"if every candidate has a specific disqualifying factor."
                    f"{memory_context}"
                    f"{_build_market_context_prompt(prefetched_markets)}"
                )
                result = await agent.run(prompt, deps=deps)

            output: ScoutOutput = result.output

            # Strip citation tokens leaked by the OpenAI Responses API structured output
            cleaned_opps = [
                opp.model_copy(update={
                    "rationale": _strip_cite_tokens(opp.rationale),
                    "resolution_source": _strip_cite_tokens(opp.resolution_source),
                    "evidence_bullets": [_strip_cite_tokens(b) for b in opp.evidence_bullets],
                    "remaining_risks": [_strip_cite_tokens(r) for r in opp.remaining_risks],
                })
                for opp in output.opportunities
            ]

            added_count = 0
            for opp in cleaned_opps:
                try:
                    await save_opportunity_to_db(opp, paper=settings.trading.paper_mode)
                except Exception as e:
                    logfire.error("DB write failed for opportunity", opportunity_id=opp.id, error=str(e))

                try:
                    save_opportunity(opp, paper=settings.trading.paper_mode)
                    added_count += 1
                except Exception as e:
                    logfire.error("Local write failed for opportunity", opportunity_id=opp.id, error=str(e))
                    continue

                if not settings.trading.paper_mode:
                    try:
                        await add_seen_ticker_to_db(opp.market_ticker)
                    except Exception as e:
                        logfire.error("DB seen ticker write failed", ticker=opp.market_ticker, error=str(e))
                    add_seen_ticker(opp.market_ticker)

            logfire.info(
                "Scout scan complete",
                opportunities_found=output.opportunities_found,
                added=added_count,
            )

        return output
