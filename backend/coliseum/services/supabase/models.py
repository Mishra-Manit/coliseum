"""SQLAlchemy ORM models mapping to the Supabase schema defined in online_db.md."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from coliseum.memory.enums import LearningCategory
from coliseum.services.supabase.db import Base

_category_values = ", ".join(f"'{v.value}'" for v in LearningCategory)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    market_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    event_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    event_title: Mapped[str] = mapped_column(Text, nullable=False)
    market_title: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    yes_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    no_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    close_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    outcome_status: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str | None] = mapped_column(Text, nullable=True)
    trader_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    recommendation_completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    paper: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class OpportunityAnalysis(Base):
    __tablename__ = "opportunity_analysis"

    opportunity_id: Mapped[str] = mapped_column(
        Text, ForeignKey("opportunities.id"), primary_key=True
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_bullets: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    remaining_risks: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    scout_sources: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    research_synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    trader_tldr: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class OpenPosition(Base):
    __tablename__ = "open_positions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    market_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    average_entry: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("opportunities.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class ClosedPosition(Base):
    __tablename__ = "closed_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    entry_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    position_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paper: Mapped[bool] = mapped_column(Boolean, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class TradeClose(Base):
    __tablename__ = "trade_closes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    opportunity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_ticker: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    entry_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class PortfolioState(Base):
    __tablename__ = "portfolio_state"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_portfolio_state_singleton"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text("1"))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    positions_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    positions_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    open_positions: Mapped[int] = mapped_column(Integer, nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class SeenTicker(Base):
    __tablename__ = "seen_tickers"

    ticker: Mapped[str] = mapped_column(Text, primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    tldr: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(Text, nullable=False)


class RunCycle(Base):
    __tablename__ = "run_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    guardian_synced: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    guardian_closed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    scout_scanned: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    scout_found: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    analyst_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trader_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cash_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    positions_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    open_positions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    errors: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )


class Learning(Base):
    __tablename__ = "learnings"
    __table_args__ = (
        CheckConstraint(
            f"category IN ({_category_values})",
            name="ck_learnings_category",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
