"""
DailyBatchRepository

MongoDB operations for the 'daily_batches' collection.

Specialized Methods:
- get_by_date(date: str): Find batch for specific date (unique)
- exists_for_date(date: str): Idempotency check before ingestion
- update_status(batch_id, status): Transition batch state
- mark_completed(batch_id): Set completed_at timestamp
- get_recent(limit=10): Recent batches for history view
"""
