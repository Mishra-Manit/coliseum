"""File I/O operations for opportunities, recommendations, and trades.

This module handles saving opportunities, research briefs, recommendations to markdown files
with YAML frontmatter, and logging trades to JSONL format. All files use date-based
directory organization for easy browsing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from coliseum.llm_providers import (
    AnthropicModel,
    FireworksModel,
    get_model_string,
)
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
    """Scout-discovered opportunity - matches DESIGN.md spec."""

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
    priority: Literal["high", "medium", "low"] = Field(
        description="Scout's priority: 'high' for tight spreads + strong edge, 'medium' for moderate, 'low' for marginal"
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
        description="Opportunity lifecycle status. Always 'pending' for newly discovered opportunities."
    )


class ResearchBrief(BaseModel):
    """Analyst research output - freeform synthesis with structured hooks."""

    id: str
    opportunity_id: str
    event_ticker: str
    market_ticker: str

    # Freeform synthesis - agent organizes findings however it sees fit
    synthesis: str  # Markdown-formatted research output

    # Structured fields for downstream agent consumption
    sources: list[str]  # URLs with citations
    confidence_level: Literal["high", "medium", "low"]
    sentiment: Literal["bullish", "bearish", "neutral"]
    key_uncertainties: list[str]  # What could invalidate this analysis?

    # Metadata
    created_at: datetime
    research_depth: Literal["quick", "standard", "deep"] = "standard"
    model_used: str = FireworksModel.LLAMA_3_3_70B_INSTRUCT
    tokens_used: int | None = None
    research_duration_seconds: int | None = None


class TradeRecommendation(BaseModel):
    """Analyst trade recommendation - matches DESIGN.md spec."""

    id: str
    opportunity_id: str
    research_brief_id: str
    event_ticker: str
    market_ticker: str
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"]
    status: Literal["pending", "approved", "executed", "rejected", "expired"] = (
        "pending"
    )
    confidence: float = Field(ge=0, le=1)
    estimated_true_probability: float = Field(ge=0, le=1)
    current_market_price: float = Field(ge=0, le=1)
    expected_value: float
    edge: float
    suggested_position_pct: float = Field(ge=0, le=0.10)
    reasoning: str
    key_risks: list[str]
    created_at: datetime
    executed_at: datetime | None = None
    model_used: str = FireworksModel.LLAMA_3_3_70B_INSTRUCT


class TradeExecution(BaseModel):
    """Trade execution record - logged to JSONL."""

    id: str
    position_id: str | None
    recommendation_id: str
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

**Priority**: {opportunity.priority.title()}

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


def save_research_brief(brief: ResearchBrief) -> Path:
    """Save research brief to markdown file in data/research/{date}/{ticker}.md."""
    data_dir = get_data_dir()
    research_dir = data_dir / "research"
    date_dir = _ensure_date_dir(research_dir, brief.created_at)

    filename = f"{brief.market_ticker}.md"
    file_path = date_dir / filename

    # Frontmatter contains metadata, excludes long-form content
    frontmatter = brief.model_dump(
        mode="json",
        exclude={"synthesis", "sources", "key_uncertainties"},
    )

    # Format sources and uncertainties
    sources_md = "\n".join(
        f"{i+1}. [{src}]({src})" for i, src in enumerate(brief.sources)
    )
    uncertainties_md = "\n".join(
        f"- {uncertainty}" for uncertainty in brief.key_uncertainties
    )

    body = f"""# Research: {brief.event_ticker}

## Synthesis

{brief.synthesis}

## Key Uncertainties

{uncertainties_md}

## Sources

{sources_md}

## Assessment

- **Confidence Level**: {brief.confidence_level.title()}
- **Sentiment**: {brief.sentiment.title()}
"""

    # Write markdown file
    content = _format_markdown_with_frontmatter(frontmatter, body)
    file_path.write_text(content, encoding="utf-8")

    logger.info(f"Saved research brief to {file_path}")
    return file_path


def save_recommendation(recommendation: TradeRecommendation) -> Path:
    """Save trade recommendation to markdown file in data/recommendations/{date}/{ticker}.md."""
    data_dir = get_data_dir()
    recs_dir = data_dir / "recommendations"
    date_dir = _ensure_date_dir(recs_dir, recommendation.created_at)

    # Generate filename from market ticker
    filename = f"{recommendation.market_ticker}.md"
    file_path = date_dir / filename

    # Prepare frontmatter
    frontmatter = recommendation.model_dump(
        mode="json", exclude={"reasoning", "key_risks"}
    )

    # Prepare markdown body
    risks_md = "\n".join(
        f"{i+1}. **{risk.split(':')[0] if ':' in risk else 'Risk'}**: {risk}"
        for i, risk in enumerate(recommendation.key_risks)
    )

    body = f"""# Trade Recommendation: {recommendation.action} on {recommendation.market_ticker}

## Summary

| Metric | Value |
|--------|-------|
| **Action** | {recommendation.action} |
| **Confidence** | {recommendation.confidence:.0%} |
| **Edge** | {recommendation.edge:+.0%} |
| **Expected Value** | {recommendation.expected_value:+.0%} |
| **Suggested Size** | {recommendation.suggested_position_pct:.1%} of portfolio |
| **Status** | {recommendation.status.title()} |

## Reasoning

{recommendation.reasoning}

## Key Risks

{risks_md}

## Trade Details

- **Estimated True Probability**: {recommendation.estimated_true_probability:.0%}
- **Current Market Price**: {recommendation.current_market_price * 100:.0f}¢ (${recommendation.current_market_price:.2f})
- **Model Used**: {recommendation.model_used}
- **Created**: {recommendation.created_at.strftime('%Y-%m-%d %I:%M %p UTC')}
"""

    # Write markdown file
    content = _format_markdown_with_frontmatter(frontmatter, body)
    file_path.write_text(content, encoding="utf-8")

    logger.info(f"Saved recommendation to {file_path}")
    return file_path


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
    trade_json = trade.model_dump_json() + "\n"

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


def generate_research_id() -> str:
    """Generate unique research brief ID with research_ prefix."""
    return f"research_{uuid4().hex[:8]}"


def generate_recommendation_id() -> str:
    """Generate unique recommendation ID with rec_ prefix."""
    return f"rec_{uuid4().hex[:8]}"


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
    
    This updates both the YAML frontmatter and preserves the rest of the file.
    Also updates the state.yaml seen_markets entry if present.
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
        
        # Also update state.yaml if this market is tracked
        from coliseum.storage.state import update_market_status
        update_market_status(market_ticker, new_status)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update opportunity status for {market_ticker}: {e}")
        return False


def opportunity_exists(market_ticker: str, lookback_days: int = 7) -> bool:
    """Check if an opportunity file exists for a given market ticker."""
    return find_opportunity_file(market_ticker, lookback_days) is not None
