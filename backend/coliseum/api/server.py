"""FastAPI dashboard server for the Coliseum trading system."""

import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

app = FastAPI(title="Coliseum Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        logger.warning(f"Error parsing {file_path}: {e}")
        return None


def _get_all_opportunities() -> list[dict[str, Any]]:
    """Scan all opportunity markdown files across date directories."""
    opps_dir = DATA_DIR / "opportunities"
    if not opps_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for date_dir in sorted(
        [d for d in opps_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    ):
        for md_file in sorted(date_dir.glob("*.md"), reverse=True):
            parsed = _parse_opportunity(md_file)
            if parsed:
                results.append(parsed)
    return results


@app.get("/api/config")
async def get_config():
    """Return the full config.yaml contents."""
    return _load_yaml(DATA_DIR / "config.yaml")


@app.get("/api/state")
async def get_state():
    """Return the full state.yaml contents."""
    return _load_yaml(DATA_DIR / "state.yaml")


@app.get("/api/opportunities")
async def list_opportunities():
    """List all opportunities with frontmatter summary."""
    results = []
    for opp in _get_all_opportunities():
        fm = opp["frontmatter"]
        results.append({
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
            "strategy": fm.get("strategy", "edge"),
            "action": fm.get("action"),
            "estimated_true_probability": fm.get("estimated_true_probability"),
            "edge": fm.get("edge"),
            "expected_value": fm.get("expected_value"),
            "date_folder": opp["date_folder"],
        })
    return results


@app.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get full opportunity detail including markdown body."""
    for opp in _get_all_opportunities():
        fm = opp["frontmatter"]
        if fm.get("id") == opportunity_id:
            return {
                "summary": {
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
                    "strategy": fm.get("strategy", "edge"),
                    "action": fm.get("action"),
                    "estimated_true_probability": fm.get("estimated_true_probability"),
                    "edge": fm.get("edge"),
                    "expected_value": fm.get("expected_value"),
                    "date_folder": opp["date_folder"],
                },
                "markdown_body": opp["body"],
                "raw_frontmatter": fm,
            }
    raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
