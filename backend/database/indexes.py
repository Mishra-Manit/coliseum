"""
MongoDB Index Definitions

Creates all required indexes on startup for performance.

Indexes by Collection:
- daily_batches: date (unique), status
- events: batch_id, kalshi_ticker (unique), status, close_time, category
- agents: model_slug (unique), current_bankroll
- bets: batch_id, agent_id, event_id, status, (agent_id, created_at) compound

Called from database/connection.py on application startup.
"""
