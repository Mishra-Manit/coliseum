"""Memory system for tracking agent trading decisions and outcomes."""

import logging
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from coliseum.config import get_settings

logger = logging.getLogger(__name__)

MemoryStatus = Literal["PENDING", "SKIPPED", "EXECUTED", "CLOSED"]


class TradeDetails(BaseModel):
    """Trade execution details - added by Trader agent."""
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float = Field(description="Entry price as decimal 0-1")
    reasoning: str | None = None


class TradeOutcome(BaseModel):
    """Exit outcome - added when position closes."""
    exit_price: float = Field(description="Exit price as decimal 0-1")
    pnl: float = Field(description="Profit/loss in dollars")


class MemoryEntry(BaseModel):
    """Core memory entry - progressively enriched by agents."""
    market_ticker: str = Field(description="Kalshi market ticker")
    discovered_at: datetime = Field(description="When Scout discovered this opportunity")
    close_time: datetime = Field(description="Market close time")
    status: MemoryStatus = Field(default="PENDING")
    
    trade: TradeDetails | None = None
    outcome: TradeOutcome | None = None


def get_memory_path() -> Path:
    """Get the path to the memory file (data/memory.md)."""
    settings = get_settings()
    return settings.data_dir / "memory.md"


def _get_memory_header() -> str:
    """Return the header template for a new memory file."""
    return """# Agent Memory Log

> This file tracks the agent's trading plans, reasoning, and learnings.
> The Guardian reviews this to ensure the agent is following market strategy correctly.

---
"""


def _to_utc(dt: datetime) -> datetime:
    """Normalize datetime to UTC with tzinfo."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_entry_from_markdown(entry_text: str) -> MemoryEntry | None:
    """Parse a single memory entry from markdown text."""
    try:
        header_match = re.search(r"^## (\d{4}-\d{2}-\d{2}T[\d:]+Z?) - (.+)$", entry_text, re.MULTILINE)
        if not header_match:
            return None
        
        discovered_at_str = header_match.group(1)
        market_ticker = header_match.group(2).strip()
        
        if discovered_at_str.endswith("Z"):
            discovered_at = datetime.fromisoformat(discovered_at_str.replace("Z", "+00:00"))
        else:
            discovered_at = datetime.fromisoformat(discovered_at_str)
        discovered_at = _to_utc(discovered_at)
        
        def extract_table_value(field_name: str) -> str | None:
            pattern = rf"\|\s*\*\*{field_name}\*\*\s*\|\s*(.+?)\s*\|"
            match = re.search(pattern, entry_text)
            if match:
                value = match.group(1).strip()
                return value if value != "—" else None
            return None
        
        status = extract_table_value("Status") or "PENDING"
        close_time_str = extract_table_value("Close Time")
        
        close_time = None
        if close_time_str:
            try:
                if close_time_str.endswith("Z"):
                    close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                else:
                    close_time = datetime.fromisoformat(close_time_str)
            except ValueError:
                try:
                    close_time = datetime.strptime(close_time_str, "%Y-%m-%d")
                    close_time = close_time.replace(hour=23, minute=59, second=59)
                except ValueError:
                    pass
        if close_time is None:
            close_time = discovered_at
        close_time = _to_utc(close_time)
        
        # Parse trade details if present
        trade = None
        side = extract_table_value("Side")
        contracts_str = extract_table_value("Contracts")
        entry_price_str = extract_table_value("Entry Price")
        
        if side and contracts_str and entry_price_str:
            def extract_section(header: str) -> str | None:
                pattern = rf"### {header}\n(.*?)(?=\n### |\n---|\Z)"
                match = re.search(pattern, entry_text, re.DOTALL)
                return match.group(1).strip() if match else None
            
            trade = TradeDetails(
                side=side,  # type: ignore
                contracts=int(contracts_str),
                entry_price=float(entry_price_str.rstrip("¢")) / 100,
                reasoning=extract_section("Reasoning"),
            )
        
        # Parse outcome if present
        outcome = None
        outcome_section_match = re.search(r"### Outcome.*?\n(.*?)(?=\n### |\n---|\Z)", entry_text, re.DOTALL)
        if outcome_section_match:
            outcome_text = outcome_section_match.group(1)
            exit_price = None
            pnl = None
            for line in outcome_text.split("\n"):
                if "**Exit Price**" in line and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and val != "—":
                        exit_price = float(val.rstrip("¢")) / 100 if "¢" in val else float(val)
                elif "**P&L**" in line and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and val != "—" and "$" in val:
                        pnl = float(val.replace("$", "").replace(",", ""))
            if exit_price is not None and pnl is not None:
                outcome = TradeOutcome(exit_price=exit_price, pnl=pnl)
        
        return MemoryEntry(
            market_ticker=market_ticker,
            discovered_at=discovered_at,
            close_time=close_time,
            status=status,  # type: ignore
            trade=trade,
            outcome=outcome,
        )
        
    except Exception as e:
        logger.warning(f"Failed to parse memory entry: {e}")
        return None


def parse_memory_file(path: Path | None = None) -> list[MemoryEntry]:
    """Parse all entries from the memory file."""
    if path is None:
        path = get_memory_path()
    
    if not path.exists():
        return []
    
    content = path.read_text(encoding="utf-8")
    
    # Split by entry headers (## timestamp - ticker)
    entries: list[MemoryEntry] = []
    
    # Find all entry blocks (from ## to next ## or ---)
    pattern = r"(## \d{4}-\d{2}-\d{2}T[\d:]+Z? - .+?)(?=\n## \d{4}-\d{2}-\d{2}T|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        entry = _parse_entry_from_markdown(match)
        if entry:
            entries.append(entry)
    
    return entries




def _format_entry_to_markdown(entry: MemoryEntry) -> str:
    """Format a MemoryEntry to markdown text for appending to the file."""
    timestamp = _to_utc(entry.discovered_at).strftime("%Y-%m-%dT%H:%M:%SZ")
    close_date = _to_utc(entry.close_time).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    table_rows = [f"| **Status** | {entry.status} |"]
    
    if entry.trade:
        table_rows.append(f"| **Side** | {entry.trade.side} |")
        table_rows.append(f"| **Contracts** | {entry.trade.contracts} |")
        table_rows.append(f"| **Entry Price** | {entry.trade.entry_price * 100:.0f}¢ |")
    
    table_rows.append(f"| **Close Time** | {close_date} |")
    table = "| Field | Value |\n|-------|-------|\n" + "\n".join(table_rows)
    
    sections = []
    
    if entry.trade and entry.trade.reasoning:
        sections.append(f"### Reasoning\n{entry.trade.reasoning}")
    
    if entry.status == "CLOSED" and entry.outcome:
        sections.append(
            f"### Outcome\n"
            f"- **Exit Price**: {entry.outcome.exit_price * 100:.0f}¢\n"
            f"- **P&L**: ${entry.outcome.pnl:.2f}"
        )
    
    sections_text = "\n\n".join(sections) if sections else ""
    
    return f"""## {timestamp} - {entry.market_ticker}

{table}

{sections_text}

---
"""


def _atomic_write(path: Path, content: str) -> None:
    """Write content to file atomically using tempfile + move."""
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False, suffix=".md", encoding="utf-8"
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        shutil.move(str(temp_path), str(path))
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def append_memory_entry(entry: MemoryEntry) -> None:
    """Atomically append a new entry to the memory file."""
    memory_path = get_memory_path()
    
    if memory_path.exists():
        existing_content = memory_path.read_text(encoding="utf-8")
    else:
        existing_content = _get_memory_header()
        memory_path.parent.mkdir(parents=True, exist_ok=True)
    
    new_content = existing_content.rstrip() + "\n\n" + _format_entry_to_markdown(entry)
    _atomic_write(memory_path, new_content)
    logger.info(f"Appended memory entry for {entry.market_ticker}")


def get_seen_tickers() -> list[str]:
    """Get list of market tickers for markets that haven't closed yet.
    
    Only returns tickers for markets where close_time > now, since closed
    markets won't appear in the scout's market scan anyway.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    entries = parse_memory_file()
    return [entry.market_ticker for entry in entries if entry.close_time > now]


def is_market_seen(market_ticker: str) -> bool:
    """Check if a market ticker exists in memory."""
    return market_ticker in get_seen_tickers()


def get_entry_by_ticker(market_ticker: str) -> MemoryEntry | None:
    """Get the memory entry for a specific market ticker. Returns most recent if duplicates exist."""
    entries = parse_memory_file()
    for entry in reversed(entries):  # Most recent first
        if entry.market_ticker == market_ticker:
            return entry
    return None


def update_entry(
    market_ticker: str,
    *,
    status: MemoryStatus | None = None,
    trade: TradeDetails | None = None,
    outcome: TradeOutcome | None = None,
) -> bool:
    """Update an existing memory entry with status, trade, or outcome data."""
    memory_path = get_memory_path()

    if not memory_path.exists():
        logger.warning(f"Memory file not found: {memory_path}")
        return False

    content = memory_path.read_text(encoding="utf-8")

    pattern = rf"(## \d{{4}}-\d{{2}}-\d{{2}}T[\d:]+Z? - {re.escape(market_ticker)}.*?)(?=\n## \d{{4}}-\d{{2}}-\d{{2}}T|\Z)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        logger.warning(f"Memory entry not found for ticker: {market_ticker}")
        return False

    existing_entry = _parse_entry_from_markdown(match.group(1))
    if not existing_entry:
        logger.warning(f"Failed to parse existing entry for: {market_ticker}")
        return False

    if status is not None:
        existing_entry.status = status
    if trade is not None:
        existing_entry.trade = trade
    if outcome is not None:
        existing_entry.outcome = outcome

    new_entry_text = _format_entry_to_markdown(existing_entry)
    new_content = content[:match.start()] + new_entry_text + content[match.end():]

    _atomic_write(memory_path, new_content)
    logger.info(f"Updated memory entry for {market_ticker}")
    return True





def create_memory_file_if_missing() -> bool:
    """Create the memory file with header if it doesn't exist. Returns True if created."""
    memory_path = get_memory_path()
    
    if memory_path.exists():
        return False
    
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(_get_memory_header(), encoding="utf-8")
    logger.info(f"Created memory file: {memory_path}")
    return True
