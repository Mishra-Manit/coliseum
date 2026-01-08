"""
Bet MongoDB Schema

Defines the Bet document model for the 'bets' collection.
Ledger of all betting actions by AI agents.

Schema Fields:
- _id: ObjectId
- batch_id: Reference to daily_batches
- agent_id: Reference to agents collection
- event_id: Reference to events collection
- decision: "YES" | "NO" | "ABSTAIN"
- amount_wagered: Dollar amount bet
- locked_price_at_bet: YES price when bet was placed
- reasoning_trace: Full AI reasoning text
- confidence: 0-100 confidence score
- status: "pending" | "settled"
- pnl: Calculated profit/loss after settlement
- outcome: "WIN" | "LOSS" | "VOID" | "ABSTAIN"
- created_at: Bet creation timestamp
- settled_at: Settlement timestamp

Indexes:
- batch_id
- agent_id
- event_id
- status
- Compound: (agent_id, created_at) for history queries
"""

# TODO: Implement Pydantic models for Bet schema
# TODO: Define decision enum
# TODO: Define outcome enum
# TODO: Create index definitions
