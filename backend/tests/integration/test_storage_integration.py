"""Quick integration test for storage layer Phase 1.2.

This script tests:
1. Loading/saving state
2. Creating opportunities, research, recommendations
3. Logging trades
4. Queue operations

Run from backend/ directory: python test_storage_integration.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coliseum.storage import (
    # State
    load_state,
    save_state,
    PortfolioState,
    Position,
    # Files
    OpportunitySignal,
    ResearchBrief,
    TradeRecommendation,
    TradeExecution,
    save_opportunity,
    save_research_brief,
    save_recommendation,
    log_trade,
    generate_opportunity_id,
    generate_research_id,
    generate_recommendation_id,
    generate_trade_id,
    # Queue
    queue_for_analyst,
    queue_for_trader,
    get_pending,
    dequeue,
)


def test_state_management():
    """Test loading and saving portfolio state."""
    print("\n=== Testing State Management ===")

    # Load state
    state = load_state()
    print(f"✓ Loaded state: {state.portfolio.total_value:.2f}")

    # Modify state
    original_value = state.portfolio.cash_balance
    state.portfolio.cash_balance -= 100.0
    state.portfolio.positions_value += 100.0

    # Save state
    save_state(state)
    print(f"✓ Saved state (moved $100 to positions)")

    # Reload and verify
    reloaded = load_state()
    assert reloaded.portfolio.cash_balance == original_value - 100.0
    print(f"✓ Verified state persistence")

    # Restore original
    state.portfolio.cash_balance = original_value
    state.portfolio.positions_value -= 100.0
    save_state(state)
    print("✓ Restored original state")


def test_file_operations():
    """Test creating opportunity, research, and recommendation files."""
    print("\n=== Testing File Operations ===")

    # Create test opportunity
    opp_id = generate_opportunity_id()
    opportunity = OpportunitySignal(
        id=opp_id,
        event_ticker="TEST-EVENT",
        market_ticker="TEST-MARKET-001",
        title="Test: Will integration tests pass?",
        category="testing",
        yes_price=0.75,
        no_price=0.25,
        volume_24h=50000,
        close_time=datetime.now(timezone.utc) + timedelta(days=2),
        priority="high",
        rationale="This is a test opportunity for Phase 1.2 integration testing.",
        discovered_at=datetime.now(timezone.utc),
    )

    opp_path = save_opportunity(opportunity)
    print(f"✓ Created opportunity: {opp_path}")

    # Create test research brief
    research_id = generate_research_id()
    brief = ResearchBrief(
        id=research_id,
        opportunity_id=opp_id,
        event_ticker="TEST-EVENT",
        market_ticker="TEST-MARKET-001",
        synthesis="""## Key Findings

The integration test demonstrates that all storage layer components are working correctly.
This includes state management, file operations, and queue processing.

### Technical Assessment
- All Pydantic models are validating correctly
- Atomic file writes prevent corruption
- Queue operations support agent communication
""",
        sources=["https://github.com/coliseum", "https://example.com/docs"],
        confidence_level="high",
        sentiment="bullish",
        key_uncertainties=[
            "Test environment may differ from production",
            "Concurrent access patterns not yet verified",
        ],
        created_at=datetime.now(timezone.utc),
    )

    brief_path = save_research_brief(brief)
    print(f"✓ Created research brief: {brief_path}")

    # Create test recommendation
    rec_id = generate_recommendation_id()
    recommendation = TradeRecommendation(
        id=rec_id,
        opportunity_id=opp_id,
        research_brief_id=research_id,
        event_ticker="TEST-EVENT",
        market_ticker="TEST-MARKET-001",
        action="BUY_YES",
        confidence=0.85,
        estimated_true_probability=0.90,
        current_market_price=0.75,
        expected_value=0.20,
        edge=0.15,
        suggested_position_pct=0.05,
        reasoning="Strong edge based on research. High confidence in outcome.",
        key_risks=[
            "Time decay: Event closes in 48 hours",
            "Market volatility: Price may shift quickly",
        ],
        created_at=datetime.now(timezone.utc),
    )

    rec_path = save_recommendation(recommendation)
    print(f"✓ Created recommendation: {rec_path}")

    # Log test trade
    trade_id = generate_trade_id()
    trade = TradeExecution(
        id=trade_id,
        position_id=None,
        recommendation_id=rec_id,
        market_ticker="TEST-MARKET-001",
        side="YES",
        action="BUY",
        contracts=50,
        price=0.75,
        total=37.50,
        portfolio_pct=0.05,
        edge=0.15,
        ev=0.20,
        paper=True,
        executed_at=datetime.now(timezone.utc),
        category="testing",
    )

    log_trade(trade)
    print(f"✓ Logged trade: {trade_id}")

    return opp_id, rec_id


def test_queue_operations(opp_id: str, rec_id: str):
    """Test file-based queue operations."""
    print("\n=== Testing Queue Operations ===")

    # Queue for analyst
    queue_for_analyst(opp_id)
    print(f"✓ Queued opportunity {opp_id} for Analyst")

    # Get pending analyst items
    analyst_pending = get_pending("analyst")
    assert len(analyst_pending) > 0
    print(f"✓ Found {len(analyst_pending)} pending analyst items")

    # Dequeue
    dequeue("analyst", analyst_pending[0].id)
    print(f"✓ Dequeued item from analyst queue")

    # Queue for trader
    queue_for_trader(rec_id)
    print(f"✓ Queued recommendation {rec_id} for Trader")

    # Get pending trader items
    trader_pending = get_pending("trader")
    assert len(trader_pending) > 0
    print(f"✓ Found {len(trader_pending)} pending trader items")

    # Dequeue
    dequeue("trader", trader_pending[0].id)
    print(f"✓ Dequeued item from trader queue")

    # Verify empty
    assert len(get_pending("analyst")) == 0
    assert len(get_pending("trader")) == 0
    print("✓ Queues are empty after dequeue")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Phase 1.2 Storage Layer Integration Test")
    print("=" * 60)

    try:
        # Test state management
        test_state_management()

        # Test file operations
        opp_id, rec_id = test_file_operations()

        # Test queue operations
        test_queue_operations(opp_id, rec_id)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nPhase 1.2 implementation complete!")
        print("Storage layer is ready for Phase 1.3 (Kalshi API client)\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
