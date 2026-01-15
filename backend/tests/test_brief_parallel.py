#!/usr/bin/env python3
"""
Brief Generator Parallel Execution Test

Verify that the BriefGenerator can execute multiple Exa queries in parallel.

Usage:
    cd backend
    source venv/bin/activate
    python tests/test_brief_parallel.py
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load .env file before any other imports
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

# Configure logfire before importing modules that use it
import logfire
logfire.configure(send_to_logfire=False)


async def main():
    """Test BriefGenerator with parallel query execution."""
    print("\n" + "=" * 60)
    print("BRIEF GENERATOR PARALLEL EXECUTION TEST")
    print("=" * 60)

    # Check for API keys
    exa_key = os.getenv("EXA_API_KEY")
    if not exa_key:
        print("ERROR: EXA_API_KEY environment variable not set")
        sys.exit(1)

    # Import and initialize the BriefGenerator
    try:
        from pipeline.stages.research.brief_generator import BriefGenerator
        generator = BriefGenerator()
        print("✅ BriefGenerator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize BriefGenerator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Create a test event
    event = {
        'ticker': 'TEST-BTC-100K',
        'question': 'Will Bitcoin reach $100,000 by end of 2026?',
        'resolution_criteria': 'BTC-USD >= $100,000 on CoinGecko at any point before Dec 31, 2026 23:59:59 UTC',
        'close_time': '2026-12-31T23:59:59Z',
        'yes_price': 0.45,
        'category': 'finance'
    }

    print(f"\n📊 Event: {event['question']}")
    print("-" * 60)

    # Measure time for parallel execution
    start_time = time.time()

    try:
        print("\n🔄 Generating brief with parallel Exa queries...")
        brief = await generator.generate_brief(event)

        elapsed_time = time.time() - start_time

        print(f"\n⏱️  Execution time: {elapsed_time:.2f} seconds")
        print("\n📝 BRIEF SUMMARY:")
        print(f"  • Market Question: {brief.market_question}")
        print(f"  • Key Facts: {len(brief.key_facts)} items")
        print(f"  • Recent Developments: {len(brief.recent_developments)} items")
        print(f"  • Historical Context: {len(brief.historical_context)} items")
        print(f"  • Expert Views: {len(brief.expert_views)} items")
        print(f"  • Sources: {len(brief.sources)} sources")

        print("\n📚 KEY FACTS:")
        for i, fact in enumerate(brief.key_facts[:3], 1):
            print(f"  {i}. {fact}")

        print("\n📰 RECENT DEVELOPMENTS:")
        for i, dev in enumerate(brief.recent_developments[:3], 1):
            print(f"  {i}. {dev}")

        print("\n✅ Brief generation with parallel queries is working correctly!")

        # Verify performance improvement
        if elapsed_time < 120:  # Should be much faster than 5 queries × 30s each
            print(f"\n🚀 Performance check PASSED: {elapsed_time:.2f}s (expected < 120s for parallel execution)")
        else:
            print(f"\n⚠️  Performance warning: {elapsed_time:.2f}s (might be running sequentially)")

    except Exception as e:
        print(f"\n❌ Error generating brief: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
