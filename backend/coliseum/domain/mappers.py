"""Centralized mapping between domain Pydantic models and SQLAlchemy ORM models."""

from datetime import datetime, timezone
from decimal import Decimal

from coliseum.domain.opportunity import OpportunitySignal
from coliseum.domain.portfolio import ClosedPosition, Position, PortfolioStats, PortfolioState
from coliseum.domain.trade import TradeClose, TradeExecution
from coliseum.services.supabase.models import (
    ClosedPosition as DBClosedPosition,
    OpenPosition as DBOpenPosition,
    Opportunity as DBOpportunity,
    OpportunityAnalysis as DBOpportunityAnalysis,
    PortfolioState as DBPortfolioState,
    Trade as DBTrade,
    TradeClose as DBTradeClose,
)


def to_decimal(v: float) -> Decimal:
    """Convert float to Decimal via string to avoid floating-point artifacts."""
    return Decimal(str(v))


def to_float(v: Decimal | None, default: float = 0.0) -> float:
    """Convert Decimal to float, with default for None."""
    if v is not None:
        return float(v)
    return default



def opportunity_to_db(
    opp: OpportunitySignal,
    *,
    paper: bool = False,
) -> tuple[DBOpportunity, DBOpportunityAnalysis]:
    """Convert domain OpportunitySignal to DB Opportunity + OpportunityAnalysis rows."""
    opp_row = DBOpportunity(
        id=opp.id,
        market_ticker=opp.market_ticker,
        event_ticker=opp.event_ticker,
        event_title=opp.event_title,
        market_title=opp.market_title,
        subtitle=opp.subtitle or None,
        yes_price=to_decimal(opp.yes_price),
        no_price=to_decimal(opp.no_price),
        close_time=opp.close_time,
        discovered_at=opp.discovered_at,
        status=opp.status,
        outcome_status=opp.outcome_status,
        risk_level=opp.risk_level,
        paper=paper,
    )

    analysis_row = DBOpportunityAnalysis(
        opportunity_id=opp.id,
        rationale=opp.rationale,
        resolution_source=opp.resolution_source or None,
        evidence_bullets=opp.evidence_bullets,
        remaining_risks=opp.remaining_risks,
        scout_sources=opp.scout_sources,
    )

    return opp_row, analysis_row


def db_to_opportunity(
    opp: DBOpportunity,
    analysis: DBOpportunityAnalysis | None,
) -> OpportunitySignal:
    """Convert DB Opportunity + optional OpportunityAnalysis to domain OpportunitySignal."""
    if analysis:
        rationale = analysis.rationale
        resolution_source = analysis.resolution_source or ""
        evidence_bullets = analysis.evidence_bullets
        remaining_risks = analysis.remaining_risks
        scout_sources = analysis.scout_sources
        research_duration_seconds = analysis.research_duration_seconds
        trader_tldr = analysis.trader_tldr or ""
    else:
        rationale = ""
        resolution_source = ""
        evidence_bullets = []
        remaining_risks = []
        scout_sources = []
        research_duration_seconds = None
        trader_tldr = ""

    return OpportunitySignal(
        id=opp.id,
        market_ticker=opp.market_ticker,
        event_ticker=opp.event_ticker,
        event_title=opp.event_title,
        market_title=opp.market_title,
        subtitle=opp.subtitle or "",
        yes_price=to_float(opp.yes_price),
        no_price=to_float(opp.no_price),
        close_time=opp.close_time,
        discovered_at=opp.discovered_at,
        status=opp.status,
        outcome_status=opp.outcome_status,
        risk_level=opp.risk_level,
        action=opp.action,
        trader_decision=opp.trader_decision or "",
        research_completed_at=opp.research_completed_at,
        recommendation_completed_at=opp.recommendation_completed_at,
        rationale=rationale,
        resolution_source=resolution_source,
        evidence_bullets=evidence_bullets,
        remaining_risks=remaining_risks,
        scout_sources=scout_sources,
        research_duration_seconds=research_duration_seconds,
        trader_tldr=trader_tldr,
    )



def position_to_db(pos: Position) -> DBOpenPosition:
    """Convert domain Position to DB OpenPosition row."""
    return DBOpenPosition(
        id=pos.id,
        market_ticker=pos.market_ticker,
        side=pos.side,
        contracts=pos.contracts,
        average_entry=to_decimal(pos.average_entry),
        current_price=to_decimal(pos.current_price),
        opportunity_id=pos.opportunity_id,
    )


def db_to_position(row: DBOpenPosition) -> Position:
    """Convert DB OpenPosition row to domain Position."""
    return Position(
        id=row.id,
        market_ticker=row.market_ticker,
        side=row.side,
        contracts=row.contracts,
        average_entry=to_float(row.average_entry),
        current_price=to_float(row.current_price),
        opportunity_id=row.opportunity_id,
    )



def closed_position_to_db(cp: ClosedPosition) -> DBClosedPosition:
    """Convert domain ClosedPosition to DB ClosedPosition row."""
    return DBClosedPosition(
        market_ticker=cp.market_ticker,
        side=cp.side,
        contracts=cp.contracts,
        entry_price=to_decimal(cp.entry_price),
        exit_price=to_decimal(cp.exit_price),
        pnl=to_decimal(cp.pnl),
        opportunity_id=cp.opportunity_id,
        closed_at=cp.closed_at,
        entry_rationale=cp.entry_rationale,
    )


def db_to_closed_position(row: DBClosedPosition) -> ClosedPosition:
    """Convert DB ClosedPosition row to domain ClosedPosition."""
    return ClosedPosition(
        market_ticker=row.market_ticker,
        side=row.side,
        contracts=row.contracts,
        entry_price=to_float(row.entry_price),
        exit_price=to_float(row.exit_price),
        pnl=to_float(row.pnl),
        opportunity_id=row.opportunity_id,
        closed_at=row.closed_at,
        entry_rationale=row.entry_rationale,
    )



def trade_to_db(trade: TradeExecution) -> DBTrade:
    """Convert domain TradeExecution to DB Trade row."""
    return DBTrade(
        id=trade.id,
        position_id=trade.position_id,
        opportunity_id=trade.opportunity_id,
        market_ticker=trade.market_ticker,
        side=trade.side,
        action=trade.action,
        contracts=trade.contracts,
        price=to_decimal(trade.price),
        total=to_decimal(trade.total),
        paper=trade.paper,
        executed_at=trade.executed_at,
    )


def trade_close_to_db(tc: TradeClose) -> DBTradeClose:
    """Convert domain TradeClose to DB TradeClose row."""
    return DBTradeClose(
        id=tc.id,
        opportunity_id=tc.opportunity_id,
        market_ticker=tc.market_ticker,
        side=tc.side,
        contracts=tc.contracts,
        entry_price=to_decimal(tc.entry_price),
        exit_price=to_decimal(tc.exit_price),
        pnl=to_decimal(tc.pnl),
        entry_rationale=tc.entry_rationale,
        closed_at=tc.closed_at,
    )



def portfolio_stats_to_db(
    cash_balance: float,
    positions_value: float,
    total_value: float,
) -> DBPortfolioState:
    """Convert portfolio values to the singleton DB PortfolioState row."""
    return DBPortfolioState(
        id=1,
        cash_balance=to_decimal(cash_balance),
        positions_value=to_decimal(positions_value),
        total_value=to_decimal(total_value),
        updated_at=datetime.now(timezone.utc),
    )


def db_to_portfolio_state(
    portfolio_row: DBPortfolioState | None,
    open_rows: list[DBOpenPosition],
    closed_rows: list[DBClosedPosition],
) -> PortfolioState:
    """Convert DB rows to a complete domain PortfolioState."""
    if portfolio_row is None:
        return PortfolioState(
            portfolio=PortfolioStats(total_value=0.0, cash_balance=0.0, positions_value=0.0),
            open_positions=[],
            closed_positions=[],
            seen_tickers=[],
        )

    stats = PortfolioStats(
        cash_balance=to_float(portfolio_row.cash_balance),
        positions_value=to_float(portfolio_row.positions_value),
        total_value=to_float(portfolio_row.total_value),
    )

    return PortfolioState(
        portfolio=stats,
        open_positions=[db_to_position(row) for row in open_rows],
        closed_positions=[db_to_closed_position(row) for row in closed_rows],
        seen_tickers=[],
    )
