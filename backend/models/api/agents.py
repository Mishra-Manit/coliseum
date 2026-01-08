"""
Agents API Response Models

GET /api/agents/{agent_id} - Agent profile with history

Response includes:
- Agent identity (name, model_slug, colors)
- Bankroll and PnL data
- Detailed stats (win_rate, best/worst category)
- recent_performance: Last 10 bets
- bankroll_history: Daily snapshots for charts
"""
