"""FastAPI dashboard server for the Coliseum trading system."""

import asyncio
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

import logfire
import yaml
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from coliseum.config import get_settings
from coliseum.daemon import ColiseumDaemon
from coliseum.observability import initialize_logfire
from coliseum.pipeline import run_pipeline
from coliseum.services.kalshi.client import KalshiClient
from coliseum.api.parsing import parse_opportunity_sections
from coliseum.services.supabase.repositories.portfolio import load_state_from_db
from coliseum.services.supabase.repositories.opportunities import (
    load_opportunity_from_db,
    get_opportunity_body_from_db,
    list_opportunities_from_db,
)
from coliseum.services.supabase.repositories.trades import (
    list_trades_from_db,
    list_trade_closes_from_db,
)
from coliseum.storage.state import Position
from coliseum.storage.sync import resolve_market_price

logger = logging.getLogger(__name__)
_DAEMON_OFFLINE: dict[str, Any] = {
    "available": False,
    "running": False,
    "paused": False,
    "uptime_seconds": 0,
    "cycles_completed": 0,
    "consecutive_failures": 0,
    "last_cycle": None,
}


# ---------------------------------------------------------------------------
# Lifespan functions (one per server mode)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _api_lifespan(app: FastAPI):
    """Lifespan for the API-only server (no daemon)."""
    app.state.daemon = None
    app.state.pipeline_task = None
    app.state.pipeline_running = False
    yield


@asynccontextmanager
async def _daemon_lifespan(app: FastAPI):
    """Lifespan for the daemon+API server."""
    settings = get_settings()
    try:
        initialize_logfire(settings)
    except Exception as e:
        logger.warning("Failed to initialize Logfire in lifespan: %s", e)
    daemon = ColiseumDaemon(settings)
    task = asyncio.create_task(daemon.start(install_signal_handlers=False))
    app.state.daemon = daemon
    app.state.pipeline_task = None
    app.state.pipeline_running = False
    logger.info("Daemon started as background task alongside API server")
    yield
    daemon._shutdown_event.set()
    try:
        await asyncio.wait_for(task, timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Daemon did not stop within 10s timeout")


# ---------------------------------------------------------------------------
# Shared router (all API routes live here)
# ---------------------------------------------------------------------------

router = APIRouter()

_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]


def _make_app(lifespan) -> FastAPI:
    """Construct a FastAPI instance with shared middleware and routes."""
    the_app = FastAPI(
        title="Coliseum Dashboard API",
        version="0.1.0",
        lifespan=lifespan,
    )
    the_app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    the_app.include_router(router)
    return the_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict if missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_data_dir() -> Path:
    """Return the configured data directory used by CLI and storage helpers."""
    return get_settings().data_dir


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/api/config")
async def get_config():
    """Return the full config.yaml contents."""
    return _load_yaml(_get_data_dir() / "config.yaml")


@router.get("/api/state")
async def get_state():
    """Return current portfolio state from DB."""
    state = await load_state_from_db()
    return {
        "last_updated": None,
        "portfolio": {
            "cash_balance": state.portfolio.cash_balance,
            "positions_value": state.portfolio.positions_value,
            "total_value": state.portfolio.total_value,
        },
        "open_positions": [p.model_dump(mode="json") for p in state.open_positions],
    }


@router.get("/api/opportunities")
async def list_opportunities():
    """List all opportunities with frontmatter summary."""
    start_date = _get_start_date()
    opps = await list_opportunities_from_db(start_date=start_date)
    return [
        {
            "id": opp.id,
            "event_ticker": opp.event_ticker,
            "market_ticker": opp.market_ticker,
            "title": opp.market_title,
            "subtitle": opp.subtitle,
            "yes_price": opp.yes_price,
            "no_price": opp.no_price,
            "close_time": str(opp.close_time),
            "discovered_at": str(opp.discovered_at),
            "status": opp.status,
            "event_title": opp.event_title,
            "action": opp.action,
            "date_folder": str(opp.discovered_at)[:10],
        }
        for opp in opps
    ]


@router.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get full opportunity detail including markdown body."""
    try:
        opp = await load_opportunity_from_db(opportunity_id)
    except ValueError:
        raise HTTPException(
            status_code=404, detail=f"Opportunity {opportunity_id} not found"
        )
    markdown_body = await get_opportunity_body_from_db(opportunity_id)
    return {
        "summary": {
            "id": opp.id,
            "event_ticker": opp.event_ticker,
            "event_title": opp.event_title,
            "market_ticker": opp.market_ticker,
            "title": opp.market_title,
            "subtitle": opp.subtitle,
            "yes_price": opp.yes_price,
            "no_price": opp.no_price,
            "close_time": str(opp.close_time),
            "discovered_at": str(opp.discovered_at),
            "status": opp.status,
            "action": opp.action,
            "date_folder": str(opp.discovered_at)[:10],
        },
        "markdown_body": markdown_body,
        "raw_frontmatter": opp.model_dump(mode="json"),
        "parsed_sections": parse_opportunity_sections(opp, markdown_body),
    }


@router.get("/api/stream/portfolio")
async def stream_portfolio(request: Request) -> EventSourceResponse:
    """SSE endpoint: pushes enriched portfolio state with live prices every 2 seconds."""

    async def _generator():
        async with _make_kalshi_client() as client:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    state = await load_state_from_db()
                    positions = state.open_positions
                    if positions:
                        with logfire.suppress_instrumentation():
                            prices = await _fetch_prices_for_positions(client, positions)
                        enriched = [
                            _enrich_position(p, prices.get(p.market_ticker, p.current_price))
                            for p in positions
                        ]
                    else:
                        enriched = []
                    live_positions_value = sum(
                        e.current_price * p.contracts
                        for e, p in zip(enriched, positions)
                    )
                    payload = {
                        "open_positions": [e.model_dump() for e in enriched],
                        "portfolio": {
                            "cash_balance": state.portfolio.cash_balance,
                            "positions_value": live_positions_value,
                            "total_value": state.portfolio.cash_balance + live_positions_value,
                        },
                        "timestamp": time.time(),
                    }
                    yield {"data": json.dumps(payload)}
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning("SSE portfolio stream error: %s", e)
                    yield {"data": json.dumps({"error": str(e)})}
                await asyncio.sleep(2.0)

    return EventSourceResponse(_generator())


# ---------------------------------------------------------------------------
# Trade ledger
# ---------------------------------------------------------------------------


def _get_start_date() -> date | None:
    """Read dashboard_display.start_date from config, or None if unset."""
    settings = get_settings()
    raw = settings.dashboard_display.start_date
    if raw is None:
        return None
    return date.fromisoformat(raw)


@router.get("/api/ledger")
async def get_ledger(limit: int = 100):
    """Return merged buy+close trade entries sorted newest-first."""
    start_date = _get_start_date()
    return await list_trades_from_db(start_date=start_date, limit=limit)


# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------


@router.get("/api/chart")
async def get_chart_data():
    """Return portfolio chart data: daily P&L, cumulative NAV, and stats."""
    start_date = _get_start_date()
    raw_entries = await list_trade_closes_from_db(start_date=start_date)

    daily_map: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"pnl": 0.0, "trades": 0, "wins": 0, "losses": 0}
    )
    for entry in raw_entries:
        day = entry["closed_at"][:10]
        pnl = entry["pnl"]
        daily_map[day]["pnl"] += pnl
        daily_map[day]["trades"] += 1
        if pnl >= 0:
            daily_map[day]["wins"] += 1
        else:
            daily_map[day]["losses"] += 1

    try:
        state = await load_state_from_db()
        current_nav = float(state.portfolio.total_value)
    except Exception:
        current_nav = 1000.0

    total_pnl = sum(e["pnl"] for e in raw_entries)
    initial_nav = current_nav - total_pnl

    sorted_dates = sorted(daily_map.keys())
    cumulative = 0.0
    daily: list[dict[str, Any]] = []
    for day in sorted_dates:
        d = daily_map[day]
        cumulative += d["pnl"]
        daily.append(
            {
                "date": day,
                "pnl": round(d["pnl"], 4),
                "cumulative_pnl": round(cumulative, 4),
                "nav": round(initial_nav + cumulative, 4),
                "trades": d["trades"],
                "wins": d["wins"],
                "losses": d["losses"],
            }
        )

    total_trades = sum(d["trades"] for d in daily)
    winning_trades = sum(d["wins"] for d in daily)
    losing_trades = sum(d["losses"] for d in daily)
    daily_pnls = [d["pnl"] for d in daily]

    if total_trades > 0:
        win_rate = round(winning_trades / total_trades, 4)
    else:
        win_rate = 0.0

    if daily_pnls:
        best_day = round(max(daily_pnls), 4)
    else:
        best_day = 0.0

    if daily_pnls:
        worst_day = round(min(daily_pnls), 4)
    else:
        worst_day = 0.0

    stats = {
        "total_pnl": round(total_pnl, 4),
        "win_rate": win_rate,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "best_day": best_day,
        "worst_day": worst_day,
        "current_nav": round(current_nav, 4),
        "initial_nav": round(initial_nav, 4),
    }

    return {"daily": daily, "stats": stats}


# ---------------------------------------------------------------------------
# Pipeline trigger
# ---------------------------------------------------------------------------

# In-memory price cache for SSE stream: ticker -> (price, fetched_at_epoch)
_price_cache: dict[str, tuple[float, float]] = {}
_price_cache_lock = asyncio.Lock()
# TTL exceeds the 2s poll interval so concurrent SSE clients share cached values
_PRICE_CACHE_TTL = 10.0


class EnrichedPosition(BaseModel):
    """Position view model enriched with live price and unrealized P&L."""

    id: str
    market_ticker: str
    side: str
    contracts: int
    average_entry: float
    current_price: float
    unrealized_pnl: float
    pct_change: float
    opportunity_id: str | None


def _make_kalshi_client() -> KalshiClient:
    """Build an authenticated KalshiClient from current settings."""
    settings = get_settings()
    return KalshiClient(
        api_key=settings.kalshi_api_key,
        private_key_pem=settings.get_rsa_private_key(),
    )


def _enrich_position(pos: Position, current_price: float) -> EnrichedPosition:
    """Compute unrealized P&L for an open position. Returns new object, no mutation."""
    pnl = (current_price - pos.average_entry) * pos.contracts
    cost = pos.average_entry * pos.contracts
    if cost > 0:
        pct = pnl / cost * 100
    else:
        pct = 0.0
    return EnrichedPosition(
        id=pos.id,
        market_ticker=pos.market_ticker,
        side=pos.side,
        contracts=pos.contracts,
        average_entry=pos.average_entry,
        current_price=current_price,
        unrealized_pnl=round(pnl, 4),
        pct_change=round(pct, 2),
        opportunity_id=pos.opportunity_id,
    )


async def _fetch_prices_for_positions(
    client: KalshiClient,
    positions: list[Position],
) -> dict[str, float]:
    """Fetch current bid prices for open positions, with TTL-based in-memory cache.

    Lock is held for the full operation so concurrent SSE clients share a single
    Kalshi fetch rather than firing duplicate requests.
    """
    async with _price_cache_lock:
        now = time.time()
        stale_tickers = {
            p.market_ticker for p in positions
            if p.market_ticker not in _price_cache
            or now - _price_cache[p.market_ticker][1] > _PRICE_CACHE_TTL
        }
        stale = [p for p in positions if p.market_ticker in stale_tickers]
        result: dict[str, float] = {
            p.market_ticker: _price_cache[p.market_ticker][0]
            for p in positions
            if p.market_ticker not in stale_tickers
        }
        if not stale:
            return result
        markets = await asyncio.gather(
            *[client.get_market(p.market_ticker) for p in stale],
            return_exceptions=True,
        )
        fetch_time = time.time()
        for p, market in zip(stale, markets):
            if isinstance(market, Exception):
                result[p.market_ticker] = p.current_price
                continue
            price = resolve_market_price(market, p.side) or p.current_price
            _price_cache[p.market_ticker] = (price, fetch_time)
            result[p.market_ticker] = price
        return result


def _pipeline_running(request: Request) -> bool:
    """Return current in-process pipeline status for this app instance."""
    return bool(getattr(request.app.state, "pipeline_running", False))


async def _execute_pipeline(request: Request) -> None:
    """Wrapper that flips the running flag on completion."""
    try:
        settings = get_settings()
        await run_pipeline(settings)
    except Exception:
        logger.exception("Pipeline run failed")
    finally:
        request.app.state.pipeline_running = False
        request.app.state.pipeline_task = None


@router.post("/api/pipeline/run", status_code=202)
async def trigger_pipeline(request: Request):
    """Kick off a full pipeline cycle. Returns 409 if one is already running."""
    if _pipeline_running(request):
        raise HTTPException(status_code=409, detail="Pipeline already running")

    request.app.state.pipeline_running = True
    request.app.state.pipeline_task = asyncio.create_task(_execute_pipeline(request))
    return {"status": "started"}


@router.get("/api/pipeline/status")
async def pipeline_status(request: Request):
    """Check whether a pipeline cycle is currently in progress."""
    return {"running": _pipeline_running(request)}


@router.get("/api/daemon/status")
async def daemon_status(request: Request):
    """Return live daemon state, or offline sentinel when daemon is not running."""
    daemon = getattr(request.app.state, "daemon", None)
    if daemon is None:
        return _DAEMON_OFFLINE
    return {"available": True, **daemon.status_summary()}


# app      → coliseum api     (dashboard only, no trading)
# daemon_app → coliseum daemon (dashboard + trading daemon)
# Must be instantiated AFTER all @router routes are defined so include_router
# picks them up.
app = _make_app(_api_lifespan)
daemon_app = _make_app(_daemon_lifespan)
