"""
Kalshi API Client

Wrapper for Kalshi prediction market API.

Methods:
- get_active_events(close_within_hours=48): Paginated event fetch
- get_event_outcome(ticker): Settlement outcome lookup
- filter_binary_markets(events): Keep only YES/NO markets

Error Handling:
- Raises ExternalAPIError on HTTP failures
- Implements retry with exponential backoff
"""
