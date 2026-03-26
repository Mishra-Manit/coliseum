"""File I/O operations for opportunities and trades."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, field_validator

from coliseum.agents.shared_tools import _strip_cite_tokens
from coliseum.storage._io import atomic_write, yaml_dump, append_jsonl
from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)


class OpportunitySignal(BaseModel):
    """Scout-discovered opportunity."""

    # Scout fields
    id: str = Field(
        description="Unique opportunity ID with 'opp_' prefix (e.g., 'opp_a1b2c3d4'). Use generate_opportunity_id_tool() to create."
    )
    event_ticker: str = Field(
        description="Kalshi event ticker from market data (e.g., 'KXNFL-2024')"
    )
    event_title: str = Field(
        default="",
        description="Human-readable event name from Kalshi events API (e.g., 'Lowest temperature in Chicago on Mar 11, 2026?')"
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
    # Structured Scout output (populated by new prompt format)
    outcome_status: str = Field(default="", description="CONFIRMED | NEAR-DECIDED | STRONGLY FAVORED")
    risk_level: str = Field(default="", description="NEGLIGIBLE | LOW | MODERATE | HIGH")
    resolution_source: str = Field(default="", description="One sentence on resolution mechanism")
    evidence_bullets: list[str] = Field(default_factory=list, description="2-4 specific quantitative facts")
    remaining_risks: list[str] = Field(default_factory=list, description="1-3 brief risk items")
    scout_sources: list[str] = Field(default_factory=list, description="Real https:// URLs from Scout research")
    # Research fields
    research_completed_at: datetime | None = None
    research_duration_seconds: int | None = None

    # Recommendation fields
    recommendation_completed_at: datetime | None = None
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"] | None = None

    # Trader fields
    trader_decision: str = Field(default="", description="EXECUTE_BUY_YES | EXECUTE_BUY_NO | REJECT")
    trader_tldr: str = Field(default="", description="10-15 word summary from Trader agent")


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
    paper: bool
    executed_at: datetime

    @field_validator("price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("total")
    @classmethod
    def round_total(cls, v: float) -> float:
        return round(v, 2)


class TradeClose(BaseModel):
    """Position closure record written by Guardian when a market resolves."""

    id: str
    opportunity_id: str | None
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    entry_rationale: str | None
    closed_at: datetime

    @field_validator("entry_price", "exit_price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("pnl")
    @classmethod
    def round_usd(cls, v: float) -> float:
        return round(v, 2)


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
    return f"---\n{yaml_dump(frontmatter_data)}---\n\n{body}"


def _get_opps_dir(paper: bool = False) -> Path:
    """Return the base opportunities directory, routed by paper mode."""
    base = get_data_dir() / "opportunities"
    return base / "paper-mode" if paper else base


_atomic_write = atomic_write


def _parse_frontmatter(content: str, file_path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content, returning (frontmatter_dict, body)."""
    if not content.startswith("---"):
        raise ValueError(f"Invalid frontmatter in {file_path}")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Could not parse frontmatter in {file_path}")
    return yaml.safe_load(parts[1]) or {}, parts[2]


def _iter_date_dirs(base_dir: Path, lookback_days: int) -> list[Path]:
    """Return date subdirectories sorted newest-first, up to lookback_days+1."""
    if not base_dir.exists():
        return []
    return sorted(
        [d for d in base_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )[:lookback_days + 1]


def _generate_id(prefix: str) -> str:
    """Generate a short unique ID with the given prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


def save_opportunity(opportunity: OpportunitySignal, paper: bool = False) -> Path:
    """Save opportunity to markdown file."""
    opps_dir = _get_opps_dir(paper)
    date_dir = _ensure_date_dir(opps_dir, opportunity.discovered_at)

    filename = f"{opportunity.market_ticker}.md"
    file_path = date_dir / filename

    # Strip cite tokens from all text fields before writing
    clean_rationale = _strip_cite_tokens(opportunity.rationale)
    clean_resolution = _strip_cite_tokens(opportunity.resolution_source)
    clean_evidence = [_strip_cite_tokens(b) for b in opportunity.evidence_bullets]
    clean_risks = [_strip_cite_tokens(r) for r in opportunity.remaining_risks]

    # Build a clean copy for frontmatter — rationale goes to frontmatter as short summary
    clean_opp = opportunity.model_copy(update={
        "rationale": clean_rationale,
        "resolution_source": clean_resolution,
        "evidence_bullets": clean_evidence,
        "remaining_risks": clean_risks,
    })
    frontmatter = clean_opp.model_dump(mode="json", exclude={"title", "subtitle"})

    event_line = f"**Event**: {opportunity.event_title}\n" if opportunity.event_title else ""
    subtitle_section = f"\n**Outcome**: {opportunity.subtitle}\n" if opportunity.subtitle else ""

    # Build structured Scout Assessment section
    evidence_lines = "\n".join(f"- {b}" for b in clean_evidence) if clean_evidence else "- See rationale"
    risks_lines = "\n".join(f"- {r}" for r in clean_risks) if clean_risks else "- None identified"
    sources_lines = "\n".join(f"- {s}" for s in opportunity.scout_sources) if opportunity.scout_sources else ""

    verdict_line = (
        f"**{opportunity.outcome_status}**  ·  **{opportunity.risk_level} RISK**"
        if opportunity.outcome_status
        else f"**Rationale**: {clean_rationale}"
    )

    scout_section = f"""## Scout Assessment

{verdict_line}

{clean_rationale}

**Evidence**
{evidence_lines}

**Resolution**
{clean_resolution}

**Risks**
{risks_lines}
"""
    if sources_lines:
        scout_section += f"\n**Sources**\n{sources_lines}\n"

    body = f"""# {opportunity.title}
{event_line}{subtitle_section}
{scout_section}
## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | {opportunity.yes_price * 100:.0f}¢ (${opportunity.yes_price:.2f}) |
| No Price | {opportunity.no_price * 100:.0f}¢ (${opportunity.no_price:.2f}) |
| Closes | {opportunity.close_time.strftime('%Y-%m-%d %I:%M %p')} |
"""

    content = _format_markdown_with_frontmatter(frontmatter, body)
    _atomic_write(file_path, content)

    logger.info("Saved opportunity to %s", file_path)
    return file_path


def append_to_opportunity(
    market_ticker: str,
    frontmatter_updates: dict,
    body_section: str,
    section_header: str,
    lookback_days: int = 7,
    paper: bool = False,
) -> Path:
    """Safely append research or recommendation data to an existing opportunity file."""
    file_path = find_opportunity_file(market_ticker, lookback_days, paper=paper)
    if not file_path:
        raise FileNotFoundError(f"Opportunity file not found: {market_ticker}")

    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content, file_path)

    if section_header in body:
        logger.warning("Section '%s' already exists in %s", section_header, file_path)
        raise ValueError(f"Section '{section_header}' already exists")

    frontmatter.update(frontmatter_updates)

    new_body = body.rstrip() + "\n\n" + body_section
    new_content = f"---\n{yaml_dump(frontmatter)}---{new_body}"
    _atomic_write(file_path, new_content)

    logger.info("Appended section '%s' to %s", section_header, file_path)
    return file_path


def update_opportunity_frontmatter(file_path: Path, frontmatter_updates: dict) -> None:
    """Atomically update frontmatter fields in an opportunity markdown file."""
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content, file_path)

    frontmatter.update(frontmatter_updates)

    new_content = f"---\n{yaml_dump(frontmatter)}---{body}"
    _atomic_write(file_path, new_content)

    logger.info("Updated frontmatter in %s", file_path)


def mark_opportunity_failed(
    file_path: Path,
    *,
    failed_stage: str,
    error_message: str,
) -> None:
    """Persist failed status metadata without altering existing markdown body."""
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content, file_path)

    frontmatter.update(
        {
            "status": "failed",
            "failed_stage": failed_stage,
            "failure_error": error_message,
            "failed_at": datetime.utcnow().isoformat() + "Z",
        }
    )

    new_content = f"---\n{yaml_dump(frontmatter)}---{body}"
    _atomic_write(file_path, new_content)

    logger.info("Marked opportunity failed in %s", file_path)


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
        # New files have rationale in frontmatter; old files have it in the body
        "rationale": rationale or frontmatter.get("rationale", ""),
    }

    return OpportunitySignal(**data)


def load_opportunity_from_file(file_path: Path) -> OpportunitySignal:
    """Load opportunity data from a markdown file path."""
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content, file_path)
    return _parse_opportunity_from_parts(frontmatter, body)


def find_opportunity_file_by_id(
    opportunity_id: str, lookback_days: int = 7, paper: bool = False
) -> Path | None:
    """Find opportunity file by searching for ID in YAML frontmatter."""
    opps_dir = _get_opps_dir(paper)

    for date_dir in _iter_date_dirs(opps_dir, lookback_days):
        for file_path in date_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                frontmatter, _ = _parse_frontmatter(content, file_path)
                if frontmatter.get("id") == opportunity_id:
                    return file_path
            except Exception as e:
                logger.warning("Error reading %s: %s", file_path, e)
                continue

    return None


def get_opportunity_markdown_body(file_path: Path) -> str:
    """Get the markdown body from an opportunity file."""
    content = file_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[2].strip()


def log_trade(trade: TradeExecution) -> None:
    """Append trade execution to JSONL ledger in data/trades/buy/{date}.jsonl."""
    date_str = trade.executed_at.strftime("%Y-%m-%d")
    ledger_path = get_data_dir() / "trades" / "buy" / f"{date_str}.jsonl"
    append_jsonl(ledger_path, trade)
    logger.info("Logged trade %s to %s", trade.id, ledger_path)


def log_trade_close(close: TradeClose) -> None:
    """Append position closure record to JSONL ledger in data/trades/close/{date}.jsonl."""
    date_str = close.closed_at.strftime("%Y-%m-%d")
    ledger_path = get_data_dir() / "trades" / "close" / f"{date_str}.jsonl"
    append_jsonl(ledger_path, close)
    logger.info("Logged trade close %s to %s", close.id, ledger_path)


def generate_opportunity_id() -> str:
    """Generate unique opportunity ID."""
    return _generate_id("opp")


def generate_trade_id() -> str:
    """Generate unique trade execution ID."""
    return _generate_id("trade")


def generate_close_id() -> str:
    """Generate unique trade closure ID."""
    return _generate_id("close")


def find_opportunity_file(market_ticker: str, lookback_days: int = 7, paper: bool = False) -> Path | None:
    """Find the opportunity markdown file for a given market ticker."""
    opps_dir = _get_opps_dir(paper)

    for date_dir in _iter_date_dirs(opps_dir, lookback_days):
        file_path = date_dir / f"{market_ticker}.md"
        if file_path.exists():
            return file_path

    return None
