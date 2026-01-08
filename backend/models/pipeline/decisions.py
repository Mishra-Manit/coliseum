"""
Pipeline Decision Models

Data classes for betting decisions and event data
used during pipeline execution.

Models:
- BetDecision: Agent's betting decision with reasoning
  - agent_id, event_id, decision, amount, confidence, reasoning
- EventData: Processed event data from ingestion
  - kalshi_ticker, title, question, category, locked_price, close_time
"""
