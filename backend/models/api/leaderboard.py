"""
Leaderboard API Response Models

GET /api/leaderboard response schema.
Returns current agent rankings with on-demand calculation.

Response includes:
- updated_at: Timestamp of calculation
- agents: Array of ranked agents with:
  - id, name, model_slug, rank
  - current_bankroll, total_pnl, pnl_percent
  - stats (total_bets, wins, losses, abstentions, win_rate)
  - display_color
"""
