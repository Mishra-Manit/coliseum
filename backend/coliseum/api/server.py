"""FastAPI dashboard server for the Coliseum trading system."""

import asyncio
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from coliseum.config import get_settings
from coliseum.daemon import ColiseumDaemon
from coliseum.pipeline import run_pipeline
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.files import (
    find_opportunity_file_by_id,
    get_opportunity_markdown_body,
    load_opportunity_from_file,
)
from coliseum.storage.state import Position, load_state
from coliseum.storage.sync import normalize_probability_price

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


# ---------------------------------------------------------------------------
# Lifespan functions (one per server mode)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _api_lifespan(app: FastAPI):
    """Lifespan for the API-only server (no daemon)."""
    app.state.daemon = None
    yield


@asynccontextmanager
async def _daemon_lifespan(app: FastAPI):
    """Lifespan for the daemon+API server."""
    settings = get_settings()
    try:
        from coliseum.observability import initialize_logfire
        initialize_logfire(settings)
    except Exception as e:
        logger.warning("Failed to initialize Logfire in lifespan: %s", e)
    daemon = ColiseumDaemon(settings)
    task = asyncio.create_task(daemon.start(install_signal_handlers=False))
    app.state.daemon = daemon
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


def _parse_opportunity(file_path: Path) -> dict[str, Any] | None:
    """Parse a markdown opportunity file into frontmatter + body."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()

        title = ""
        subtitle = ""
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
            elif stripped.startswith("**Outcome**:"):
                subtitle = stripped.split(":", 1)[1].strip()

        return {
            "frontmatter": frontmatter,
            "body": body,
            "title": title,
            "subtitle": subtitle,
            "date_folder": file_path.parent.name,
        }
    except Exception as e:
        logger.warning("Error parsing %s: %s", file_path, e)
        return None


def _get_all_opportunities() -> list[dict[str, Any]]:
    """Scan all opportunity markdown files, sorted by discovered_at descending."""
    opps_dir = DATA_DIR / "opportunities"
    if not opps_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for md_file in opps_dir.rglob("*.md"):
        parsed = _parse_opportunity(md_file)
        if parsed:
            results.append(parsed)

    results.sort(
        key=lambda o: o["frontmatter"].get("discovered_at", ""),
        reverse=True,
    )
    return results


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/api/config")
async def get_config():
    """Return the full config.yaml contents."""
    return _load_yaml(DATA_DIR / "config.yaml")


@router.get("/api/state")
async def get_state():
    """Return the full state.yaml contents."""
    return _load_yaml(DATA_DIR / "state.yaml")


@router.get("/api/opportunities")
async def list_opportunities():
    """List all opportunities with frontmatter summary."""
    results = []
    for opp in _get_all_opportunities():
        fm = opp["frontmatter"]
        results.append(
            {
                "id": fm.get("id", ""),
                "event_ticker": fm.get("event_ticker", ""),
                "market_ticker": fm.get("market_ticker", ""),
                "title": opp["title"],
                "subtitle": opp["subtitle"],
                "yes_price": fm.get("yes_price", 0.0),
                "no_price": fm.get("no_price", 0.0),
                "close_time": str(fm.get("close_time", "")),
                "discovered_at": str(fm.get("discovered_at", "")),
                "status": fm.get("status", "pending"),
                "action": fm.get("action"),
                "date_folder": opp["date_folder"],
            }
        )
    return results


@router.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get full opportunity detail including markdown body."""
    file_path = (
        find_opportunity_file_by_id(opportunity_id, paper=False)
        or find_opportunity_file_by_id(opportunity_id, paper=True)
    )
    if not file_path:
        raise HTTPException(
            status_code=404, detail=f"Opportunity {opportunity_id} not found"
        )
    opp = load_opportunity_from_file(file_path)
    return {
        "summary": {
            "id": opp.id,
            "event_ticker": opp.event_ticker,
            "market_ticker": opp.market_ticker,
            "title": opp.title,
            "subtitle": opp.subtitle,
            "yes_price": opp.yes_price,
            "no_price": opp.no_price,
            "close_time": str(opp.close_time),
            "discovered_at": str(opp.discovered_at),
            "status": opp.status,
            "action": opp.action,
            "date_folder": file_path.parent.name,
        },
        "markdown_body": get_opportunity_markdown_body(file_path),
        "raw_frontmatter": opp.model_dump(mode="json"),
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
                    state = load_state()
                    positions = state.open_positions
                    if positions:
                        prices = await _fetch_prices_for_positions(client, positions)
                        enriched = [
                            _enrich_position(p, prices.get(p.market_ticker, p.current_price))
                            for p in positions
                        ]
                    else:
                        enriched = []
                    payload = {
                        "open_positions": [e.model_dump() for e in enriched],
                        "portfolio": state.portfolio.model_dump(),
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read all JSON objects from a .jsonl file."""
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except Exception as e:
        logger.warning("Error reading %s: %s", path, e)
    return rows


@router.get("/api/ledger")
async def get_ledger(limit: int = 100):
    """Return merged buy+close trade entries sorted newest-first."""
    trades_dir = DATA_DIR / "trades"
    entries: list[dict[str, Any]] = []

    buy_dir = trades_dir / "buy"
    if buy_dir.exists():
        for f in sorted(buy_dir.glob("*.jsonl")):
            for row in _read_jsonl(f):
                entries.append(
                    {
                        "type": "buy",
                        "id": row.get("id", ""),
                        "market_ticker": row.get("market_ticker", ""),
                        "side": (row.get("side") or "").upper(),
                        "contracts": row.get("contracts", 0),
                        "price": row.get("price", 0.0),
                        "pnl": None,
                        "opportunity_id": row.get("opportunity_id"),
                        "paper": row.get("paper", False),
                        "timestamp": row.get("executed_at", ""),
                    }
                )

    close_dir = trades_dir / "close"
    if close_dir.exists():
        for f in sorted(close_dir.glob("*.jsonl")):
            for row in _read_jsonl(f):
                entries.append(
                    {
                        "type": "close",
                        "id": row.get("id", ""),
                        "market_ticker": row.get("market_ticker", ""),
                        "side": (row.get("side") or "").upper(),
                        "contracts": row.get("contracts", 0),
                        "price": row.get("exit_price", 0.0),
                        "pnl": row.get("pnl"),
                        "opportunity_id": row.get("opportunity_id"),
                        "paper": True,
                        "timestamp": row.get("closed_at", ""),
                    }
                )

    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries[:limit]


# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------


@router.get("/api/chart")
async def get_chart_data():
    """Return portfolio chart data: daily P&L, cumulative NAV, and stats."""
    close_dir = DATA_DIR / "trades" / "close"

    raw_entries: list[dict[str, Any]] = []
    if close_dir.exists():
        for f in sorted(close_dir.glob("*.jsonl")):
            for row in _read_jsonl(f):
                pnl = row.get("pnl")
                closed_at = row.get("closed_at", "")
                if pnl is not None and closed_at:
                    raw_entries.append({"pnl": float(pnl), "closed_at": str(closed_at)})

    raw_entries.sort(key=lambda e: e["closed_at"])

    daily_map: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"pnl": 0.0, "trades": 0, "wins": 0, "losses": 0}
    )
    for entry in raw_entries:
        date = entry["closed_at"][:10]
        pnl = entry["pnl"]
        daily_map[date]["pnl"] += pnl
        daily_map[date]["trades"] += 1
        if pnl >= 0:
            daily_map[date]["wins"] += 1
        else:
            daily_map[date]["losses"] += 1

    state = _load_yaml(DATA_DIR / "state.yaml")
    current_nav = float(state.get("portfolio", {}).get("total_value", 1000.0))

    total_pnl = sum(e["pnl"] for e in raw_entries)
    initial_nav = current_nav - total_pnl

    sorted_dates = sorted(daily_map.keys())
    cumulative = 0.0
    daily: list[dict[str, Any]] = []
    for date in sorted_dates:
        day = daily_map[date]
        cumulative += day["pnl"]
        daily.append(
            {
                "date": date,
                "pnl": round(day["pnl"], 4),
                "cumulative_pnl": round(cumulative, 4),
                "nav": round(initial_nav + cumulative, 4),
                "trades": day["trades"],
                "wins": day["wins"],
                "losses": day["losses"],
            }
        )

    total_trades = sum(d["trades"] for d in daily)
    winning_trades = sum(d["wins"] for d in daily)
    losing_trades = sum(d["losses"] for d in daily)
    daily_pnls = [d["pnl"] for d in daily]

    stats = {
        "total_pnl": round(total_pnl, 4),
        "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0.0,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "best_day": round(max(daily_pnls), 4) if daily_pnls else 0.0,
        "worst_day": round(min(daily_pnls), 4) if daily_pnls else 0.0,
        "current_nav": round(current_nav, 4),
        "initial_nav": round(initial_nav, 4),
    }

    return {"daily": daily, "stats": stats}


# ---------------------------------------------------------------------------
# Pipeline trigger
# ---------------------------------------------------------------------------

_pipeline_running = False
_pipeline_task: asyncio.Task[None] | None = None

# In-memory price cache for SSE stream: ticker -> (price, fetched_at_epoch)
_price_cache: dict[str, tuple[float, float]] = {}
_PRICE_CACHE_TTL = 3.0


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
    if pos.side == "YES":
        pnl = (current_price - pos.average_entry) * pos.contracts
    else:
        pnl = (pos.average_entry - current_price) * pos.contracts
    cost = pos.average_entry * pos.contracts
    pct = (pnl / cost * 100) if cost > 0 else 0.0
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
    """Fetch current bid prices for open positions, with TTL-based in-memory cache."""
    now = time.time()
    stale = [
        p for p in positions
        if p.market_ticker not in _price_cache
        or now - _price_cache[p.market_ticker][1] > _PRICE_CACHE_TTL
    ]
    result: dict[str, float] = {
        p.market_ticker: _price_cache[p.market_ticker][0]
        for p in positions
        if p.market_ticker not in [s.market_ticker for s in stale]
    }
    if not stale:
        return result
    markets = await asyncio.gather(
        *[client.get_market(p.market_ticker) for p in stale],
        return_exceptions=True,
    )
    for p, market in zip(stale, markets):
        if isinstance(market, Exception):
            result[p.market_ticker] = p.current_price
            continue
        if p.side == "YES":
            price = normalize_probability_price(market.yes_bid) or 0.0
            if price == 0.0:
                price = normalize_probability_price(market.yes_ask) or 0.0
        else:
            price = normalize_probability_price(market.no_bid) or 0.0
            if price == 0.0:
                price = normalize_probability_price(market.no_ask) or 0.0
        _price_cache[p.market_ticker] = (price, now)
        result[p.market_ticker] = price
    return result


async def _execute_pipeline() -> None:
    """Wrapper that flips the running flag on completion."""
    global _pipeline_running
    try:
        settings = get_settings()
        await run_pipeline(settings)
    except Exception:
        logger.exception("Pipeline run failed")
    finally:
        _pipeline_running = False


@router.post("/api/pipeline/run", status_code=202)
async def trigger_pipeline():
    """Kick off a full pipeline cycle. Returns 409 if one is already running."""
    global _pipeline_running, _pipeline_task
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    _pipeline_running = True
    _pipeline_task = asyncio.create_task(_execute_pipeline())
    return {"status": "started"}


@router.get("/api/pipeline/status")
async def pipeline_status():
    """Check whether a pipeline cycle is currently in progress."""
    return {"running": _pipeline_running}


# ---------------------------------------------------------------------------
# Daemon status
# ---------------------------------------------------------------------------

_DAEMON_OFFLINE: dict = {
    "available": False,
    "running": False,
    "paused": False,
    "uptime_seconds": 0,
    "cycles_completed": 0,
    "consecutive_failures": 0,
    "last_cycle": None,
}


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
