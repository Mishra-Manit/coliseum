"""Storage layer for Coliseum - file-based persistence and queuing.

This package provides:
- State management (load/save portfolio state from data/state.yaml)
- File operations (save opportunities, recommendations, trades to markdown/JSONL)
- Queue management (file-based job queue for agent communication)

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
    ResearchBrief,
    TradeRecommendation,
    TradeExecution,
    save_opportunity,
    save_research_brief,
    save_recommendation,
    log_trade,
    generate_opportunity_id,
    generate_research_id,
    generate_recommendation_id,
    generate_trade_id,
)

# Queue operations
from .queue import (
    QueueItem,
    queue_for_analyst,
    queue_for_trader,
    get_pending,
    dequeue,
    clear_queue,
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
    "ResearchBrief",
    "TradeRecommendation",
    "TradeExecution",
    "save_opportunity",
    "save_research_brief",
    "save_recommendation",
    "log_trade",
    "generate_opportunity_id",
    "generate_research_id",
    "generate_recommendation_id",
    "generate_trade_id",
    # Queue operations
    "QueueItem",
    "queue_for_analyst",
    "queue_for_trader",
    "get_pending",
    "dequeue",
    "clear_queue",
]
