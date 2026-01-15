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

from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime


class BetDecision(BaseModel):
    """Agent's betting decision with reasoning.

    Attributes:
        agent_id: ID of the AI agent making the decision
        event_id: ID of the event being bet on
        decision: Betting decision (YES, NO, or ABSTAIN)
        amount: Dollar amount to bet (0 for ABSTAIN)
        confidence: Confidence level 0-1
        reasoning: Detailed explanation of the decision
    """
    agent_id: str = Field(description="ID of the AI agent")
    event_id: str = Field(description="ID of the event")
    decision: Literal["YES", "NO", "ABSTAIN"] = Field(
        description="Betting decision"
    )
    amount: float = Field(
        ge=0.0,
        description="Dollar amount to bet (0 for ABSTAIN)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)"
    )
    reasoning: str = Field(
        description="Detailed explanation of the decision"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "gpt-4o",
                "event_id": "TICKER-2026",
                "decision": "YES",
                "amount": 50.0,
                "confidence": 0.75,
                "reasoning": "Based on recent polling data and historical trends..."
            }
        }


class EventData(BaseModel):
    """Processed event data from ingestion.

    Attributes:
        kalshi_ticker: Kalshi market ticker symbol
        title: Event title
        question: Market question
        category: Event category
        locked_price: YES price at selection time
        close_time: When the market closes
    """
    kalshi_ticker: str = Field(description="Kalshi market ticker")
    title: str = Field(description="Event title")
    question: str = Field(description="Market question")
    category: str = Field(description="Event category")
    locked_price: float = Field(
        ge=0.0,
        le=1.0,
        description="YES price at selection time (0-1)"
    )
    close_time: datetime = Field(description="Market close time")

    class Config:
        json_schema_extra = {
            "example": {
                "kalshi_ticker": "PRES-2026",
                "title": "Presidential Election 2026",
                "question": "Will the Republican candidate win?",
                "category": "Politics",
                "locked_price": 0.52,
                "close_time": "2026-11-03T23:59:59Z"
            }
        }
