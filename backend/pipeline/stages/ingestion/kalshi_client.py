"""
Kalshi API Client

Wrapper for Kalshi prediction market API.

Methods:
- get_active_events(close_within_hours=24): Paginated event fetch
- get_event_outcome(ticker): Settlement outcome lookup
- filter_events_by_timeframe(events): Keep only events closing within 24 hours

Error Handling:
- Raises ExternalAPIError on HTTP failures
- Implements retry with exponential backoff
"""
