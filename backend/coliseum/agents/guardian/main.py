"""Guardian Agent: Position monitoring and exit signal generation.

The Guardian agent monitors open positions and triggers exits based on:
- Profit targets (edge capture)
- Stop losses
- Time stops (approaching market close)
- News/event developments

When a position is closed, the Guardian updates the memory system with outcome data.
"""

import logging

from coliseum.storage.memory import TradeOutcome, update_entry

logger = logging.getLogger(__name__)


def close_position_and_update_memory(
    market_ticker: str,
    exit_price: float,
    pnl: float,
) -> bool:
    """Close a position and update the memory system with outcome data."""
    outcome = TradeOutcome(exit_price=exit_price, pnl=pnl)
    success = update_entry(market_ticker, status="CLOSED", outcome=outcome)
    
    if success:
        logger.info(f"Updated memory outcome for {market_ticker}: P&L ${pnl:.2f}")
    else:
        logger.warning(f"Failed to update memory outcome for {market_ticker}")
    
    return success


# TODO: Implement full Guardian agent with position monitoring loop
# The agent should:
# 1. Load open positions from state.yaml
# 2. Check current prices for each position
# 3. Compare against exit criteria (profit target, stop loss, time stop) from config
# 4. Generate exit signals and execute closing trades
# 5. Call close_position_and_update_memory() after each position close
