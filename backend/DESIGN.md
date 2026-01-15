# Coliseum: Autonomous Quant Agent System

## Specification Document v2.0

---

## Executive Summary

**Coliseum** is an autonomous quantitative trading system that deploys AI agents to trade on Kalshi prediction markets. The system operates as a fully autonomous pipeline where specialized agents collaborate to research events, identify trading opportunities, execute positions, and continuously monitor the portfolio.

### Vision Statement
> *Build a self-sustaining AI trading system that can independently identify high-value prediction market opportunities, execute trades with disciplined risk management, and adapt to changing market conditions—all with minimal human intervention.*

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Autonomous Operation** | Agents run 24/7 with minimal human oversight |
| **Research-Driven** | Every trade is backed by deep, grounded research |
| **Risk-First** | Hard limits and circuit breakers prevent catastrophic losses |
| **Transparent** | Full audit trail of every decision and trade |
| **Adaptable** | Agents learn from outcomes and adjust strategies |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COLISEUM AUTONOMOUS TRADING SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌──────────────┐                                    ┌──────────────┐         │
│    │              │    Opportunities     ┌────────────▶│              │         │
│    │    SCOUT     │───────────────────▶  │             │   GUARDIAN   │         │
│    │    Agent     │                      │             │    Agent     │         │
│    │              │                      │             │              │         │
│    └──────┬───────┘                      │             └──────┬───────┘         │
│           │                              │                    │                 │
│           │ New Events                   │                    │ Exit Signals    │
│           ▼                              │                    ▼                 │
│    ┌──────────────┐                      │             ┌──────────────┐         │
│    │              │    Recommendations   │             │              │         │
│    │   ANALYST    │──────────────────────┼────────────▶│    TRADER    │         │
│    │    Agent     │                      │             │    Agent     │         │
│    │              │                      │             │              │         │
│    └──────────────┘                      │             └──────────────┘         │
│           │                              │                    │                 │
│           │                              │                    │                 │
│    ┌──────┴──────────────────────────────┴────────────────────┴──────┐          │
│    │                    LOCAL FILE STORAGE                           │          │
│    │         Markdown + YAML Files (Human-Readable & Git-Friendly)   │          │
│    └─────────────────────────────────────────────────────────────────┘          │
│           │                              │                    │                 │
│           ▼                              ▼                    ▼                 │
│    ┌─────────────────────────────────────────────────────────────────┐          │
│    │                       EXTERNAL SERVICES                         │          │
│    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │          │
│    │  │ Kalshi  │  │  Exa AI │  │Perplexity│ │  News   │             │          │
│    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘             │          │
│    └─────────────────────────────────────────────────────────────────┘          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```
Scout ──(NewOpportunity)──▶ Analyst ──(TradeRecommendation)──▶ Trader
                                                                   │
                                   ┌───────────────────────────────┘
                                   │
Guardian ◀──(OpenPosition)─────────┘
    │
    └──(ExitSignal)──▶ Trader ──(ClosePosition)──▶ Kalshi
```

---

## Technology Stack

### Core Framework

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Agent Framework** | PydanticAI | Type-safe agents with structured outputs |
| **Backend** | Python (CLI + optional FastAPI) | Agent execution, local operation |
| **Storage** | Markdown + YAML Files | Human-readable, git-friendly persistence |
| **State** | `state.yaml` | Single source of truth for portfolio state |
| **Scheduler** | APScheduler | In-process scheduled jobs |
| **Observability** | Pydantic Logfire | LLM tracing, performance monitoring |

### AI/ML Services

| Service | Provider | Use Case |
|---------|----------|----------|
| **Primary LLM** | Anthropic (Claude Sonnet 4) | Agent reasoning, analysis |
| **Fast LLM** | Anthropic (Claude Haiku) | Quick decisions, monitoring |
| **Deep Reasoning** | Anthropic (Claude Opus 4) | Complex analysis (optional) |
| **Grounded Search** | Exa AI | Research with citations |
| **Real-time Search** | Perplexity API | Breaking news, current events |

### External APIs

| API | Purpose | Authentication |
|-----|---------|----------------|
| **Kalshi Markets** | Read market data | API Key (public endpoints) |
| **Kalshi Trading** | Execute trades | API Key + Private Key (member API) |
| **Exa AI** | Grounded web research | API Key |
| **Perplexity** | Real-time information | API Key |

---

## Agent Specifications

### 1. Scout Agent 🔍

**Mission**: Continuously discover and filter high-quality trading opportunities from Kalshi markets.

#### Responsibilities
- Scan Kalshi API for new/updated events
- Filter events by liquidity, volume, and close time
- Categorize events by topic (politics, crypto, sports, etc.)
- Identify events suitable for research
- Push qualified opportunities to Analyst queue

#### Configuration

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import Literal
from datetime import datetime

class ScoutConfig(BaseModel):
    """Scout agent configuration"""
    min_volume: int = 10_000  # Minimum contracts traded
    min_liquidity: float = 0.05  # Minimum bid-ask spread tolerance
    max_close_hours: int = 72  # Events closing within N hours
    scan_interval_minutes: int = 60  # How often to scan
    max_opportunities_per_scan: int = 20
    
class OpportunitySignal(BaseModel):
    """Output from Scout agent"""
    event_ticker: str
    market_ticker: str
    title: str
    category: str
    yes_price: float = Field(ge=0, le=1)
    no_price: float = Field(ge=0, le=1)
    volume_24h: int
    close_time: datetime
    priority: Literal["high", "medium", "low"]
    rationale: str  # Why this opportunity is interesting
```

#### Execution Schedule
- **Full Scan**: Every 60 minutes
- **Quick Scan**: Every 15 minutes (high-volume events only)
- **Trigger**: Celery Beat scheduled task

#### Tools Available
| Tool | Description |
|------|-------------|
| `get_kalshi_events` | Fetch events from Kalshi API |
| `get_event_markets` | Get markets for specific event |
| `check_event_liquidity` | Analyze bid/ask spreads |
| `categorize_event` | LLM-based topic classification |

---

### 2. Analyst Agent 📊

**Mission**: Conduct deep research on opportunities and produce actionable trade recommendations.

#### Responsibilities
- Receive opportunities from Scout
- Conduct comprehensive research using Exa AI
- **Execute Devil's Advocate Loop (Pro vs. Con)**
- Analyze historical data and precedents
- Synthesize findings to calculate expected value and edge
- Generate trade recommendations with confidence scores
- Document reasoning for audit trail

#### Configuration

```python
class AnalystConfig(BaseModel):
    """Analyst agent configuration"""
    research_depth: Literal["quick", "standard", "deep"] = "standard"
    min_confidence_threshold: float = 0.6  # Don't recommend below this
    max_research_time_seconds: int = 300  # 5 minute timeout
    required_sources: int = 3  # Minimum sources for recommendation
    
class ResearchBrief(BaseModel):
    """Structured research output"""
    event_ticker: str
    market_ticker: str
    
    # Research findings
    key_facts: list[str]
    recent_developments: list[str]
    expert_opinions: list[str]
    historical_precedents: list[str]
    sources: list[str]  # URLs with citations
    
    # Analysis
    base_rate: float | None  # Historical probability if available
    current_sentiment: Literal["bullish", "bearish", "neutral"]
    information_quality: Literal["high", "medium", "low"]
    
class TradeRecommendation(BaseModel):
    """Output from Analyst agent"""
    event_ticker: str
    market_ticker: str
    
    # Recommendation
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"]
    confidence: float = Field(ge=0, le=1)
    
    # Edge calculation
    estimated_true_probability: float = Field(ge=0, le=1)
    current_market_price: float = Field(ge=0, le=1)
    expected_value: float  # EV per dollar risked
    edge: float  # True prob - market prob
    
    # Research backing
    research_brief: ResearchBrief
    reasoning: str
    key_risks: list[str]
    
    # Suggested sizing
    suggested_position_pct: float = Field(ge=0, le=0.10)  # Max 10% of bankroll
```

#### Research Workflow

```
1. Receive Opportunity from Scout
           │
           ▼
2. Initial Research (Facts & Data Collection)
           │
           ▼
3. DEBATE PHASE
   ├─ Analyst (PRO): Generates Bull Case (Why YES?)
   │
   ├─ Analyst (CON): Generates Bear Case (Why NO/Risks?)
   │                 (Explicitly tasked to destroy the Bull case)
           │
           ▼
4. Synthesis & Verdict
   (Weighs Pro/Con, assigns final confidence score)
           │
           ▼
5. Calculate Edge & Expected Value
           │
           ▼
6. Generate Trade Recommendation
           │
           ▼
7. Store in Database + Push to Trader Queue
```

#### Tools Available
| Tool | Description |
|------|-------------|
| `exa_search` | Grounded web search with citations |
| `exa_answer` | Question answering with sources |
| `perplexity_search` | Real-time news search |
| `get_historical_data` | Query internal database for precedents |
| `calculate_expected_value` | EV calculation helper |

---

### 3. Trader Agent 💰

**Mission**: Execute trades with disciplined risk management and optimal position sizing.

#### Responsibilities
- Receive recommendations from Analyst
- Validate recommendations against risk rules
- Calculate optimal position size (Kelly Criterion)
- Execute orders via Kalshi Trading API
- Record all trades with full audit trail
- Handle order failures and retries

#### Configuration

```python
class TraderConfig(BaseModel):
    """Trader agent configuration"""
    # Risk limits
    max_position_pct: float = 0.10  # Max 10% bankroll per position
    max_daily_loss_pct: float = 0.05  # Stop trading if down 5% in a day
    max_open_positions: int = 10  # Maximum concurrent positions
    max_single_trade_usd: float = 1000  # Hard cap per trade
    
    # Execution
    min_edge_threshold: float = 0.05  # Only trade if edge > 5%
    min_ev_threshold: float = 0.10  # Only trade if EV > 10%
    use_kelly_sizing: bool = True
    kelly_fraction: float = 0.25  # Use fractional Kelly (1/4)
    
    # Safety
    require_human_approval_above: float = 500  # Manual approval for large trades
    paper_trading_mode: bool = True  # Start in paper trading!
    
class TradeExecution(BaseModel):
    """Trade execution record"""
    id: str  # UUID
    
    # Position details
    event_ticker: str
    market_ticker: str
    side: Literal["YES", "NO"]
    
    # Sizing
    contracts: int
    price_per_contract: float
    total_cost: float
    
    # Execution
    order_id: str | None  # Kalshi order ID
    status: Literal["pending", "filled", "partial", "failed", "cancelled"]
    
    # Risk metrics at entry
    portfolio_pct: float  # What % of bankroll this represents
    edge_at_entry: float
    ev_at_entry: float
    
    # Audit
    recommendation_id: str  # Link to TradeRecommendation
    executed_at: datetime
    reasoning: str
```

#### Risk Management Rules

```python
class RiskManager:
    """Enforces risk limits before every trade"""
    
    def validate_trade(self, trade: TradeExecution, portfolio: Portfolio) -> bool:
        checks = [
            self._check_position_limit(trade, portfolio),
            self._check_daily_loss(portfolio),
            self._check_open_positions(portfolio),
            self._check_single_trade_cap(trade),
            self._check_edge_threshold(trade),
            self._check_ev_threshold(trade),
        ]
        return all(checks)
    
    def calculate_kelly_size(
        self,
        win_probability: float,
        win_payout: float,  # Net profit if win
        loss_amount: float,  # Amount lost if lose
        fraction: float = 0.25  # Fractional Kelly
    ) -> float:
        """
        Kelly Criterion: f* = (bp - q) / b
        Where:
          b = odds received on the bet (win_payout / loss_amount)
          p = probability of winning
          q = probability of losing (1 - p)
        """
        b = win_payout / loss_amount
        p = win_probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        return max(0, kelly * fraction)  # Fractional Kelly, never negative
```

#### Execution Flow

```
1. Receive TradeRecommendation
           │
           ▼
2. Risk Manager Validation ──(FAIL)──▶ Log & Reject
           │
           │ (PASS)
           ▼
3. Calculate Position Size (Kelly)
           │
           ▼
4. Check if Human Approval Required ──(YES)──▶ Queue for Approval
           │
           │ (NO)
           ▼
5. Execute Order via Kalshi API
           │
           ▼
6. Record Trade in Database
           │
           ▼
7. Notify Guardian Agent of New Position
```

#### Order Execution Strategy

> **Critical**: Never use market orders. All trades must be executed via limit orders with liquidity-aware sizing to prevent slippage from destroying edge.

##### Order Book Depth Model

```python
class OrderBookLevel(BaseModel):
    """Single price level in order book"""
    price: float = Field(ge=0, le=1)
    contracts_available: int = Field(ge=0)
    
class OrderBookDepth(BaseModel):
    """Order book snapshot for a market"""
    market_ticker: str
    timestamp: datetime
    
    # Best bid/ask
    best_bid: float
    best_ask: float
    spread: float  # best_ask - best_bid
    
    # Depth on each side
    yes_bids: list[OrderBookLevel]  # Sorted by price descending
    yes_asks: list[OrderBookLevel]  # Sorted by price ascending
    no_bids: list[OrderBookLevel]
    no_asks: list[OrderBookLevel]
    
    # Aggregate liquidity
    total_yes_bid_depth: int  # Total contracts on bid side
    total_yes_ask_depth: int  # Total contracts on ask side
    
class SlippageEstimate(BaseModel):
    """Estimated fill quality for a given order size"""
    contracts_requested: int
    contracts_fillable: int  # How many can fill at acceptable price
    
    best_price: float  # Price of first contract
    worst_price: float  # Price of last contract (if sweeping)
    average_fill_price: float  # Volume-weighted average
    
    slippage_cents: float  # avg_fill - best_price
    slippage_pct: float  # slippage as % of best price
    
    edge_after_slippage: float  # Recalculated edge
    ev_after_slippage: float  # Recalculated EV
    still_tradeable: bool  # Edge > threshold after slippage?
```

##### Slippage-Adjusted Edge Filter

Before executing any trade, the Trader MUST:

1. **Fetch order book depth** for the target market
2. **Simulate the fill** at the desired contract count
3. **Recalculate edge** using average fill price (not best price)
4. **Reject trade** if edge drops below `min_edge_threshold` after slippage

```python
def calculate_slippage(
    order_book: OrderBookDepth,
    side: Literal["YES", "NO"],
    contracts: int,
    max_price: float  # Won't pay more than this
) -> SlippageEstimate:
    """
    Walk the order book to estimate fill quality.
    Returns slippage estimate with adjusted edge/EV.
    """
    if side == "YES":
        levels = order_book.yes_asks  # Buying YES = lifting asks
    else:
        levels = order_book.no_asks
    
    filled = 0
    total_cost = 0.0
    worst_price = 0.0
    
    for level in levels:
        if level.price > max_price:
            break  # Won't pay above our limit
            
        take = min(level.contracts_available, contracts - filled)
        filled += take
        total_cost += take * level.price
        worst_price = level.price
        
        if filled >= contracts:
            break
    
    avg_price = total_cost / filled if filled > 0 else 0
    best_price = levels[0].price if levels else 0
    
    return SlippageEstimate(
        contracts_requested=contracts,
        contracts_fillable=filled,
        best_price=best_price,
        worst_price=worst_price,
        average_fill_price=avg_price,
        slippage_cents=avg_price - best_price,
        slippage_pct=(avg_price - best_price) / best_price if best_price > 0 else 0,
        edge_after_slippage=estimated_true_prob - avg_price,
        ev_after_slippage=calculate_ev(estimated_true_prob, avg_price),
        still_tradeable=edge_after_slippage > config.min_edge_threshold
    )
```

##### Liquidity-Aware Position Sizing

The Trader adjusts position size based on available liquidity:

```python
def size_with_liquidity(
    kelly_contracts: int,
    order_book: OrderBookDepth,
    side: Literal["YES", "NO"],
    max_price: float,
    max_slippage_pct: float = 0.05  # Max 5% slippage
) -> int:
    """
    Reduce position size if order book can't support it
    without excessive slippage.
    """
    slippage = calculate_slippage(order_book, side, kelly_contracts, max_price)
    
    # If slippage is acceptable, use full size
    if slippage.slippage_pct <= max_slippage_pct:
        return kelly_contracts
    
    # Binary search for max size with acceptable slippage
    low, high = 1, kelly_contracts
    best_size = 0
    
    while low <= high:
        mid = (low + high) // 2
        est = calculate_slippage(order_book, side, mid, max_price)
        
        if est.slippage_pct <= max_slippage_pct:
            best_size = mid
            low = mid + 1
        else:
            high = mid - 1
    
    return best_size
```

##### Order Execution State Machine

The Trader uses a **"Work the Order"** approach rather than fire-and-forget:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORDER EXECUTION STATE MACHINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐                                                        │
│   │   INITIALIZED   │  Order created but not yet submitted                   │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────┐                                                        │
│   │  PLACED_LIMIT   │  Limit order submitted to Kalshi                       │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│            ├───────────────────────────────────────────────────┐             │
│            │ Wait 5 minutes                                    │             │
│            ▼                                                   │             │
│   ┌─────────────────┐                                          │             │
│   │  CHECK_STATUS   │  Poll Kalshi for fill status             │             │
│   └────────┬────────┘                                          │             │
│            │                                                   │             │
│            ├─────────(FILLED)────────────────┐                 │             │
│            │                                 ▼                 │             │
│            │                        ┌─────────────────┐        │             │
│            │                        │    COMPLETED    │────────┴────▶ EXIT   │
│            │                        └─────────────────┘                      │
│            │                                                                 │
│            ├─────────(PARTIAL)───────────────┐                               │
│            │                                 ▼                               │
│            │                        ┌─────────────────┐                      │
│            │                        │ PARTIAL_FILLED  │                      │
│            │                        └────────┬────────┘                      │
│            │                                 │                               │
│            │                    ┌────────────┴────────────┐                  │
│            │                    ▼                         ▼                  │
│            │           ┌──────────────┐          ┌──────────────┐            │
│            │           │ ACCEPT_PARTIAL│         │ REPRICE_REMAINING│        │
│            │           │ (book filled) │         │ (still edge)     │        │
│            │           └──────────────┘          └──────────────┘            │
│            │                                                                 │
│            ├─────────(UNFILLED)──────────────┐                               │
│            │                                 ▼                               │
│            │                        ┌─────────────────┐                      │
│            │                        │  EVALUATE_REPRICE│                     │
│            │                        └────────┬────────┘                      │
│            │                                 │                               │
│            │                    ┌────────────┴────────────┐                  │
│            │                    ▼                         ▼                  │
│            │           ┌──────────────┐          ┌──────────────┐            │
│            │           │   REPRICE    │          │    CANCEL    │            │
│            │           │ (edge exists)│          │ (no edge)    │            │
│            │           └──────┬───────┘          └──────────────┘            │
│            │                  │                                              │
│            │                  └──────────────────▶ PLACED_LIMIT (loop)       │
│            │                                                                 │
│            └─────────(TIMEOUT: 3 cycles)─────────▶ CANCEL + LOG              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Order Execution Model

```python
class OrderState(str, Enum):
    INITIALIZED = "initialized"
    PLACED_LIMIT = "placed_limit"
    PARTIAL_FILLED = "partial_filled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class WorkingOrder(BaseModel):
    """Tracks an order through the execution loop"""
    id: str  # UUID
    recommendation_id: str
    
    # Order details
    market_ticker: str
    side: Literal["YES", "NO"]
    target_contracts: int
    max_price: float  # Will not pay above this
    
    # Execution state
    state: OrderState
    kalshi_order_id: str | None
    
    # Fill tracking
    contracts_filled: int = 0
    average_fill_price: float = 0.0
    total_cost: float = 0.0
    
    # Loop tracking
    reprice_count: int = 0
    max_reprice_attempts: int = 3
    last_check_at: datetime | None
    check_interval_seconds: int = 300  # 5 minutes
    
    # Audit
    created_at: datetime
    completed_at: datetime | None
    state_history: list[tuple[datetime, OrderState, str]]  # timestamp, state, reason
```

##### Execution Configuration

```python
class ExecutionConfig(BaseModel):
    """Order execution settings"""
    # Order type
    use_limit_orders_only: bool = True  # NEVER set to False
    
    # Slippage tolerance
    max_slippage_pct: float = 0.05  # Cancel if avg fill > 5% worse than best
    
    # Working order settings
    order_check_interval_seconds: int = 300  # Check fill status every 5 min
    max_reprice_attempts: int = 3  # Give up after 3 reprice cycles
    reprice_aggression: float = 0.02  # Increase limit by 2 cents each reprice
    
    # Partial fill handling
    min_fill_pct_to_keep: float = 0.25  # Keep partial if > 25% filled
    
    # Timeouts
    max_order_age_minutes: int = 60  # Cancel if order open > 1 hour
```

#### Updated Execution Flow

```
1. Receive TradeRecommendation
           │
           ▼
2. Risk Manager Validation ──(FAIL)──▶ Log & Reject
           │
           │ (PASS)
           ▼
3. Calculate Kelly Position Size
           │
           ▼
4. Fetch Order Book Depth ◀────────────────────────────────┐
           │                                                │
           ▼                                                │
5. Calculate Slippage Estimate                              │
           │                                                │
           ├──(Edge destroyed by slippage)──▶ Log & Reject  │
           │                                                │
           │ (Edge survives)                                │
           ▼                                                │
6. Adjust Size for Liquidity                                │
           │                                                │
           ▼                                                │
7. Check if Human Approval Required ──(YES)──▶ Queue        │
           │                                                │
           │ (NO)                                           │
           ▼                                                │
8. Place LIMIT Order at max_price                           │
           │                                                │
           ▼                                                │
9. Enter Working Order Loop ─────────────────────────────────
           │
           ▼ (on fill)
10. Record Trade in Ledger
           │
           ▼
11. Notify Guardian of New Position
           │
           ▼
12. Send Telegram Alert
```

#### Tools Available
| Tool | Description |
|------|-------------|
| `get_portfolio_state` | Current positions and P&L |
| `get_order_book_depth` | Fetch bid/ask levels with contract counts |
| `calculate_slippage` | Simulate order fill and estimate avg price |
| `calculate_position_size` | Kelly criterion with liquidity adjustment |
| `place_limit_order` | Submit limit order to Kalshi (never market) |
| `cancel_order` | Cancel pending/partial order |
| `check_order_status` | Poll order fill status |
| `reprice_order` | Cancel and replace at new limit price |

---

### 4. Guardian Agent 🛡️

**Mission**: Continuously monitor open positions and market conditions; recommend exits when warranted.

#### Responsibilities
- Monitor all open positions in real-time
- Track relevant news and market shifts
- Detect adverse changes in thesis
- Calculate exit recommendations
- Alert on significant portfolio events
- Trigger Trader to close positions when needed

#### Configuration

```python
class GuardianConfig(BaseModel):
    """Guardian agent configuration"""
    # Monitoring frequency
    position_check_interval_minutes: int = 15
    news_scan_interval_minutes: int = 30
    
    # Exit triggers
    profit_target_pct: float = 0.50  # Take profit at 50% gain
    stop_loss_pct: float = 0.30  # Cut loss at 30% down
    thesis_invalidation_threshold: float = 0.7  # Confidence drop threshold
    
    # Alerts
    alert_on_position_change_pct: float = 0.10  # Alert if position moves 10%
    
class PositionHealth(BaseModel):
    """Guardian's assessment of a position"""
    position_id: str
    event_ticker: str
    market_ticker: str
    
    # Current state
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
    # Thesis assessment
    thesis_still_valid: bool
    current_confidence: float
    original_confidence: float
    
    # News/Events
    relevant_news: list[str]
    sentiment_shift: Literal["positive", "negative", "neutral"]
    
    # Recommendation
    action: Literal["HOLD", "CLOSE", "ADD", "REDUCE"]
    urgency: Literal["immediate", "soon", "monitor"]
    reasoning: str
    
class ExitSignal(BaseModel):
    """Signal from Guardian to Trader"""
    position_id: str
    action: Literal["CLOSE_FULL", "CLOSE_PARTIAL", "HOLD"]
    
    # If partial
    close_percentage: float = 1.0  # 1.0 = full close
    
    # Justification
    trigger: Literal[
        "profit_target",
        "stop_loss", 
        "thesis_invalidation",
        "time_decay",
        "manual_override"
    ]
    reasoning: str
    urgency: Literal["immediate", "next_cycle"]
```

#### Monitoring Loop

```
┌───────────────────────────────────────────────────────────────┐
│                    GUARDIAN MONITORING LOOP                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Every 15 minutes:                                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ For each open position:                                  │ │
│  │   1. Fetch current market price                          │ │
│  │   2. Calculate P&L                                       │ │
│  │   3. Check profit target / stop loss                     │ │
│  │   4. Scan for relevant news (if threshold hit)           │ │
│  │   5. Re-assess thesis validity                           │ │
│  │   6. Generate PositionHealth report                      │ │
│  │   7. If action != HOLD → Send ExitSignal to Trader       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  Every 30 minutes:                                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1. Scan news for all position-related topics             │ │
│  │ 2. Detect market-wide sentiment shifts                   │ │
│  │ 3. Generate portfolio-level risk assessment              │ │
│  │ 4. Alert if significant changes detected                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

#### Tools Available
| Tool | Description |
|------|-------------|
| `get_open_positions` | Fetch all active positions |
| `get_current_prices` | Real-time market prices |
| `search_news` | Search for position-relevant news |
| `assess_thesis` | LLM re-evaluation of original thesis |
| `send_exit_signal` | Push close recommendation to Trader |
| `send_alert` | Notify admin of important events |

---

## File Storage Structure

### Overview

All data is stored in the `data/` directory as human-readable Markdown and YAML files. This approach provides:

- **Git-friendly**: Track all changes with version control
- **Human-readable**: Browse and edit files directly
- **Simple backup**: Copy the folder to back up everything
- **No database setup**: Zero configuration required

### Directory Layout

```
data/
├── config.yaml                    # System configuration
├── state.yaml                     # Current portfolio state (single source of truth)
│
├── opportunities/                 # Discovered by Scout
│   └── 2025-01-14/
│       ├── TICKER-ABC-123.md
│       └── TICKER-XYZ-456.md
│
├── research/                      # Generated by Analyst
│   └── 2025-01-14/
│       ├── TICKER-ABC-123.md
│       └── TICKER-XYZ-456.md
│
├── recommendations/               # Trade recommendations from Analyst
│   └── 2025-01-14/
│       ├── TICKER-ABC-123.md
│       └── TICKER-XYZ-456.md
│
├── positions/                     # Active and closed positions
│   ├── open/
│   │   └── TICKER-ABC-123.yaml
│   └── closed/
│       └── 2025-01-14/
│           └── TICKER-XYZ-456.yaml
│
├── trades/                        # Append-only trade ledger
│   └── 2025-01-14.jsonl           # JSON Lines format for easy parsing
│
├── alerts/                        # System alerts and notifications
│   └── 2025-01-14.md              # Daily alert log
│
└── snapshots/                     # Daily portfolio snapshots
    └── 2025-01-14.yaml
```

---

### File Formats

#### `config.yaml` - System Configuration

```yaml
# config.yaml
trading:
  paper_mode: true
  initial_bankroll: 10000.00
  
risk:
  max_position_pct: 0.10          # Max 10% per position
  max_daily_loss_pct: 0.05        # Stop trading if down 5%
  max_open_positions: 10
  max_single_trade_usd: 1000.00
  min_edge_threshold: 0.05        # Only trade if edge > 5%
  min_ev_threshold: 0.10          # Only trade if EV > 10%
  kelly_fraction: 0.25            # Use 1/4 Kelly
  
scheduler:
  scout_full_scan_minutes: 60
  scout_quick_scan_minutes: 15
  guardian_position_check_minutes: 15
  guardian_news_scan_minutes: 30
  
analyst:
  research_depth: standard        # quick, standard, deep
  min_confidence_threshold: 0.6
  max_research_time_seconds: 300
  required_sources: 3
  
guardian:
  profit_target_pct: 0.50         # Take profit at 50%
  stop_loss_pct: 0.30             # Cut loss at 30%
  
execution:
  use_limit_orders_only: true     # NEVER set to false
  max_slippage_pct: 0.05          # Reject trade if slippage > 5%
  order_check_interval_seconds: 300  # Check fill status every 5 min
  max_reprice_attempts: 3         # Give up after 3 reprice cycles
  reprice_aggression: 0.02        # Increase limit by 2 cents each reprice
  min_fill_pct_to_keep: 0.25      # Keep partial if > 25% filled
  max_order_age_minutes: 60       # Cancel if order open > 1 hour
```

---

#### `state.yaml` - Current Portfolio State

This is the **single source of truth** for the current system state.

```yaml
# state.yaml
last_updated: "2025-01-14T15:30:00Z"

portfolio:
  total_value: 10250.00
  cash_balance: 8500.00
  positions_value: 1750.00
  
daily_stats:
  date: "2025-01-14"
  starting_value: 10000.00
  current_pnl: 250.00
  current_pnl_pct: 0.025
  trades_today: 2
  
open_positions:
  - id: "pos_abc123"
    market_ticker: "TICKER-ABC-123"
    side: "YES"
    contracts: 50
    average_entry: 0.65
    current_price: 0.70
    unrealized_pnl: 2.50
    
risk_status:
  daily_loss_limit_hit: false
  trading_halted: false
  capital_at_risk_pct: 0.175
```

---

#### Opportunity File (`opportunities/YYYY-MM-DD/TICKER.md`)

```markdown
---
id: opp_abc123
event_ticker: EVENT-ABC
market_ticker: TICKER-ABC-123
status: pending  # pending, researching, recommended, traded, expired, skipped
priority: high
discovered_at: "2025-01-14T10:00:00Z"
close_time: "2025-01-16T20:00:00Z"
yes_price: 0.45
no_price: 0.55
volume_24h: 15000
category: politics
---

# Will X happen by Y date?

## Scout Assessment

**Priority**: High

**Rationale**: This market shows significant volume with a 10-cent spread, suggesting 
potential for price discovery. Recent news suggests the market may be mispriced.

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | $0.45 |
| No Price | $0.55 |
| 24h Volume | 15,000 |
| Closes | 2025-01-16 8:00 PM |
```

---

#### Research Brief (`research/YYYY-MM-DD/TICKER.md`)

```markdown
---
id: research_abc123
opportunity_id: opp_abc123
event_ticker: EVENT-ABC
market_ticker: TICKER-ABC-123
research_depth: standard
model_used: claude-sonnet-4-20250514
tokens_used: 4500
research_duration_seconds: 45
created_at: "2025-01-14T10:05:00Z"
base_rate: 0.60
sentiment: bullish
information_quality: high
---

# Research: Will X happen by Y date?

## Key Facts

1. Historical data shows X has occurred 60% of the time under similar conditions
2. Recent announcement by Z suggests increased likelihood
3. Expert consensus has shifted in the past week

## Recent Developments

- [2025-01-13] Major announcement from relevant authority
- [2025-01-12] Market reaction to related event
- [2025-01-10] Initial catalyst event occurred

## Expert Opinions

> "Based on our analysis, we expect a 65% probability..." - Expert A, Source 1

> "The market appears to be underpricing this outcome..." - Expert B, Source 2

## Historical Precedents

- Similar situation in 2024 resolved YES (70% of cases)
- Comparable market in 2023 had similar pricing before resolution

## Sources

1. [Source Title 1](https://example.com/source1) - Published 2025-01-13
2. [Source Title 2](https://example.com/source2) - Published 2025-01-12
3. [Source Title 3](https://example.com/source3) - Published 2025-01-10
```

---

#### Trade Recommendation (`recommendations/YYYY-MM-DD/TICKER.md`)

```markdown
---
id: rec_abc123
opportunity_id: opp_abc123
research_brief_id: research_abc123
event_ticker: EVENT-ABC
market_ticker: TICKER-ABC-123
action: BUY_YES  # BUY_YES, BUY_NO, ABSTAIN
status: pending  # pending, approved, executed, rejected, expired
confidence: 0.72
estimated_true_probability: 0.65
current_market_price: 0.45
expected_value: 0.44  # (0.65 * 1.22) - 1 where 1.22 = 1/0.45 - 1
edge: 0.20  # 0.65 - 0.45
suggested_position_pct: 0.05
model_used: claude-sonnet-4-20250514
created_at: "2025-01-14T10:10:00Z"
executed_at: null
---

# Trade Recommendation: BUY YES on TICKER-ABC-123

## Summary

| Metric | Value |
|--------|-------|
| **Action** | BUY YES |
| **Confidence** | 72% |
| **Edge** | +20% |
| **Expected Value** | +44% |
| **Suggested Size** | 5% of portfolio |

## Reasoning

Based on the research, the true probability of YES is estimated at **65%**, while the 
market is pricing YES at only **45%**. This represents a significant edge of 20 percentage 
points.

The research quality is high with 3 corroborating sources, and the base rate analysis 
supports our probability estimate.

## Key Risks

1. **Time decay**: Event closes in 48 hours - limited time for thesis to play out
2. **News sensitivity**: Unexpected announcements could shift odds quickly
3. **Liquidity**: Spread may widen if we try to exit quickly

## Position Sizing

Using 1/4 Kelly with 72% confidence:
- Kelly optimal: ~20% of bankroll
- Fractional (1/4): 5% of bankroll
- Suggested contracts: 50 at $0.45 = $22.50 cost
```

---

#### Position File (`positions/open/TICKER.yaml`)

```yaml
# positions/open/TICKER-ABC-123.yaml
id: pos_abc123
recommendation_id: rec_abc123

# Market info
event_ticker: EVENT-ABC
market_ticker: TICKER-ABC-123
side: YES

# Position details
contracts: 50
average_entry_price: 0.45
total_cost: 22.50

# Current state (updated by Guardian)
current_price: 0.52
unrealized_pnl: 3.50
unrealized_pnl_pct: 0.156

# Entry metrics
edge_at_entry: 0.20
ev_at_entry: 0.44
portfolio_pct_at_entry: 0.05

# Timestamps
opened_at: "2025-01-14T10:15:00Z"
last_checked: "2025-01-14T15:30:00Z"

# Guardian assessment
thesis_still_valid: true
current_confidence: 0.75
```

---

#### Trade Ledger (`trades/YYYY-MM-DD.jsonl`)

JSON Lines format for easy appending and parsing:

```jsonl
{"id":"trade_001","position_id":"pos_abc123","recommendation_id":"rec_abc123","market_ticker":"TICKER-ABC-123","side":"YES","action":"BUY","contracts":50,"price":0.45,"total":22.50,"portfolio_pct":0.05,"edge":0.20,"ev":0.44,"paper":true,"executed_at":"2025-01-14T10:15:00Z"}
{"id":"trade_002","position_id":"pos_xyz456","recommendation_id":"rec_xyz456","market_ticker":"TICKER-XYZ-456","side":"NO","action":"BUY","contracts":30,"price":0.60,"total":18.00,"portfolio_pct":0.04,"edge":0.15,"ev":0.25,"paper":true,"executed_at":"2025-01-14T11:30:00Z"}
```

---

#### Daily Snapshot (`snapshots/YYYY-MM-DD.yaml`)

```yaml
# snapshots/2025-01-14.yaml
snapshot_date: "2025-01-14"
created_at: "2025-01-14T16:00:00Z"

portfolio:
  total_value: 10250.00
  cash_balance: 8500.00
  positions_value: 1750.00

daily_metrics:
  daily_pnl: 250.00
  daily_pnl_pct: 0.025
  
cumulative_metrics:
  total_pnl: 250.00
  total_pnl_pct: 0.025
  starting_bankroll: 10000.00

positions:
  open_count: 2
  closed_today: 0
  
trades:
  count_today: 2
  volume_today: 40.50
  
risk:
  max_position_pct: 0.05
  capital_at_risk: 1750.00
  capital_at_risk_pct: 0.175
```

---

#### Alert Log (`alerts/YYYY-MM-DD.md`)

```markdown
# Alerts - 2025-01-14

## 15:30:00 - INFO - Position Update
Position `pos_abc123` gained 15.6% (unrealized)

---

## 11:45:00 - WARNING - High Volatility
Market `TICKER-XYZ-456` moved 10% in last hour

---

## 10:15:00 - INFO - Trade Executed
Opened position: BUY 50 YES @ $0.45 on TICKER-ABC-123

---
```

---

### File Operations

#### Reading State

```python
import yaml
from pathlib import Path

DATA_DIR = Path("data")

def load_state() -> dict:
    """Load current portfolio state."""
    with open(DATA_DIR / "state.yaml") as f:
        return yaml.safe_load(f)

def load_config() -> dict:
    """Load system configuration."""
    with open(DATA_DIR / "config.yaml") as f:
        return yaml.safe_load(f)
```

#### Writing State (Atomic)

```python
import tempfile
import shutil

def save_state(state: dict) -> None:
    """Atomically save state to prevent corruption."""
    state_path = DATA_DIR / "state.yaml"
    
    # Write to temp file first
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        yaml.dump(state, f, default_flow_style=False)
        temp_path = f.name
    
    # Atomic rename
    shutil.move(temp_path, state_path)
```

#### Querying Positions

```python
from pathlib import Path
import yaml

def get_open_positions() -> list[dict]:
    """Get all open positions."""
    positions = []
    for path in (DATA_DIR / "positions" / "open").glob("*.yaml"):
        with open(path) as f:
            positions.append(yaml.safe_load(f))
    return positions

def get_positions_with_loss(threshold: float = 0.10) -> list[dict]:
    """Find positions with unrealized loss > threshold."""
    return [
        p for p in get_open_positions()
        if p.get("unrealized_pnl_pct", 0) < -threshold
    ]
```

#### Appending to Trade Ledger

```python
import json
from datetime import date

def log_trade(trade: dict) -> None:
    """Append trade to today's ledger."""
    today = date.today().isoformat()
    ledger_path = DATA_DIR / "trades" / f"{today}.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ledger_path, "a") as f:
        f.write(json.dumps(trade) + "\n")
```


---

## Command Line Interface

Since this system runs locally, the primary interface is a CLI rather than a REST API.

### Main Commands

```bash
# Start the autonomous trading system
python -m coliseum run

# Run individual agents manually
python -m coliseum scout --scan-type full
python -m coliseum scout --scan-type quick
python -m coliseum analyst --opportunity-id opp_abc123
python -m coliseum guardian --check-positions
python -m coliseum trader --recommendation-id rec_abc123

# Portfolio management
python -m coliseum portfolio status
python -m coliseum portfolio history --days 30
python -m coliseum positions list
python -m coliseum positions close TICKER-ABC-123

# Configuration
python -m coliseum config show
python -m coliseum config set trading.paper_mode false

# Utilities
python -m coliseum init              # Set up data directory structure
python -m coliseum snapshot          # Force daily snapshot
python -m coliseum alerts list       # View recent alerts
python -m coliseum alerts clear      # Clear acknowledged alerts
```

### Optional: FastAPI Dashboard

For a web-based view, an optional FastAPI server can be run:

```bash
python -m coliseum serve --port 8000
```

```
GET    /                             # Dashboard (static HTML)
GET    /api/portfolio                # Current portfolio state
GET    /api/positions                # List positions
GET    /api/recommendations          # List pending recommendations
POST   /api/recommendations/{id}/approve
POST   /api/recommendations/{id}/reject
GET    /api/alerts                   # Recent alerts
```

---

## Telegram Bot Alert System

### Overview

The system uses a Telegram bot to deliver real-time notifications for trading activity, position updates, and system alerts. This enables immediate awareness of portfolio changes without needing to monitor a dashboard.

### Bot Setup

| Setting | Description |
|---------|-------------|
| **Bot Token** | Obtained via [@BotFather](https://t.me/BotFather) |
| **Chat ID** | Your personal or group chat ID for receiving alerts |
| **Rate Limit** | Max 30 messages per second (Telegram limit) |

### Alert Types & Priority

| Priority | Type | Telegram Behavior |
|----------|------|-------------------|
| 🔴 **Critical** | Daily loss limit hit, circuit breaker triggered | Sound + notification |
| 🟠 **High** | Trade executed, position closed, stop loss/take profit | Sound + notification |
| 🟡 **Medium** | New opportunity found, recommendation generated | Silent notification |
| 🟢 **Low** | Position check complete, daily summary | Silent, batched |

### Message Formats

#### Trade Executed
```
🟢 TRADE EXECUTED

📈 BUY YES on TICKER-ABC-123
💰 50 contracts @ $0.45
💵 Total: $22.50 (5% of portfolio)

Edge: +20% | EV: +44%
Confidence: 72%
```

#### Position Closed
```
🔴 POSITION CLOSED

📉 SOLD YES on TICKER-ABC-123
💰 50 contracts @ $0.70
💵 Realized P&L: +$12.50 (+55.6%)

Trigger: profit_target
Duration: 2d 4h
```

#### Stop Loss Triggered
```
⚠️ STOP LOSS TRIGGERED

📉 TICKER-XYZ-456
💰 30 contracts closed @ $0.42
💵 Realized Loss: -$5.40 (-30%)

Original thesis invalidated
```

#### Daily Summary
```
📊 DAILY SUMMARY - 2025-01-14

Portfolio Value: $10,250.00
Daily P&L: +$250.00 (+2.5%)

Open Positions: 2
Trades Today: 3

Top Performer: TICKER-ABC +15.6%
Worst: TICKER-XYZ -8.2%
```

#### Circuit Breaker Alert
```
🚨 CIRCUIT BREAKER ACTIVATED

Daily loss limit reached (-5.0%)
Trading halted until tomorrow

Current P&L: -$500.00
Positions frozen: 3

⚠️ Manual review required
```

### Implementation

```python
import httpx
from pydantic import BaseModel
from enum import Enum

class AlertPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TelegramNotifier:
    """Send alerts via Telegram Bot API."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_alert(
        self,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a Telegram message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_notification": priority in [
                        AlertPriority.LOW, 
                        AlertPriority.MEDIUM
                    ],
                },
            )
            return response.status_code == 200
    
    async def send_trade_executed(self, trade: "TradeExecution") -> bool:
        """Send trade execution notification."""
        emoji = "🟢" if trade.side == "YES" else "🔴"
        message = f"""
{emoji} *TRADE EXECUTED*

📈 BUY {trade.side} on `{trade.market_ticker}`
💰 {trade.contracts} contracts @ ${trade.price_per_contract:.2f}
💵 Total: ${trade.total_cost:.2f} ({trade.portfolio_pct:.1%} of portfolio)

Edge: +{trade.edge_at_entry:.0%} | EV: +{trade.ev_at_entry:.0%}
        """
        return await self.send_alert(message.strip(), AlertPriority.HIGH)
    
    async def send_position_closed(
        self, 
        position: "Position", 
        pnl: float, 
        trigger: str
    ) -> bool:
        """Send position close notification."""
        emoji = "🟢" if pnl > 0 else "🔴"
        pnl_pct = pnl / position.total_cost * 100
        message = f"""
{emoji} *POSITION CLOSED*

📉 SOLD {position.side} on `{position.market_ticker}`
💰 {position.contracts} contracts
💵 Realized P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)

Trigger: {trigger}
        """
        return await self.send_alert(message.strip(), AlertPriority.HIGH)
    
    async def send_circuit_breaker(self, reason: str, daily_pnl: float) -> bool:
        """Send circuit breaker alert."""
        message = f"""
🚨 *CIRCUIT BREAKER ACTIVATED*

{reason}
Trading halted until tomorrow

Current P&L: ${daily_pnl:.2f}

⚠️ Manual review required
        """
        return await self.send_alert(message.strip(), AlertPriority.CRITICAL)
```

### Configuration

Add to `config.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # From environment
  chat_id: "${TELEGRAM_CHAT_ID}"      # Your chat ID
  
  # Alert preferences
  alerts:
    trade_executed: true
    position_closed: true
    stop_loss: true
    take_profit: true
    daily_summary: true
    circuit_breaker: true
    
  # Quiet hours (UTC) - only critical alerts
  quiet_hours:
    enabled: false
    start: "02:00"
    end: "08:00"
```

### Environment Variables

Add to `.env`:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
TELEGRAM_CHAT_ID=987654321
```

### Bot Commands (Future Enhancement)

| Command | Description |
|---------|-------------|
| `/status` | Current portfolio status |
| `/positions` | List open positions |
| `/pause` | Pause trading (manual override) |
| `/resume` | Resume trading |
| `/alerts on/off` | Toggle alert notifications |

---

## Scheduler (APScheduler)

Using APScheduler for in-process job scheduling—no Redis or Celery required.

### Scheduled Jobs

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    
    # Scout: Full market scan every hour
    scheduler.add_job(
        scout_full_scan,
        trigger=CronTrigger(minute=0),
        id="scout-full-scan",
        name="Scout Full Scan",
    )
    
    # Scout: Quick scan every 15 minutes
    scheduler.add_job(
        scout_quick_scan,
        trigger=IntervalTrigger(minutes=15),
        id="scout-quick-scan",
        name="Scout Quick Scan",
    )
    
    # Guardian: Position check every 15 minutes
    scheduler.add_job(
        guardian_check_positions,
        trigger=IntervalTrigger(minutes=15),
        id="guardian-position-check",
        name="Guardian Position Check",
    )
    
    # Guardian: News scan every 30 minutes
    scheduler.add_job(
        guardian_news_scan,
        trigger=IntervalTrigger(minutes=30),
        id="guardian-news-scan",
        name="Guardian News Scan",
    )
    
    # Portfolio: Daily snapshot at 4 PM EST
    scheduler.add_job(
        portfolio_daily_snapshot,
        trigger=CronTrigger(hour=16, minute=0),
        id="portfolio-snapshot",
        name="Portfolio Daily Snapshot",
    )
    
    # Settlement: Check for resolved events hourly
    scheduler.add_job(
        check_settlements,
        trigger=CronTrigger(minute=30),
        id="check-settlements",
        name="Check Settlements",
    )
    
    return scheduler
```

### Event-Driven Processing

Agents communicate through the file system (file-based queue pattern):

```python
async def scout_full_scan():
    """Scout discovers opportunities, writes to opportunities/"""
    opportunities = await scout_agent.scan()
    for opp in opportunities:
        # Write opportunity file
        save_opportunity(opp)
        # Queue for analyst by writing to pending queue
        queue_for_analyst(opp.id)

async def process_analyst_queue():
    """Analyst processes pending opportunities"""
    pending = list((DATA_DIR / "queue" / "analyst").glob("*.json"))
    for item in pending:
        opportunity_id = json.loads(item.read_text())["opportunity_id"]
        recommendation = await analyst_agent.research(opportunity_id)
        if recommendation.action != "ABSTAIN":
            save_recommendation(recommendation)
            queue_for_trader(recommendation.id)
        item.unlink()  # Remove from queue

async def process_trader_queue():
    """Trader processes pending recommendations"""
    pending = list((DATA_DIR / "queue" / "trader").glob("*.json"))
    for item in pending:
        recommendation_id = json.loads(item.read_text())["recommendation_id"]
        await trader_agent.evaluate_and_execute(recommendation_id)
        item.unlink()
```

---

## Risk Management Framework

### Hard Limits (Circuit Breakers)

| Limit | Threshold | Action |
|-------|-----------|--------|
| **Max Position Size** | 10% of portfolio | Reject trade |
| **Max Single Trade** | $1,000 | Reject trade |
| **Max Open Positions** | 10 | Reject new positions |
| **Daily Loss Limit** | 5% of portfolio | Halt all trading for day |
| **Weekly Loss Limit** | 15% of portfolio | Halt all trading for week |
| **Max Drawdown** | 25% from peak | Halt all trading, alert admin |

### Position-Level Rules

| Rule | Description |
|------|-------------|
| **Minimum Edge** | Only trade if edge > 5% |
| **Minimum EV** | Only trade if EV > 10% |
| **Kelly Sizing** | Use 1/4 Kelly for position sizing |
| **Profit Target** | Auto-close at 50% profit |
| **Stop Loss** | Auto-close at 30% loss |
| **Time Decay** | Close positions with < 24h to expiry at 50% of original allocation |

### Manual Approval Gates

```python
class ApprovalGates:
    """Conditions requiring human approval"""
    
    LARGE_TRADE_THRESHOLD = 500.00  # Trades > $500 need approval
    LOW_CONFIDENCE_THRESHOLD = 0.65  # Confidence < 65% needs approval
    HIGH_RISK_CATEGORIES = ["crypto", "memecoins"]  # These need approval
    FIRST_TRADE_OF_DAY = True  # First trade always needs approval (optional)
```

---

## Local Execution

### Running the System

No Docker, no servers—just Python:

```bash
# Set up the environment
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Initialize data directory
python -m coliseum init

# Start autonomous operation
python -m coliseum run
```

### Directory Structure

```
backend/
├── .venv/                    # Python virtual environment
├── .env                      # Environment variables (API keys)
├── requirements.txt
│
├── coliseum/                 # Main package
│   ├── __main__.py           # CLI entry point
│   ├── agents/
│   │   ├── scout.py
│   │   ├── analyst.py
│   │   ├── trader.py
│   │   └── guardian.py
│   ├── storage/
│   │   ├── state.py          # State management
│   │   ├── files.py          # File operations
│   │   └── queue.py          # File-based queue
│   ├── services/
│   │   ├── kalshi.py         # Kalshi API client
│   │   ├── exa.py            # Exa AI client
│   │   └── perplexity.py     # Perplexity client
│   └── scheduler.py          # APScheduler setup
│
└── data/                    
    ├── config.yaml
    ├── state.yaml
    ├── opportunities/
    ├── research/
    ├── recommendations/
    ├── positions/
    ├── trades/
    ├── alerts/
    ├── snapshots/
    └── queue/
        ├── analyst/
        └── trader/
```

### Backup Strategy

```bash
# Backup entire data directory
cp -r data/ backup/data-$(date +%Y-%m-%d)/

# Or use git for version control
cd data && git init && git add -A && git commit -m "Snapshot"
```

---

## Observability & Monitoring

### Logfire Integration

```python
import logfire

# Configure Logfire
logfire.configure(
    service_name="coliseum",
    environment=os.getenv("ENVIRONMENT", "development"),
)

# Automatic PydanticAI instrumentation
logfire.instrument_pydantic_ai()

# Custom spans for trading operations
with logfire.span("trade_execution", trade_id=trade.id):
    result = await trader.execute(trade)
    logfire.info("trade_completed", result=result.model_dump())
```

### Key Metrics to Track

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `agent.scout.opportunities_found` | New opportunities per scan | < 2 per hour |
| `agent.analyst.research_duration` | Time to complete research | > 5 minutes |
| `agent.trader.execution_latency` | Order placement time | > 10 seconds |
| `agent.guardian.positions_checked` | Positions monitored per cycle | Mismatch with open count |
| `portfolio.daily_pnl` | Today's P&L | < -5% |
| `portfolio.open_positions` | Current position count | > 10 |
| `risk.capital_at_risk` | $ at risk in open positions | > 30% of portfolio |
| `kalshi.api_errors` | API error rate | > 5% of calls |

---

## Implementation Phases

### Package Structure

Before starting, create the `coliseum/` package with this structure:

```
backend/
├── coliseum/                     # NEW: Main agent package
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point
│   ├── config.py                 # Load config.yaml + environment
│   ├── scheduler.py              # APScheduler setup
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py               # Shared agent utilities
│   │   ├── scout.py              # Market discovery agent
│   │   ├── analyst.py            # Research + recommendation agent
│   │   ├── trader.py             # Trade execution agent
│   │   ├── guardian.py           # Position monitoring agent
│   │   ├── risk.py               # Risk management logic
│   │   └── calculations.py       # Edge/EV/Kelly calculations
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── state.py              # Portfolio state (state.yaml)
│   │   ├── files.py              # File operations (atomic writes)
│   │   └── queue.py              # File-based job queue
│   │
│   └── services/
│       ├── __init__.py
│       ├── kalshi.py             # Kalshi API client (public + trading)
│       ├── exa.py                # Exa AI research wrapper
│       └── telegram.py           # Telegram alert notifier
│
└── data/                         # NEW: Runtime data directory
    ├── config.yaml               # System configuration
    ├── state.yaml                # Current portfolio state
    ├── opportunities/            # Scout output
    ├── research/                 # Analyst research briefs
    ├── recommendations/          # Trade recommendations
    ├── positions/
    │   ├── open/
    │   └── closed/
    ├── trades/                   # JSONL trade ledger
    ├── alerts/                   # Daily alert logs
    ├── snapshots/                # Daily portfolio snapshots
    └── queue/
        ├── analyst/              # Pending for Analyst
        └── trader/               # Pending for Trader
```

---

### Phase 1: Foundation (Week 1-2)

**Goal**: Core infrastructure—agents can run, Kalshi API works, files persist.

#### 1.1 Project Setup
- [ ] Create `coliseum/` package structure (directories + `__init__.py` files)
- [ ] Create `coliseum/__main__.py` with basic CLI skeleton (`init`, `run`, `status`)
- [ ] Create `coliseum/config.py` to load `data/config.yaml` and `.env`
- [ ] Update `requirements.txt`:
  - Add: `apscheduler>=3.10.4`, `pyyaml>=6.0.1`, `cryptography>=42.0.0`
  - Remove: `celery`, `redis`, `flower`, `kombu` (no longer needed)

#### 1.2 Storage Layer (`coliseum/storage/`)
- [ ] `state.py`: Implement `load_state()`, `save_state()` with atomic writes
- [ ] `files.py`: Implement `save_opportunity()`, `save_recommendation()`, `log_trade()`
- [ ] `queue.py`: Implement `queue_for_analyst()`, `queue_for_trader()`, `get_pending()`
- [ ] Create `data/config.yaml` template with all configuration options
- [ ] Create `data/state.yaml` initial template (empty portfolio)

#### 1.3 Kalshi API Client (`coliseum/services/kalshi.py`)
- [ ] Migrate `mess_around/explore_kalshi_api.py` → production client
- [ ] Add `KalshiTradingAuth` class (RSA signature generation)
- [ ] Implement authenticated methods:
  - `get_balance()` → Account balance and buying power
  - `get_positions()` → All open positions
  - `place_order(ticker, side, count, type, price)` → Execute trade
  - `cancel_order(order_id)` → Cancel pending order
  - `get_order_status(order_id)` → Check fill status
- [ ] Add paper mode flag (skip actual API calls, simulate fills)

#### 1.4 Scout Agent (`coliseum/agents/scout.py`)
- [ ] Create `ScoutConfig`, `OpportunitySignal` Pydantic models
- [ ] Implement `scout_agent` with PydanticAI
- [ ] Add tools: `fetch_markets`, `check_liquidity`, `categorize_event`
- [ ] Implement `run_scout()` function that writes to `data/opportunities/`
- [ ] Queue discovered opportunities for Analyst

#### 1.5 Scheduler (`coliseum/scheduler.py`)
- [ ] Create `AsyncIOScheduler` with jobs:
  - Scout full scan: Every hour at `:00`
  - Scout quick scan: Every 15 minutes
  - Process analyst queue: Every 5 minutes
  - Process trader queue: Every 5 minutes
- [ ] Implement `start_scheduler()` and `stop_scheduler()` functions

#### 1.6 Phase 1 Verification
| Test | Method |
|------|--------|
| Storage atomic writes | Unit test: write state, crash mid-write, verify no corruption |
| Kalshi API connection | Integration: fetch markets, verify response parsing |
| Scout market discovery | Manual: run scout, inspect `data/opportunities/` output |
| Scheduler runs jobs | Manual: start scheduler, verify jobs execute on schedule |

---

### Phase 2: Intelligence (Week 3-4)

**Goal**: Analyst agent produces high-quality trade recommendations backed by research.

#### 2.1 Exa AI Integration (`coliseum/services/exa.py`)
- [ ] Create `ExaResearcher` class wrapping `exa-py` client
- [ ] Implement `search(query, num_results)` → List of results with URLs
- [ ] Implement `answer(question)` → Answer with source citations
- [ ] Add error handling and retry logic

#### 2.2 Analyst Agent (`coliseum/agents/analyst.py`)
- [ ] Create Pydantic models:
  - `AnalystConfig` (research depth, min confidence, timeout)
  - `ResearchBrief` (key facts, sources, base rate, sentiment)
  - `TradeRecommendation` (action, confidence, edge, EV, sizing)
- [ ] Implement `analyst_agent` with PydanticAI
- [ ] Add tools:
  - `generate_search_queries(opportunity)` → List of search queries
  - `exa_search(query)` → Execute Exa search
  - `synthesize_research(results)` → Create ResearchBrief
  - `calculate_edge_ev(probability, market_price)` → Edge and EV
- [ ] Implement research workflow (query → search → synthesize → recommend)

#### 2.3 Edge/EV Calculations (`coliseum/agents/calculations.py`)
- [ ] `calculate_edge(true_prob, market_prob)` → Edge percentage
- [ ] `calculate_expected_value(win_prob, payout, cost)` → EV per dollar
- [ ] `calculate_kelly_fraction(win_prob, odds, fraction=0.25)` → Position size %

#### 2.4 Analyst Queue Processing
- [ ] Implement `process_analyst_queue()`:
  1. Read pending items from `data/queue/analyst/`
  2. Load opportunity from `data/opportunities/`
  3. Run analyst agent
  4. Save research brief to `data/research/`
  5. Save recommendation to `data/recommendations/`
  6. If action != `ABSTAIN`, queue for trader
  7. Delete processed queue item

#### 2.5 Logfire Observability
- [ ] Add `logfire.configure()` to `coliseum/__init__.py`
- [ ] Instrument PydanticAI with `logfire.instrument_pydantic_ai()`
- [ ] Add custom spans for key operations (research, recommendation)

#### 2.6 Phase 2 Verification
| Test | Method |
|------|--------|
| Exa search returns results | Unit test with real API call |
| Research brief quality | Manual: inspect generated briefs for source quality |
| Edge/EV calculations | Unit test: verify math against known examples |
| Full pipeline | Integration: opportunity → research → recommendation |

---

### Phase 3: Execution (Week 5-6)

**Goal**: Trader agent safely executes trades with full risk management and liquidity-aware order execution.

#### 3.1 Risk Management (`coliseum/agents/risk.py`)
- [ ] Create `RiskManager` class with validation methods:
  - `check_position_limit(trade, portfolio)` → Max 10% per position
  - `check_daily_loss(portfolio)` → Max 5% daily loss
  - `check_open_positions(portfolio)` → Max 10 concurrent positions
  - `check_single_trade_cap(trade)` → Max $1,000 per trade
  - `check_edge_threshold(trade)` → Min 5% edge
  - `check_ev_threshold(trade)` → Min 10% EV
- [ ] Implement `validate_trade(trade, portfolio)` → `(passed: bool, reason: str)`

#### 3.2 Order Execution Models (`coliseum/agents/execution.py`)
- [ ] Create Pydantic models:
  - `OrderBookLevel` (price, contracts available)
  - `OrderBookDepth` (bid/ask levels, spreads, aggregate liquidity)
  - `SlippageEstimate` (fill simulation, adjusted edge/EV)
  - `ExecutionConfig` (slippage tolerance, reprice settings, timeouts)
  - `OrderState` enum (initialized, placed, partial, completed, cancelled)
  - `WorkingOrder` (order tracking through execution loop)

#### 3.3 Order Book & Slippage (`coliseum/services/kalshi.py`)
- [ ] Add `get_order_book(ticker)` → Fetch full order book depth from Kalshi
- [ ] Implement `calculate_slippage(order_book, side, contracts, max_price)`:
  - Walk order book levels
  - Calculate volume-weighted average fill price
  - Return `SlippageEstimate` with adjusted edge/EV
- [ ] Implement `size_with_liquidity(kelly_size, order_book, max_slippage)`:
  - Binary search for max size within slippage tolerance
  - Return reduced position size if order book is thin

#### 3.4 Trader Agent (`coliseum/agents/trader.py`)
- [ ] Create Pydantic models:
  - `TraderConfig` (limits, thresholds, paper mode flag)
  - `TradeExecution` (position details, sizing, execution status)
- [ ] Implement `trader_agent` with PydanticAI
- [ ] Add tools:
  - `get_portfolio_state()` → Current positions and P&L
  - `get_order_book_depth(ticker)` → Fetch bid/ask levels
  - `calculate_slippage(order_book, size)` → Estimate fill quality
  - `calculate_position_size(recommendation, order_book)` → Kelly + liquidity
  - `place_limit_order(ticker, side, contracts, limit_price)` → Execute limit order
  - `reprice_order(order_id, new_limit)` → Cancel and replace
  - `record_trade(execution)` → Log to JSONL ledger

#### 3.5 Working Order Execution Loop (`coliseum/agents/trader.py`)
- [ ] Implement order state machine:
  - `INITIALIZED` → `PLACED_LIMIT` → `CHECK_STATUS` → `COMPLETED/PARTIAL/CANCELLED`
- [ ] Implement `work_order(working_order)` loop:
  1. Place limit order at max acceptable price
  2. Wait `check_interval_seconds` (default: 5 min)
  3. Poll fill status from Kalshi
  4. If filled → complete and record
  5. If partial → decide: accept partial or reprice remainder
  6. If unfilled → re-check edge, reprice or cancel
  7. After `max_reprice_attempts` → cancel and log
- [ ] Track all state transitions in `WorkingOrder.state_history`

#### 3.6 Paper Trading Mode
- [ ] When `config.trading.paper_mode: true`:
  - Simulate order book (use snapshot from real data)
  - Simulate partial fills based on order book depth
  - Update `state.yaml` positions as if real
  - Log trades with `paper: true` flag

#### 3.7 Trade Journaling
- [ ] Append all trades to `data/trades/YYYY-MM-DD.jsonl`
- [ ] Include: position ID, recommendation ID, side, contracts, price, edge, EV, slippage, fill_type
- [ ] Store working order history for audit trail
- [ ] Atomically append (no corruption on crash)

#### 3.8 Phase 3 Verification
| Test | Method |
|------|--------|
| Order book parsing | Unit test: parse sample Kalshi order book response |
| Slippage calculation | Unit test: verify avg fill price against manual calculation |
| Slippage edge rejection | Unit test: trade rejected when slippage destroys edge |
| Liquidity sizing | Unit test: position size reduced for thin books |
| Working order loop | Integration: mock partial fill, verify reprice triggered |
| Risk manager blocks bad trades | Unit test: trades exceeding limits are rejected |
| Kelly sizing is correct | Unit test: verify against manual calculations |
| Paper trades logged correctly | Integration: execute paper trade, verify ledger entry |
| State updates correctly | Integration: paper trade, verify `state.yaml` reflects position |

---

### Phase 4: Monitoring (Week 7-8)

**Goal**: Guardian agent watches positions, triggers exits, sends Telegram alerts.

#### 4.1 Guardian Agent (`coliseum/agents/guardian.py`)
- [ ] Create Pydantic models:
  - `GuardianConfig` (check intervals, profit target, stop loss)
  - `PositionHealth` (current state, thesis assessment, recommendation)
  - `ExitSignal` (action, trigger, reasoning, urgency)
- [ ] Implement `guardian_agent` with PydanticAI
- [ ] Add tools:
  - `get_open_positions()` → All positions from `data/positions/open/`
  - `get_current_price(ticker)` → Fetch from Kalshi API
  - `assess_thesis(position, news)` → Re-evaluate original thesis
  - `generate_exit_signal(position, price)` → Profit target / stop loss check
- [ ] Implement position monitoring loop

#### 4.2 Exit Signal Logic
- [ ] Check profit target: Close if P&L >= +50%
- [ ] Check stop loss: Close if P&L <= -30%
- [ ] Check thesis invalidation: LLM re-assesses with new information
- [ ] Check time decay: Reduce position if < 24h to expiry

#### 4.3 Telegram Notifier (`coliseum/services/telegram.py`)
- [ ] Create `TelegramNotifier` class
- [ ] Implement alert methods:
  - `send_trade_executed(trade)` → 🟢 Trade notification
  - `send_position_closed(position, pnl, trigger)` → 🔴 Close notification
  - `send_stop_loss_triggered(position)` → ⚠️ Stop loss alert
  - `send_circuit_breaker(reason, pnl)` → 🚨 Critical alert
  - `send_daily_summary(portfolio)` → 📊 End of day summary
- [ ] Add quiet hours support (only critical alerts during quiet hours)

#### 4.4 Scheduled Alert Jobs
- [ ] Add to scheduler:
  - Guardian position check: Every 15 minutes
  - Guardian news scan: Every 30 minutes
  - Daily portfolio snapshot: 4 PM EST
  - Daily summary Telegram: 4:05 PM EST

#### 4.5 Phase 4 Verification
| Test | Method |
|------|--------|
| Telegram messages send | Manual: configure bot, send test message |
| Profit target triggers | Unit test: mock position at +50%, verify exit signal |
| Stop loss triggers | Unit test: mock position at -30%, verify exit signal |
| Guardian loop runs | Integration: start system with open position, verify health checks |

---

### Phase 5: Polish (Week 9+)

**Goal**: CLI interface, production hardening, extended paper trading.

#### 5.1 CLI Interface (`coliseum/__main__.py`)
- [ ] Implement commands:
  ```bash
  python -m coliseum init                    # Initialize data directory
  python -m coliseum run                     # Start full autonomous system
  python -m coliseum scout --scan-type full  # Manual scout scan
  python -m coliseum analyst --opportunity-id OPP123
  python -m coliseum portfolio status        # Show current portfolio
  python -m coliseum positions list          # List open positions
  python -m coliseum positions close TICKER  # Manual position close
  python -m coliseum config show             # Display configuration
  python -m coliseum test-telegram           # Test Telegram connection
  ```
- [ ] Use `argparse` or `click` for CLI framework

#### 5.2 Paper Trading at Scale
- [ ] Run full system in paper mode for 2-4 weeks
- [ ] Track metrics:
  - Hit rate (% of recommendations that resolve profitably)
  - Edge accuracy (estimated edge vs actual outcome)
  - Average P&L per trade
  - Sharpe ratio simulation
- [ ] Create `data/metrics/` for performance tracking

#### 5.3 Parameter Tuning
- [ ] Analyze paper trading results
- [ ] Adjust thresholds based on data:
  - Min edge threshold (currently 5%)
  - Min EV threshold (currently 10%)
  - Kelly fraction (currently 0.25)
  - Profit target (currently 50%)
  - Stop loss (currently 30%)
- [ ] Document optimal parameters in `config.yaml`

#### 5.4 Live Trading Transition
- [ ] Create checklist for go-live:
  - [ ] Kalshi account funded
  - [ ] Paper trading profitable for 2+ weeks
  - [ ] All Telegram alerts working
  - [ ] Risk limits verified
  - [ ] Manual override tested
- [ ] Start with reduced limits (e.g., max $100/trade)
- [ ] Gradually increase limits as confidence builds

#### 5.5 Optional: FastAPI Dashboard
- [ ] Create `coliseum/api/dashboard.py`
- [ ] Endpoints:
  - `GET /api/portfolio` → Current state
  - `GET /api/positions` → Open positions
  - `GET /api/recommendations` → Pending recommendations
  - `POST /api/recommendations/{id}/approve` → Manual approval
  - `GET /api/alerts` → Recent alerts
- [ ] Simple static HTML dashboard

#### 5.6 Phase 5 Verification
| Test | Method |
|------|--------|
| CLI commands work | Manual: run each command, verify output |
| Paper trading metrics accurate | Compare logged trades to Kalshi market outcomes |
| Live trade executes | Integration: place small live trade, verify on Kalshi |

---

## Appendix

### A. Sample Agent Definition (PydanticAI)

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import Literal
from datetime import datetime

# Define structured output
class ScoutOutput(BaseModel):
    opportunities: list[OpportunitySignal]
    scan_summary: str
    next_scan_recommendation: datetime

# Define agent dependencies (injected context)
class ScoutDependencies(BaseModel):
    kalshi_client: KalshiAPI
    db_session: AsyncSession
    config: ScoutConfig

# Create the agent
scout_agent = Agent(
    model="anthropic:claude-3-5-haiku",
    result_type=ScoutOutput,
    deps_type=ScoutDependencies,
    system_prompt="""
    You are a market scout for a prediction market trading system.
    Your job is to identify high-quality trading opportunities from Kalshi.
    
    Focus on:
    - Events with sufficient liquidity (volume > 10,000 contracts)
    - Markets with reasonable spreads
    - Events closing within 72 hours
    - Diverse categories (avoid concentration)
    
    Rate each opportunity as high/medium/low priority based on:
    - Information asymmetry potential
    - Market inefficiency signals
    - News catalyst potential
    """,
)

# Define tools
@scout_agent.tool
async def fetch_kalshi_markets(
    ctx: RunContext[ScoutDependencies],
    status: str = "open",
    max_close_hours: int = 72,
) -> list[dict]:
    """Fetch markets from Kalshi API."""
    return await ctx.deps.kalshi_client.get_markets_closing_within_hours(max_close_hours)

@scout_agent.tool
async def check_market_liquidity(
    ctx: RunContext[ScoutDependencies],
    market_ticker: str,
) -> dict:
    """Check bid-ask spread and volume for a market."""
    return await ctx.deps.kalshi_client.get_market_orderbook(market_ticker)

# Run the agent
async def run_scout():
    deps = ScoutDependencies(
        kalshi_client=kalshi_client,
        db_session=db_session,
        config=ScoutConfig(),
    )
    
    result = await scout_agent.run(
        "Scan current Kalshi markets and identify trading opportunities.",
        deps=deps,
    )
    
    return result.data  # ScoutOutput
```

### B. Environment Variables

```bash
# .env.example

# Kalshi API
KALSHI_API_KEY=your_api_key
KALSHI_PRIVATE_KEY_PATH=/path/to/private.pem

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
EXA_API_KEY=exa-...
PERPLEXITY_API_KEY=pplx-...

# OpenRouter (for model routing - optional)
OPENROUTER_API_KEY=sk-or-...

# Observability (optional)
LOGFIRE_TOKEN=...

# Note: Trading configuration is in data/config.yaml, not environment variables
```

### C. Kalshi Trading API Authentication

```python
import base64
import hashlib
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

class KalshiTradingAuth:
    """Authentication for Kalshi Member Trading API"""
    
    def __init__(self, api_key: str, private_key_path: str):
        self.api_key = api_key
        with open(private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
    
    def generate_signature(
        self, 
        timestamp: int, 
        method: str, 
        path: str
    ) -> str:
        """Generate request signature"""
        message = f"{timestamp}{method}{path}"
        signature = self.private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def get_headers(self, method: str, path: str) -> dict:
        """Get authentication headers for request"""
        timestamp = int(time.time() * 1000)
        signature = self.generate_signature(timestamp, method, path)
        
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
        }
```

---

### D. DuckDB Analytics Engine

> [!TIP]
> You do not need to rewrite your current code or change your file structure. That is the beauty of DuckDB—it meets your data where it lives.

However, to make your life easier when you *do* run those queries, I recommend **one small change to your Spec** (Schema) and **one addition to your Code**.

#### 1. The Spec Change: "Denormalize" the Trade Log

In your current spec, `TradeExecution` does not include the `category` (e.g., "Politics", "Crypto").

* **The Problem:** To calculate "Win Rate on Crypto," DuckDB would have to open the `trades.jsonl` file *AND* join it with the YAML/Markdown files in `opportunities/` to find the category. That is messy.
* **The Fix:** Add `category` (and maybe `tags`) directly to the `TradeExecution` model. Make the `Trader` agent copy this data from the `Recommendation` when it logs the trade.

**Update `TradeExecution` in your Spec:**

```python
class TradeExecution(BaseModel):
    # ... existing fields ...
    market_ticker: str
    side: Literal["YES", "NO"]
    
    # NEW FIELDS FOR ANALYTICS
    category: str  # e.g. "politics", "tech"
    strategy: str  # e.g. "deep_research", "quick_scalp"
    
    # ... existing fields ...
```

#### 2. The Code Addition: The Analytics Engine

You don't need to migrate data. You just need to **install one package** and add **one helper class**.

**Step A: Install**

```bash
pip install duckdb pandas
```

**Step B: Add `services/analytics.py`**

This is the "brain" that your Analyst agent will use to look up history. It treats your folder of JSONL files as if it were a high-performance database.

```python
import duckdb
import pandas as pd
from pathlib import Path

class AnalyticsEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        # Create an in-memory database connection
        self.con = duckdb.connect(database=":memory:")
        
    def query_performance(self, category: str = None) -> dict:
        """
        Run SQL directly on your JSONL files to get performance stats.
        """
        # We target all jsonl files in the trades directory using a glob pattern
        trades_path = self.data_dir / "trades" / "*.jsonl"
        
        query = f"""
            SELECT 
                count(*) as total_trades,
                avg(ev_at_entry) as avg_expected_value,
                sum(CASE WHEN status = 'filled' THEN total_cost ELSE 0 END) as volume,
                avg(edge_at_entry) as avg_edge
            FROM read_json_auto('{trades_path}')
            WHERE status = 'filled'
        """
        
        if category:
            # This works because we added 'category' to the JSONL schema!
            query += f" AND category = '{category}'"
            
        # Execute and return as a dictionary (for the Agent to read)
        df = self.con.execute(query).df()
        return df.to_dict(orient="records")[0]

    def get_win_rate_by_confidence(self):
        """
        Complex query: Did high confidence actually result in wins?
        (Requires joining with closed positions - assuming similar JSONL structure)
        """
        # You can write standard SQL here
        pass
```

#### 3. Updated Architecture Diagram

DuckDB sits "on the side" as a read-only observer:

```
[ Scout ] ---> [ Analyst ] ---> [ Trader ]
                    ^               |
                    | (Queries)     | (Writes JSONL)
                    |               v
           [ DuckDB Analytics ] <--- [ File System ]
```

#### 4. Summary of Changes Required

| Area | Change Required? | Details |
|------|------------------|---------|
| **Files** | No | Keep `jsonl` and `yaml` formats |
| **TradeExecution Model** | Yes | Add `category` and `strategy` fields |
| **Trader Agent** | Yes | Copy `category` from Recommendation when logging trades |
| **Dependencies** | Yes | Add `duckdb` and `pandas` to requirements.txt |
| **New Service** | Yes | Create `services/analytics.py` |

This is the "path of least resistance" that gives you enterprise-grade analytics capabilities immediately.

---
