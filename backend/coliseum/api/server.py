"""FastAPI dashboard server for the Coliseum trading system."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from coliseum.config import get_settings
from coliseum.daemon import ColiseumDaemon
from coliseum.observability import initialize_logfire
from coliseum.pipeline import run_pipeline
from coliseum.api.parsing import parse_opportunity_sections
from coliseum.services.supabase.repositories.portfolio import load_state_from_db
from coliseum.services.supabase.repositories.opportunities import (
    load_opportunity_from_db,
    get_opportunity_body_from_db,
    list_opportunities_from_db,
)
from coliseum.services.supabase.repositories.portfolio_snapshots import (
    list_portfolio_snapshots_from_db,
)
from coliseum.services.supabase.repositories.trades import (
    list_trades_from_db,
    list_trade_closes_from_db,
)
from coliseum.services.supabase.repositories.run_cycles import list_run_cycles_from_db
from coliseum.domain.portfolio import Position

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
        await asyncio.wait_for(task, timeout=120.0)
    except asyncio.TimeoutError:
        logger.warning("Daemon did not stop within 120s timeout — forcing exit")


# ---------------------------------------------------------------------------
# Shared router
# ---------------------------------------------------------------------------

router = APIRouter()

_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "https://coliseum.manitmishra.com",
]


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



def _get_start_date() -> date | None:
    """Read dashboard_display.start_date from config, or None if unset."""
    settings = get_settings()
    raw = settings.dashboard_display.start_date
    if raw is None:
        return None
    return date.fromisoformat(raw)


# ---------------------------------------------------------------------------
# Portfolio enrichment
# ---------------------------------------------------------------------------


class EnrichedPosition(BaseModel):
    """Position enriched with unrealized P&L computed from DB-stored prices."""

    id: str
    market_ticker: str
    side: str
    contracts: int
    average_entry: float
    current_price: float
    unrealized_pnl: float
    pct_change: float
    opportunity_id: str | None


def _enrich_position(pos: Position) -> EnrichedPosition:
    """Compute unrealized P&L for a position. Returns a new object — no mutation."""
    pnl = (pos.current_price - pos.average_entry) * pos.contracts
    cost = pos.average_entry * pos.contracts
    pct = (pnl / cost * 100) if cost > 0 else 0.0
    return EnrichedPosition(
        id=pos.id,
        market_ticker=pos.market_ticker,
        side=pos.side,
        contracts=pos.contracts,
        average_entry=pos.average_entry,
        current_price=pos.current_price,
        unrealized_pnl=round(pnl, 4),
        pct_change=round(pct, 2),
        opportunity_id=pos.opportunity_id,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/api/config")
async def get_config():
    """Return the full config.yaml contents."""
    return _load_yaml(get_settings().config_file_path)


@router.get("/api/state")
async def get_state():
    """Return portfolio state with P&L-enriched positions from the DB.

    Prices reflect the last Guardian reconciliation cycle (typically every 2 minutes).
    """
    state = await load_state_from_db()
    enriched = [_enrich_position(p) for p in state.open_positions]
    return {
        "portfolio": {
            "cash_balance": state.portfolio.cash_balance,
            "positions_value": state.portfolio.positions_value,
            "total_value": state.portfolio.total_value,
        },
        "open_positions": [e.model_dump() for e in enriched],
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
    """Return portfolio chart data from portfolio snapshots and trade closes."""
    start_date = _get_start_date()
    snapshots = await list_portfolio_snapshots_from_db(start_date=start_date)
    cycles = await list_run_cycles_from_db(start_date=start_date)

    legacy_series = [
        {
            "snapshot_at": c["cycle_at"],
            "total_value": c["total_value"],
            "cash_balance": c["cash_balance"],
            "positions_value": c["positions_value"],
        }
        for c in cycles
    ]

    if snapshots:
        first_snapshot_at = snapshots[0]["snapshot_at"]
        snapshots = [
            s for s in legacy_series
            if s["snapshot_at"] < first_snapshot_at
        ] + snapshots
    else:
        # Temporary fallback while snapshot history is being populated.
        snapshots = legacy_series

    if not snapshots:
        try:
            state = await load_state_from_db()
            current_nav = round(float(state.portfolio.total_value), 2)
        except Exception:
            current_nav = 0.0
        return {
            "series": [],
            "stats": {
                "current_nav": current_nav,
                "initial_nav": current_nav,
                "total_pnl": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "best_day": 0.0,
                "worst_day": 0.0,
                "realized_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "avg_trade": 0.0,
            },
        }

    initial_nav = snapshots[0]["total_value"]
    current_nav = snapshots[-1]["total_value"]

    series: list[dict[str, Any]] = [
        {
            "timestamp": s["snapshot_at"],
            "nav": round(s["total_value"], 2),
            "cash": round(s["cash_balance"], 2),
            "positions_value": round(s["positions_value"], 2),
        }
        for s in snapshots
    ]

    closes = await list_trade_closes_from_db(start_date=start_date)
    close_pnls = [c["pnl"] for c in closes]
    total_trades = len(close_pnls)
    winning_trades = sum(1 for pnl in close_pnls if pnl >= 0)
    losing_trades = total_trades - winning_trades
    realized_pnl = sum(close_pnls)

    daily_pnl_map: dict[str, float] = {}
    for c in closes:
        day = c["closed_at"][:10]
        daily_pnl_map[day] = daily_pnl_map.get(day, 0.0) + c["pnl"]
    daily_pnls = list(daily_pnl_map.values())

    stats = {
        "current_nav": round(current_nav, 2),
        "initial_nav": round(initial_nav, 2),
        "total_pnl": round(current_nav - initial_nav, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0.0,
        "best_day": round(max(daily_pnls), 2) if daily_pnls else 0.0,
        "worst_day": round(min(daily_pnls), 2) if daily_pnls else 0.0,
        "realized_pnl": round(realized_pnl, 2),
        "best_trade": round(max(close_pnls), 2) if close_pnls else 0.0,
        "worst_trade": round(min(close_pnls), 2) if close_pnls else 0.0,
        "avg_trade": round(realized_pnl / total_trades, 2) if total_trades > 0 else 0.0,
    }

    return {"series": series, "stats": stats}


# ---------------------------------------------------------------------------
# Pipeline trigger
# ---------------------------------------------------------------------------


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


# app        → coliseum api     (dashboard only, no trading)
# daemon_app → coliseum daemon  (dashboard + trading daemon)
# Must be instantiated AFTER all @router routes are defined.
app = _make_app(_api_lifespan)
daemon_app = _make_app(_daemon_lifespan)
