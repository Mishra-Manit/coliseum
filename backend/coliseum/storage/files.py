"""File I/O operations for opportunities and trades.

This module handles saving opportunities to markdown files
with YAML frontmatter, and logging trades to JSONL format. All files use date-based
directory organization for easy browsing.
"""

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

# Status type alias for opportunity lifecycle
OpportunityStatus = Literal[
    "pending", "researching", "recommended", "traded", "expired", "skipped"
]


# ============================================================================
# Pydantic Models
# ============================================================================


class OpportunitySignal(BaseModel):
    """Scout-discovered opportunity with progressive enrichment through pipeline stages."""

    # Scout fields (created at discovery)
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
        description="Additional context or specific outcome being bet on (e.g., movie name, player name). Empty string if not applicable."
    )
    yes_price: float = Field(
        ge=0, le=1,
        description="YES contract price as decimal 0-1. Calculate as yes_ask / 100 (e.g., 45 cents = 0.45)"
    )
    no_price: float = Field(
        ge=0, le=1,
        description="NO contract price as decimal 0-1. Calculate as no_ask / 100 (e.g., 56 cents = 0.56)"
    )
    close_time: datetime = Field(
        description="Market close timestamp in ISO 8601 format from market data 'close_time' field"
    )
    rationale: str = Field(
        description="Explanation for selecting this opportunity. MUST reference only market data (spread, volume, implied probability). Do NOT fabricate external facts."
    )
    discovered_at: datetime = Field(
        description="Timestamp when Scout discovered this (ISO 8601 format, current time)"
    )
    status: Literal[
        "pending", "researching", "recommended", "traded", "expired", "skipped"
    ] = Field(
        default="pending",
        description="Opportunity lifecycle status. 'pending' → 'researching' → 'recommended' → 'traded'"
    )

    # Research fields (null initially, populated by Researcher)
    research_completed_at: datetime | None = None
    research_duration_seconds: int | None = None

    # Recommendation fields (null initially, populated by Recommender)
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


class TradeExecution(BaseModel):
    """Trade execution record - logged to JSONL."""

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
    paper: bool  # True if paper trading
    executed_at: datetime
    strategy: str = "research_driven"


# ============================================================================
# Helper Functions
# ============================================================================


def _ensure_date_dir(base_dir: Path, date: datetime) -> Path:
    """Ensure date-based subdirectory exists (YYYY-MM-DD format).

    Args:
        base_dir: Base directory (e.g., data/opportunities/)
        date: Date for directory name

    Returns:
        Path to date directory
    """
    date_str = date.strftime("%Y-%m-%d")
    date_dir = base_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir


def _format_markdown_with_frontmatter(
    frontmatter_data: dict, body: str
) -> str:
    """Format markdown with YAML frontmatter.

    Args:
        frontmatter_data: Dictionary to serialize as YAML frontmatter
        body: Markdown body content

    Returns:
        Complete markdown file content
    """
    frontmatter = yaml.dump(
        frontmatter_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{frontmatter}---\n\n{body}"


# ============================================================================
# Public API
# ============================================================================


def save_opportunity(opportunity: OpportunitySignal) -> Path:
    """Save opportunity to markdown file in data/opportunities/{date}/{ticker}.md.

    Args:
        opportunity: Opportunity signal from Scout

    Returns:
        Path to created markdown file

    Raises:
        OSError: If file write fails
    """
    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"
    date_dir = _ensure_date_dir(opps_dir, opportunity.discovered_at)

    # Generate filename from market ticker
    filename = f"{opportunity.market_ticker}.md"
    file_path = date_dir / filename

    # Prepare frontmatter (all fields except title, subtitle, and rationale)
    frontmatter = opportunity.model_dump(
        mode="json", exclude={"title", "subtitle", "rationale"}
    )

    # Prepare markdown body
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

    # Write markdown file
    content = _format_markdown_with_frontmatter(frontmatter, body)
    file_path.write_text(content, encoding="utf-8")

    logger.info(f"Saved opportunity to {file_path}")
    return file_path


def append_to_opportunity(
    market_ticker: str,
    frontmatter_updates: dict,
    body_section: str,
    section_header: str,
    lookback_days: int = 7,
) -> Path:
    """Safely append research or recommendation data to existing opportunity file.

    Uses atomic read-modify-write pattern to prevent corruption.

    Args:
        market_ticker: Market ticker to identify the file
        frontmatter_updates: Dict of fields to update in YAML frontmatter
        body_section: Markdown content to append (complete section with header)
        section_header: Section marker (e.g., "## Research Synthesis") for duplicate detection
        lookback_days: How many days back to search for file

    Returns:
        Path to updated file

    Raises:
        FileNotFoundError: If opportunity file not found
        ValueError: If section already exists (prevents double-append)
    """
    # 1. Find the file
    file_path = find_opportunity_file(market_ticker, lookback_days)
    if not file_path:
        raise FileNotFoundError(f"Opportunity file not found: {market_ticker}")

    # 2. Read current content
    content = file_path.read_text(encoding="utf-8")

    # 3. Parse frontmatter and body
    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")

    frontmatter_raw = parts[1]
    body = parts[2]

    # 4. Parse and update frontmatter
    frontmatter = yaml.safe_load(frontmatter_raw) or {}

    # Check if section already exists (prevent double-append)
    if section_header in body:
        logger.warning(f"Section '{section_header}' already exists in {file_path}")
        raise ValueError(f"Section '{section_header}' already exists")

    # Update frontmatter fields
    frontmatter.update(frontmatter_updates)

    # 5. Append body section
    new_body = body.rstrip() + "\n\n" + body_section

    # 6. Reconstruct file
    new_frontmatter_raw = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    new_content = f"---\n{new_frontmatter_raw}---{new_body}"

    # 7. Atomic write (prevent corruption)
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.md',
        dir=file_path.parent,
        encoding='utf-8'
    ) as f:
        f.write(new_content)
        temp_path = Path(f.name)

    # Atomic rename (overwrites destination)
    shutil.move(str(temp_path), str(file_path))

    logger.info(f"Appended section '{section_header}' to {file_path}")
    return file_path


def _parse_opportunity_from_parts(frontmatter: dict, body: str) -> OpportunitySignal:
    """Build OpportunitySignal from frontmatter and body content."""
    # Extract title, subtitle, rationale from body
    lines = body.strip().split("\n")
    title = ""
    subtitle = ""
    rationale = ""

    for line in lines:
        # Strip whitespace AND replace literal \n characters from old broken files
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


def load_opportunity_with_all_stages(
    market_ticker: str, lookback_days: int = 7
) -> OpportunitySignal:
    """Load opportunity file with all stages (scout + research + recommendation).

    Args:
        market_ticker: Market ticker to identify the file
        lookback_days: How many days back to search for file

    Returns:
        Complete OpportunitySignal with all stages populated

    Raises:
        FileNotFoundError: If opportunity file not found
        ValueError: If file format is invalid
    """
    file_path = find_opportunity_file(market_ticker, lookback_days)
    if not file_path:
        raise FileNotFoundError(f"Opportunity file not found: {market_ticker}")

    return load_opportunity_from_file(file_path)


def get_opportunity_markdown_body(file_path: Path) -> str:
    """Get the markdown body (everything after frontmatter) from an opportunity file.

    Args:
        file_path: Path to opportunity markdown file

    Returns:
        The full markdown body as a string
    """
    content = file_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[2].strip()


def log_trade(trade: TradeExecution) -> None:
    """Append trade execution to JSONL ledger in data/trades/{date}.jsonl.

    Note:
        Uses atomic append - each trade is a single JSON object on one line.
        File is created if it doesn't exist.
    """
    data_dir = get_data_dir()
    trades_dir = data_dir / "trades"
    trades_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from execution date
    date_str = trade.executed_at.strftime("%Y-%m-%d")
    ledger_path = trades_dir / f"{date_str}.jsonl"

    # Serialize trade to JSON (one line)
    trade_json = trade.model_dump_json() + "\\n"

    # Atomic append
    try:
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(trade_json)

        logger.info(f"Logged trade {trade.id} to {ledger_path}")

    except Exception as e:
        logger.error(f"Failed to log trade {trade.id}: {e}")
        raise


def generate_opportunity_id() -> str:
    """Generate unique opportunity ID with opp_ prefix."""
    return f"opp_{uuid4().hex[:8]}"


def generate_trade_id() -> str:
    """Generate unique trade execution ID with trade_ prefix."""
    return f"trade_{uuid4().hex[:8]}"


def find_opportunity_file(market_ticker: str, lookback_days: int = 7) -> Path | None:
    """Find the opportunity markdown file for a given market ticker.
    
    Searches all date directories (newest to oldest) within lookback_days.
    """
    data_dir = get_data_dir()
    opps_dir = data_dir / "opportunities"
    
    if not opps_dir.exists():
        return None
    
    # Get all date directories and sort newest first
    date_dirs = sorted(
        [d for d in opps_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True  # Newest first
    )
    
    # Search in each date directory
    for date_dir in date_dirs[:lookback_days + 1]:  # Limit to lookback_days
        file_path = date_dir / f"{market_ticker}.md"
        if file_path.exists():
            return file_path
    
    return None


def update_opportunity_status(
    market_ticker: str,
    new_status: OpportunityStatus,
    lookback_days: int = 7,
) -> bool:
    """Update the status field in an opportunity's markdown frontmatter.
    
    This updates the YAML frontmatter and preserves the rest of the file.
    Note: Memory system is updated separately by the calling agent.
    """
    file_path = find_opportunity_file(market_ticker, lookback_days)
    
    if file_path is None:
        logger.warning(f"Opportunity file not found for {market_ticker}")
        return False
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # Parse frontmatter and body
        if not content.startswith("---"):
            logger.error(f"Invalid frontmatter format in {file_path}")
            return False
        
        # Split into frontmatter and body
        parts = content.split("---", 2)
        if len(parts) < 3:
            logger.error(f"Could not parse frontmatter in {file_path}")
            return False
        
        frontmatter_raw = parts[1]
        body = parts[2]
        
        # Parse YAML frontmatter
        frontmatter = yaml.safe_load(frontmatter_raw)
        if frontmatter is None:
            frontmatter = {}
        
        old_status = frontmatter.get("status", "unknown")
        frontmatter["status"] = new_status
        
        # Reconstruct file with updated frontmatter
        new_frontmatter_raw = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        new_content = f"---\n{new_frontmatter_raw}---{body}"
        
        # Write back
        file_path.write_text(new_content, encoding="utf-8")
        
        logger.info(
            f"Updated opportunity status: {market_ticker} ({old_status} -> {new_status})"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update opportunity status for {market_ticker}: {e}")
        return False


def opportunity_exists(market_ticker: str, lookback_days: int = 7) -> bool:
    """Check if an opportunity file exists for a given market ticker."""
    return find_opportunity_file(market_ticker, lookback_days) is not None
