#!/usr/bin/env python3
"""
Exa AI Integration Test Script

Simple test to verify the Exa AI Answer API integration is working.

Usage:
    cd backend
    source .venv/bin/activate
    python tests/test_exa_integration.py
"""

import os
import sys
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
    """Test the Exa answer endpoint."""
    print("\n" + "=" * 60)
    print("EXA AI INTEGRATION TEST")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("ERROR: EXA_API_KEY environment variable not set")
        sys.exit(1)

    # Import and initialize the ExaClient
    try:
        from pipeline.stages.research.exa_client import ExaClient
        exa_client = ExaClient(api_key=api_key)
        print("✅ ExaClient initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ExaClient: {e}")
        sys.exit(1)

    # Test the answer endpoint
    query = "What are the latest developments in AI technology?"
    print(f"\nQuery: {query}")
    print("-" * 60)

    try:
        result = await exa_client.answer(query)

        print("\n📝 ANSWER:")
        print(result.answer)

        print(f"\n📚 CITATIONS ({len(result.citations)} sources):")
        for i, citation in enumerate(result.citations, 1):
            print(f"  [{i}] {citation.get('title', 'No title')}")
            print(f"      {citation.get('url', 'No URL')}")

        print("\n✅ Exa answer endpoint is working correctly!")

    except Exception as e:
        print(f"\n❌ Error calling Exa API: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
