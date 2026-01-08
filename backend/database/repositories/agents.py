"""
AgentRepository

MongoDB operations for the 'agents' collection.

Specialized Methods:
- get_leaderboard() -> List[Agent]: Sorted by current_bankroll DESC
- increment_bankroll(agent_id, amount): Atomic bankroll update
- append_history(agent_id, history_entry): Add trade to history
- get_recent_trades(agent_id, limit=5): Last N trades for context
- update_stats(agent_id, stats): Update performance statistics
"""
