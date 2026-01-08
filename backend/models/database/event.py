"""
Event MongoDB Schema

Defines the Event document model for the 'events' collection.
Stores individual prediction market data and research.

Schema Fields:
- _id: ObjectId
- batch_id: Reference to daily_batches collection
- kalshi_ticker: Kalshi event identifier (e.g., "FED-RATE-JAN")
- title: Short display title
- question: Full question text
- resolution_criteria: How the event resolves
- category: LLM-classified category (politics, finance, sports, technology, other)
- kalshi_category: Original Kalshi category
- locked_price: YES price at time of selection (0-1)
- locked_at: Timestamp when price was locked
- close_time: When betting closes
- expected_resolution_time: close_time + 2 hours
- status: "open" | "waiting_settlement" | "settled"
- outcome: null | "YES" | "NO" | "VOID"
- settled_at: Settlement timestamp
- intelligence_brief: Full research text from Perplexity
- research_completed_at: Research completion timestamp
- created_at: Document creation timestamp

Indexes:
- batch_id
- kalshi_ticker (unique)
- status
- close_time
- category
"""

# TODO: Implement Pydantic models for Event schema
# TODO: Define status enum
# TODO: Define outcome enum
# TODO: Create index definitions
