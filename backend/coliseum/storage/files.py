"""File I/O operations for opportunities and trades."""

import json
import logging
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from coliseum.llm_providers import FireworksModel
from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)

OpportunityStrategy = Literal["edge", "sure_thing"]


class OpportunitySignal(BaseModel):
    """Scout-discovered opportunity."""

    # Scout fields
    id: str = Field(
        description="Unique opportunity ID with 'opp_' prefix (e.g., 'opp_a1b2c3d4'). Use generate_opportunity_id_tool() to create."
    )
    event_ticker: str = Field(
        description="Kalshi event ticker from market data (e.g., 'KXNFL-2024')"
    )
    market_ticker: str = Field(
        description="Kalshi market ticker from market data 'ticker' field (e.g., 'KXNFL-2024-KC-WIN')"
    )
    title: str = Field(
        description="Human-readable market title describing the event outcome"
    )
    subtitle: str = Field(
        default="",
        description="Additional context or specific outcome being bet on. Empty string if not applicable."
    )
    yes_price: float = Field(
        ge=0, le=1,
        description="YES contract price as decimal 0-1."
    )
    no_price: float = Field(
        ge=0, le=1,
        description="NO contract price as decimal 0-1."
    )
    close_time: datetime = Field(
        description="Market close timestamp in ISO 8601 format"
    )
    rationale: str = Field(
        description="Explanation for selecting this opportunity. MUST reference only market data."
    )
    discovered_at: datetime = Field(
        description="Timestamp when Scout discovered this"
    )
    status: str = Field(
        default="pending",
        description="Lifecycle status for the opportunity."
    )
    # Research fields
    research_completed_at: datetime | None = None
    research_duration_seconds: int | None = None

    # Recommendation fields
    estimated_true_probability: float | None = None
    current_market_price: float | None = None
    expected_value: float | None = None
    edge: float | None = None
    suggested_position_pct: float | None = None
    # NO-side metrics
    edge_no: float | None = None
    expected_value_no: float | None = None
    suggested_position_pct_no: float | None = None
    recommendation_completed_at: datetime | None = None
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"] | None = None
    strategy: Literal["edge", "sure_thing"] = "edge"


class TradeExecution(BaseModel):
    """Trade execution record."""

    id: str
    position_id: str | None
    opportunity_id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    action: Literal["BUY", "SELL"]
    contracts: int
    price: float
    total: float
    portfolio_pct: float
    edge: float
    ev: float
    paper: bool
    executed_at: datetime
    strategy: str = "research_driven"


def _ensure_date_dir(base_dir: Path, date: datetime) -> Path:
    """Ensure date-based subdirectory exists (YYYY-MM-DD format)."""
    date_str = date.strftime("%Y-%m-%d")
    date_dir = base_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir


def _format_markdown_with_frontmatter(
    frontmatter_data: dict, body: str
) -> str:
    """Format markdown with YAML frontmatter."""
    frontmatter = yaml.dump(
        frontmatter_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{frontmatter}---\n\n{body}"


def save_opportunity(opportunity: OpportunitySignal) -> Path:
    """Save opportunity to markdown file."""
    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"
    date_dir = _ensure_date_dir(opps_dir, opportunity.discovered_at)

    filename = f"{opportunity.market_ticker}.md"
    file_path = date_dir / filename

    frontmatter = opportunity.model_dump(
        mode="json", exclude={"title", "subtitle", "rationale"}
    )

    subtitle_section = f"\n**Outcome**: {opportunity.subtitle}\n" if opportunity.subtitle else ""

    body = f"""# {opportunity.title}
{subtitle_section}
## Scout Assessment

**Rationale**: {opportunity.rationale}

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | {opportunity.yes_price * 100:.0f}¢ (${opportunity.yes_price:.2f}) |
| No Price | {opportunity.no_price * 100:.0f}¢ (${opportunity.no_price:.2f}) |
| Closes | {opportunity.close_time.strftime('%Y-%m-%d %I:%M %p')} |
"""

    content = _format_markdown_with_frontmatter(frontmatter, body)

    # Atomic write
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.md',
        dir=file_path.parent,
        encoding='utf-8'
    ) as f:
        f.write(content)
        temp_path = Path(f.name)

    shutil.move(str(temp_path), str(file_path))

    logger.info(f"Saved opportunity to {file_path}")
    return file_path


def append_to_opportunity(
    market_ticker: str,
    frontmatter_updates: dict,
    body_section: str,
    section_header: str,
    lookback_days: int = 7,
) -> Path:
    """Safely append research or recommendation data to an existing opportunity file."""
    file_path = find_opportunity_file(market_ticker, lookback_days)
    if not file_path:
        raise FileNotFoundError(f"Opportunity file not found: {market_ticker}")

    content = file_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")

    frontmatter_raw = parts[1]
    body = parts[2]

    frontmatter = yaml.safe_load(frontmatter_raw) or {}

    if section_header in body:
        logger.warning(f"Section '{section_header}' already exists in {file_path}")
        raise ValueError(f"Section '{section_header}' already exists")

    frontmatter.update(frontmatter_updates)

    new_body = body.rstrip() + "\n\n" + body_section

    new_frontmatter_raw = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    new_content = f"---\n{new_frontmatter_raw}---{new_body}"

    # Atomic write
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.md',
        dir=file_path.parent,
        encoding='utf-8'
    ) as f:
        f.write(new_content)
        temp_path = Path(f.name)

    shutil.move(str(temp_path), str(file_path))

    logger.info(f"Appended section '{section_header}' to {file_path}")
    return file_path


def update_opportunity_frontmatter(file_path: Path, frontmatter_updates: dict) -> None:
    """Atomically update frontmatter fields in an opportunity markdown file."""
    content = file_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")

    frontmatter_raw = parts[1]
    body = parts[2]

    frontmatter = yaml.safe_load(frontmatter_raw) or {}
    frontmatter.update(frontmatter_updates)

    new_frontmatter_raw = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    new_content = f"---\n{new_frontmatter_raw}---{body}"

    # Atomic write
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix=".md",
        dir=file_path.parent,
        encoding="utf-8",
    ) as f:
        f.write(new_content)
        temp_path = Path(f.name)

    shutil.move(str(temp_path), str(file_path))

    logger.info(f"Updated frontmatter in {file_path}")


def _parse_opportunity_from_parts(frontmatter: dict, body: str) -> OpportunitySignal:
    """Build OpportunitySignal from frontmatter and body content."""
    lines = body.strip().split("\n")
    title = ""
    subtitle = ""
    rationale = ""

    for line in lines:
        line = line.strip().replace("\\n", "")

        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("**Outcome**:"):
            subtitle = line.split(":", 1)[1].strip()
        elif line.startswith("**Rationale**:"):
            rationale = line.split(":", 1)[1].strip()

    data = {
        **frontmatter,
        "title": title,
        "subtitle": subtitle or "",
        "rationale": rationale,
    }

    return OpportunitySignal(**data)


def load_opportunity_from_file(file_path: Path) -> OpportunitySignal:
    """Load opportunity data from a markdown file path."""
    content = file_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")

    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2]

    return _parse_opportunity_from_parts(frontmatter, body)


def _load_opportunity_frontmatter(file_path: Path) -> dict:
    """Load and parse YAML frontmatter from an opportunity markdown file."""
    content = file_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")

    return yaml.safe_load(parts[1]) or {}


def get_opportunity_strategy_from_file(file_path: Path) -> OpportunityStrategy:
    """Read and validate strategy directly from opportunity frontmatter."""
    frontmatter = _load_opportunity_frontmatter(file_path)
    strategy = frontmatter.get("strategy")

    if strategy not in {"edge", "sure_thing"}:
        raise ValueError(
            f"Opportunity {file_path} must define strategy as 'edge' or 'sure_thing'"
        )

    return strategy


def find_opportunity_file_by_id(
    opportunity_id: str, lookback_days: int = 7
) -> Path | None:
    """Find opportunity file by searching for ID in YAML frontmatter."""
    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"

    if not opps_dir.exists():
        return None

    date_dirs = sorted(
        [d for d in opps_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    for date_dir in date_dirs[:lookback_days + 1]:
        for file_path in date_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")

                if not content.startswith("---"):
                    continue

                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue

                frontmatter = yaml.safe_load(parts[1])
                if frontmatter and frontmatter.get("id") == opportunity_id:
                    return file_path

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue

    return None


def get_opportunity_strategy_by_id(
    opportunity_id: str, lookback_days: int = 7
) -> OpportunityStrategy:
    """Find an opportunity by ID and return its validated strategy."""
    opp_file = find_opportunity_file_by_id(opportunity_id, lookback_days=lookback_days)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")
    return get_opportunity_strategy_from_file(opp_file)


def load_opportunity_with_all_stages(
    market_ticker: str, lookback_days: int = 7
) -> OpportunitySignal:
    """Load opportunity file with all stages."""
    file_path = find_opportunity_file(market_ticker, lookback_days)
    if not file_path:
        raise FileNotFoundError(f"Opportunity file not found: {market_ticker}")

    return load_opportunity_from_file(file_path)


def get_opportunity_markdown_body(file_path: Path) -> str:
    """Get the markdown body from an opportunity file."""
    content = file_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[2].strip()


def log_trade(trade: TradeExecution) -> None:
    """Append trade execution to JSONL ledger in data/trades/{date}.jsonl."""
    data_dir = get_data_dir()
    trades_dir = data_dir / "trades"
    trades_dir.mkdir(parents=True, exist_ok=True)

    date_str = trade.executed_at.strftime("%Y-%m-%d")
    ledger_path = trades_dir / f"{date_str}.jsonl"

    trade_json = trade.model_dump_json() + "\n"

    try:
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(trade_json)

        logger.info(f"Logged trade {trade.id} to {ledger_path}")

    except Exception as e:
        logger.error(f"Failed to log trade {trade.id}: {e}")
        raise


def generate_opportunity_id() -> str:
    """Generate unique opportunity ID."""
    return f"opp_{uuid4().hex[:8]}"


def generate_trade_id() -> str:
    """Generate unique trade execution ID."""
    return f"trade_{uuid4().hex[:8]}"


def find_opportunity_file(market_ticker: str, lookback_days: int = 7) -> Path | None:
    """Find the opportunity markdown file for a given market ticker."""
    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"

    if not opps_dir.exists():
        return None

    date_dirs = sorted(
        [d for d in opps_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True
    )

    for date_dir in date_dirs[:lookback_days + 1]:
        file_path = date_dir / f"{market_ticker}.md"
        if file_path.exists():
            return file_path

    return None


def opportunity_exists(market_ticker: str, lookback_days: int = 7) -> bool:
    """Check if an opportunity file exists for a given market ticker."""
    return find_opportunity_file(market_ticker, lookback_days) is not None
