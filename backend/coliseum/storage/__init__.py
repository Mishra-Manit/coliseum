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
    DailyStats,
    Position,
    RiskStatus,
    load_state,
    save_state,
    get_data_dir,
)

# File operations
from .files import (
    OpportunitySignal,
    TradeExecution,
    save_opportunity,
    append_to_opportunity,
    load_opportunity_with_all_stages,
    get_opportunity_markdown_body,
    log_trade,
    generate_opportunity_id,
    generate_trade_id,
)


__all__ = [
    # State management
    "PortfolioState",
    "PortfolioStats",
    "DailyStats",
    "Position",
    "RiskStatus",
    "load_state",
    "save_state",
    "get_data_dir",
    # File operations
    "OpportunitySignal",
    "TradeExecution",
    "save_opportunity",
    "append_to_opportunity",
    "load_opportunity_with_all_stages",
    "get_opportunity_markdown_body",
    "log_trade",
    "generate_opportunity_id",
    "generate_trade_id",
]
