"""
Outcome Fetcher

Fetches settlement outcomes from Kalshi API.

Methods:
- get_outcome(ticker): Returns YES | NO | VOID

Retry logic: 3 attempts with exponential backoff.
If still failing, retry every hour (max 24 hours).
"""
