"""FastAPI dashboard server for the Coliseum trading system."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from coliseum.api.chart_export import (
    ChartExportBusyError,
    ChartExportDependencyError,
    ChartExportNoDataError,
    ChartExportService,
    ChartExportTimeoutError,
    ExportFormat,
    ExportQuality,
)

from coliseum.api.cache import get_or_compute, invalidate_all
from coliseum.api.parsing import parse_opportunity_sections
from coliseum.config import get_settings
from coliseum.daemon import ColiseumDaemon
from coliseum.domain.portfolio import Position
from coliseum.observability import initialize_logfire
from coliseum.pipeline import run_pipeline
from coliseum.services.supabase.repositories.opportunities import (
    get_opportunity_body_from_db,
    list_opportunities_from_db,
    load_opportunity_from_db,
)
from coliseum.services.supabase.repositories.portfolio import load_state_from_db
from coliseum.services.supabase.repositories.portfolio_snapshots import (
    list_portfolio_snapshots_from_db,
)
from coliseum.services.supabase.repositories.trades import (
    list_trade_closes_from_db,
    list_trades_from_db,
)

logger = logging.getLogger(__name__)

_chart_export_service = ChartExportService()

_DAEMON_OFFLINE: dict[str, Any] = {
    "available": False,
    "running": False,
    "paused": False,
    "uptime_seconds": 0,
    "cycles_completed": 0,
    "consecutive_failures": 0,
    "last_cycle": None,
}

_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "https://coliseum.manitmishra.com",
]


# ---------------------------------------------------------------------------
# Lifespan
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


def _cache_ttl() -> int:
    """Read the dashboard cache TTL from config."""
    return get_settings().dashboard_display.cache_ttl_seconds


def _start_date() -> date | None:
    """Read dashboard_display.start_date from config, or None if unset."""
    raw = get_settings().dashboard_display.start_date
    if raw is None:
        return None
    return date.fromisoformat(raw)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict if missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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
    """Compute unrealized P&L for a position."""
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
# Data builders (called by cache on miss)
# ---------------------------------------------------------------------------


async def _build_config() -> dict[str, Any]:
    return _load_yaml(get_settings().config_file_path)


async def _build_state() -> dict[str, Any]:
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


async def _build_opportunities() -> list[dict[str, Any]]:
    opps = await list_opportunities_from_db(start_date=_start_date())
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


async def _build_ledger(limit: int) -> list[dict[str, Any]]:
    return await list_trades_from_db(start_date=_start_date(), limit=limit)


async def _build_chart() -> dict[str, Any]:
    start = _start_date()
    snapshots = await list_portfolio_snapshots_from_db(start_date=start)

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
                "avg_day": 0.0,
                "realized_pnl": 0.0,
            },
        }

    initial_nav = snapshots[0]["total_value"]
    current_nav = snapshots[-1]["total_value"]

    series = [
        {
            "timestamp": s["snapshot_at"],
            "nav": round(s["total_value"], 2),
            "cash": round(s["cash_balance"], 2),
            "positions_value": round(s["positions_value"], 2),
        }
        for s in snapshots
    ]

    closes = await list_trade_closes_from_db(start_date=start)
    close_pnls = [c["pnl"] for c in closes]
    total_trades = len(close_pnls)
    winning_trades = sum(1 for pnl in close_pnls if pnl >= 0)
    realized_pnl = sum(close_pnls)

    daily_nav_map: dict[str, dict[str, float]] = {}
    for s in snapshots:
        day = s["snapshot_at"][:10]
        nav = float(s["total_value"])
        bucket = daily_nav_map.get(day)
        if bucket is None:
            daily_nav_map[day] = {"first": nav, "last": nav}
        else:
            bucket["last"] = nav

    daily_pnls = [v["last"] - v["first"] for v in daily_nav_map.values()]

    return {
        "series": series,
        "stats": {
            "current_nav": round(current_nav, 2),
            "initial_nav": round(initial_nav, 2),
            "total_pnl": round(current_nav - initial_nav, 2),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0.0,
            "best_day": round(max(daily_pnls), 2) if daily_pnls else 0.0,
            "worst_day": round(min(daily_pnls), 2) if daily_pnls else 0.0,
            "avg_day": round(sum(daily_pnls) / len(daily_pnls), 2) if daily_pnls else 0.0,
            "realized_pnl": round(realized_pnl, 2),
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/api/config")
async def get_config():
    """Return the full config.yaml contents."""
    return await get_or_compute("config", _cache_ttl(), _build_config)


@router.get("/api/state")
async def get_state():
    """Return portfolio state with P&L-enriched positions."""
    return await get_or_compute("state", _cache_ttl(), _build_state)


@router.get("/api/opportunities")
async def list_opportunities():
    """List all opportunities with frontmatter summary."""
    return await get_or_compute("opportunities", _cache_ttl(), _build_opportunities)


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
    ttl = _cache_ttl()
    return await get_or_compute(
        f"ledger:{limit}", ttl, lambda: _build_ledger(limit)
    )


@router.get("/api/chart")
async def get_chart_data():
    """Return portfolio chart data from snapshots and trade closes."""
    return await get_or_compute("chart", _cache_ttl(), _build_chart)


# ---------------------------------------------------------------------------
# Chart export
# ---------------------------------------------------------------------------


@router.get("/api/chart/export")
async def export_chart(
    format: ExportFormat = Query("mp4"),
    quality: ExportQuality = Query("balanced"),
):
    """Render and return a portfolio NAV animation as a downloadable MP4."""
    chart_data = await get_or_compute("chart", _cache_ttl(), _build_chart)
    cycles = [
        {"total_value": pt["nav"], "cycle_at": pt["timestamp"]}
        for pt in chart_data.get("series", [])
    ]

    try:
        result = await asyncio.to_thread(
            _chart_export_service.export, cycles, format, quality
        )
    except ChartExportNoDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ChartExportBusyError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except ChartExportDependencyError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except ChartExportTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))

    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Quality-Used": result.quality_used,
            "X-Cache-Hit": str(result.cache_hit).lower(),
        },
    )


# ---------------------------------------------------------------------------
# Pipeline trigger
# ---------------------------------------------------------------------------


def _pipeline_running(request: Request) -> bool:
    return bool(getattr(request.app.state, "pipeline_running", False))


async def _execute_pipeline(request: Request) -> None:
    """Run the pipeline, then invalidate the cache so fresh data is served."""
    try:
        await run_pipeline(get_settings())
    except Exception:
        logger.exception("Pipeline run failed")
    finally:
        invalidate_all()
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
    """Return live daemon state, or offline sentinel when not running."""
    daemon = getattr(request.app.state, "daemon", None)
    if daemon is None:
        return _DAEMON_OFFLINE
    return {"available": True, **daemon.status_summary()}


# ---------------------------------------------------------------------------
# App instances (must be after all @router routes)
# ---------------------------------------------------------------------------

app = _make_app(_api_lifespan)
daemon_app = _make_app(_daemon_lifespan)
