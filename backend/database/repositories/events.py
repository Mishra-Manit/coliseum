"""
EventRepository

MongoDB operations for the 'events' collection.

Specialized Methods:
- create_events_for_batch(batch_id, events): Batch insert with transaction
- get_by_batch(batch_id): All events for a daily batch
- get_pending_settlement(): Events past close_time, not yet settled
- update_outcome(event_id, outcome, settled_at): Set settlement data
- get_by_category(category, limit): Filter by category
"""
