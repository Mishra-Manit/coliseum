"""
IngestionStage Class

Main stage implementation for event ingestion (Stage 1).

Process:
1. API Scan - Query all active Kalshi events
2. Category Classification - LLM categorization into 5 categories
3. Multi-Factor Scoring - Volume, diversity, controversy
4. Hard Quota Selection - 2 Politics, 1 Finance, 1 Sports, 1 Wildcard
5. Price Locking - Record YES price at selection time

Outputs to pipeline_state:
- selected_events: List[EventData] (5 events)
- ingestion_metadata: Dict with events_scanned, quota_breakdown
"""
