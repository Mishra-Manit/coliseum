"""
Agent MongoDB Schema

Defines the Agent document model for the 'agents' collection.
Represents competitor AI models in the prediction market simulation.

Schema Fields:
- _id: ObjectId (MongoDB auto-generated)
- name: Display name (e.g., "Claude-Opus")
- model_slug: OpenRouter format identifier (e.g., "anthropic/claude-3-opus")
- display_color: Hex color for UI (e.g., "#ff6b35")
- display_color_text: Text color for contrast (e.g., "#ffffff")
- avatar_initials: Two-letter avatar (e.g., "CO")
- current_bankroll: Current money balance (starts at $100,000)
- starting_bankroll: Initial balance ($100,000)
- total_pnl: Cumulative profit/loss
- stats: Nested object with performance metrics
  - total_bets, wins, losses, abstentions, win_rate
  - avg_bet_size, largest_win, largest_loss
- history: Array of historical trade records (grows forever)
- created_at, updated_at: Timestamps

Indexes:
- model_slug (unique)
- current_bankroll (for leaderboard sorting)
"""

# TODO: Implement Pydantic models for Agent schema
# TODO: Define embedded Stats model
# TODO: Define embedded HistoryEntry model
# TODO: Create index definitions
