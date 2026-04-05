"""Storage layer for Coliseum - models and DB-backed persistence.

All operations use Pydantic models for type safety.
"""

from .state import (
    PortfolioState,
    PortfolioStats,
    Position,
    ClosedPosition,
    get_data_dir,
)

from .files import (
    OpportunitySignal,
    TradeExecution,
    TradeClose,
    generate_opportunity_id,
    generate_trade_id,
    generate_close_id,
)


__all__ = [
    # State models
    "PortfolioState",
    "PortfolioStats",
    "Position",
    "ClosedPosition",
    "get_data_dir",
    # File models and ID generators
    "OpportunitySignal",
    "TradeExecution",
    "TradeClose",
    "generate_opportunity_id",
    "generate_trade_id",
    "generate_close_id",
]
