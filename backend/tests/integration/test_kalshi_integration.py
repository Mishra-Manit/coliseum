"""Integration test for Kalshi API client with production credentials.

This script tests:
1. Authentication with RSA signature
2. Fetching account balance
3. Fetching markets and positions
4. Fetching order book data

Run from backend/ directory: 
    source venv/bin/activate && python test_kalshi_integration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

from coliseum.services.kalshi import (
    KalshiClient,
    KalshiConfig,
    KalshiAPIError,
    KalshiAuthError,
)


def load_credentials() -> tuple[str, str]:
    """Load Kalshi API credentials from .env and private key file."""
    # Load .env file
    load_dotenv()
    
    # Production credentials
    api_key = os.getenv("KALSHI_API_KEY", "")
    if not api_key:
        raise ValueError("KALSHI_API_KEY not found in .env")
    
    # Try to load private key from path (production key)
    private_key_path = os.getenv("RSA_PRIVATE_KEY_PATH", "")
    # Also check for production-specific key path
    if not private_key_path:
        private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "")
    
    private_key_content = os.getenv("RSA_PRIVATE_KEY", "")
    
    private_key = ""
    
    if private_key_path:
        # Handle relative paths from backend directory
        key_path = Path(private_key_path)
        if not key_path.is_absolute():
            # Assume relative to project root or wherever .env is, but here we assume relative to this file?
            # actually code previously did: Path(__file__).parent / private_key_path which is relative to test file.
            # But .env usually has paths relative to project root (backend/).
            # Let's try to resolve relative to backend root first
             backend_root = Path(__file__).parent.parent.parent
             key_path = backend_root / private_key_path

        if key_path.is_dir():
            key_path = key_path / "production.pem"

        if key_path.exists():
            private_key = key_path.read_text()
            print(f"✓ Loaded private key from: {key_path}")
        else:
            print(f"⚠ Private key file not found at: {key_path}")
    
    if not private_key and private_key_content:
        private_key = private_key_content.replace("\\n", "\n")
        print("✓ Loaded private key from environment variable")
    
    if not private_key:
        raise ValueError(
            "RSA private key not found. Set RSA_PRIVATE_KEY_PATH or RSA_PRIVATE_KEY in .env"
        )
    
    return api_key, private_key


async def test_public_endpoints(client: KalshiClient) -> None:
    """Test public endpoints that don't require authentication."""
    print("\n=== Testing Public Endpoints ===")
    
    # Test exchange status
    try:
        status = await client.get_exchange_status()
        print(f"✓ Exchange status: {status.get('trading_active', 'unknown')}")
    except KalshiAPIError as e:
        print(f"✗ Failed to get exchange status: {e}")
        raise
    
    # Test fetching markets
    try:
        markets = await client.get_markets(limit=10)
        print(f"✓ Fetched {len(markets)} markets")
        if markets:
            market = markets[0]
            print(f"  Sample market: {market.ticker}")
            print(f"    Title: {market.title[:50]}...")
            print(f"    Yes bid: {market.yes_bid}¢, No bid: {market.no_bid}¢")
            print(f"    Volume: {market.formatted_volume}")
    except KalshiAPIError as e:
        print(f"✗ Failed to get markets: {e}")
        raise
    
    # Test fetching markets closing soon
    try:
        closing_soon = await client.get_markets_closing_within_hours(hours=48, limit=5)
        print(f"✓ Fetched {len(closing_soon)} markets closing within 48h")
    except KalshiAPIError as e:
        print(f"✗ Failed to get markets closing soon: {e}")
        raise
    
    # Test order book (if we have a market)
    if markets:
        try:
            orderbook = await client.get_orderbook(markets[0].ticker, depth=5)
            print(f"✓ Fetched order book for {orderbook.ticker}")
            print(f"  Best yes bid: {orderbook.best_yes_bid}¢")
            print(f"  Best yes ask: {orderbook.best_yes_ask}¢")
            print(f"  Spread: {orderbook.spread}¢")
        except KalshiAPIError as e:
            print(f"✗ Failed to get order book: {e}")
            raise


async def test_authenticated_endpoints(client: KalshiClient) -> None:
    """Test authenticated endpoints that require API key + private key."""
    print("\n=== Testing Authenticated Endpoints ===")
    
    # Test getting balance
    try:
        balance = await client.get_balance()
        print(f"✓ Account balance: ${balance.balance_usd:.2f}")
        print(f"  Portfolio value: ${balance.payout_usd:.2f}")
    except KalshiAuthError as e:
        print(f"✗ Authentication failed: {e}")
        raise
    except KalshiAPIError as e:
        print(f"✗ Failed to get balance: {e}")
        raise
    
    # Test getting positions
    try:
        positions = await client.get_positions()
        print(f"✓ Found {len(positions)} open positions")
        for pos in positions[:5]:  # Show first 5
            side = "YES" if pos.position > 0 else "NO"
            print(f"  {pos.market_ticker}: {abs(pos.position)} {side} contracts")
    except KalshiAPIError as e:
        print(f"✗ Failed to get positions: {e}")
        raise
    
    # Test getting orders
    try:
        orders = await client.get_orders(limit=10)
        resting = [o for o in orders if o.status == "resting"]
        print(f"✓ Found {len(resting)} resting orders out of {len(orders)} total")
    except KalshiAPIError as e:
        print(f"✗ Failed to get orders: {e}")
        raise
    
    # Test getting fills
    try:
        fills = await client.get_fills(limit=10)
        print(f"✓ Found {len(fills)} recent fills")
    except KalshiAPIError as e:
        print(f"✗ Failed to get fills: {e}")
        raise


async def main() -> None:
    """Run all Kalshi API integration tests."""
    print("=" * 60)
    print("Kalshi API Integration Test")
    print("=" * 60)
    
    try:
        # Load credentials
        api_key, private_key = load_credentials()
        print(f"✓ Loaded API key: {api_key[:8]}...")
        
        # Create client
        config = KalshiConfig()
        print(f"✓ Using base URL: {config.base_url}")
        
        async with KalshiClient(config, api_key, private_key) as client:
            # Test public endpoints first
            await test_public_endpoints(client)
            
            # Test authenticated endpoints
            await test_authenticated_endpoints(client)
        
        print("\n" + "=" * 60)
        print("✅ ALL KALSHI API TESTS PASSED")
        print("=" * 60)
        print("\nKalshi API client is ready for trading operations!\n")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
