"""
BetRepository

MongoDB operations for the 'bets' collection (ledger).

Specialized Methods:
- create_bets_for_batch(bets): Batch insert betting decisions
- get_by_event(event_id): All bets for settlement calculation
- get_by_agent(agent_id, limit): Agent's recent bets
- update_settlement(bet_id, pnl, outcome): Mark bet as settled
- exists(agent_id, event_id, batch_id): Idempotency check
"""
