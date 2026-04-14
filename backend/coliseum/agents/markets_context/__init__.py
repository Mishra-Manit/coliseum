"""Market context package — re-exports the async reader as the primary interface."""

from coliseum.agents.markets_context.reader import get_market_type_context

__all__ = ["get_market_type_context"]
