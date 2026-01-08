"""
Repository Pattern for MongoDB

Clean database abstraction layer providing:
- Testability with mock repositories
- Centralized query logic
- Transaction management in one place

Repositories:
- BaseRepository: Common CRUD operations
- AgentRepository: Agent-specific queries (leaderboard, history)
- EventRepository: Event queries with batch filtering
- BetRepository: Bet ledger queries with compound indexes
- DailyBatchRepository: Batch metadata queries
"""
