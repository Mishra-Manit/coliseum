"""
Settlement Tasks

Celery tasks for dynamic event settlement.

settle_event_task:
- Triggered 2 hours after event close_time
- Fetches outcome from Kalshi
- Calculates PnL for all bets
- Updates bankrolls atomically
- Retry: 5 attempts with exponential backoff
"""
