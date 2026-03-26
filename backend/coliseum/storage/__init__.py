"""Storage layer for Coliseum - file-based persistence.

This package provides:
- State management (load/save portfolio state from data/state.yaml)
- File operations (save opportunities, trades to markdown/JSONL)

All operations use Pydantic models for type safety and atomic writes to prevent corruption.
"""

# State management
from .state import (
    PortfolioState,
    PortfolioStats,
    Position,
    load_state,
    save_state,
    get_data_dir,
)

# File operations
from .files import (
    OpportunitySignal,
    TradeExecution,
    TradeClose,
    save_opportunity,
    append_to_opportunity,
    get_opportunity_markdown_body,
    mark_opportunity_failed,
    log_trade,
    log_trade_close,
    generate_opportunity_id,
    generate_trade_id,
    generate_close_id,
)


__all__ = [
    # State management
    "PortfolioState",
    "PortfolioStats",
    "Position",
    "load_state",
    "save_state",
    "get_data_dir",
    # File operations
    "OpportunitySignal",
    "TradeExecution",
    "TradeClose",
    "save_opportunity",
    "append_to_opportunity",
    "get_opportunity_markdown_body",
    "mark_opportunity_failed",
    "log_trade",
    "log_trade_close",
    "generate_opportunity_id",
    "generate_trade_id",
    "generate_close_id",
]
