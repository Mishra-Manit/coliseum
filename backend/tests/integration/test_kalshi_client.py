#!/usr/bin/env python3
"""
Test script for Kalshi API client implementation.

Tests both public endpoints (no auth) and authenticated endpoints (if credentials available).
Run with: python test_kalshi_client.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coliseum.services.kalshi import (
    KalshiClient,
    KalshiConfig,
    KalshiTradingAuth,
    Market,
    Balance,
    Position,
    Order,
    OrderBook,
    KalshiAPIError,
    KalshiAuthError,
)
from coliseum.config import get_settings


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"  ✅ {msg}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"  ❌ {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"  ℹ️  {msg}")


async def test_public_endpoints(client: KalshiClient) -> bool:
    """Test public API endpoints (no authentication required)."""
    print_header("Testing Public Endpoints")
    all_passed = True

    # Test 1: Get exchange status
    try:
        status = await client.get_exchange_status()
        print_success(f"Exchange status: {status.get('exchange_active', 'unknown')}")
    except Exception as e:
        print_error(f"get_exchange_status failed: {e}")
        all_passed = False

    # Test 2: Get events
    try:
        events = await client.get_events(limit=5, status="open")
        print_success(f"Fetched {len(events)} events")
        if events:
            print_info(f"First event: {events[0].get('title', 'N/A')[:50]}...")
    except Exception as e:
        print_error(f"get_events failed: {e}")
        all_passed = False

    # Test 3: Get markets
    markets: list[Market] = []
    try:
        markets = await client.get_markets(limit=5, status="open")
        print_success(f"Fetched {len(markets)} markets")
        if markets:
            m = markets[0]
            print_info(f"First market: {m.ticker} - YES@{m.yes_bid}¢ / NO@{m.no_bid}¢")
    except Exception as e:
        print_error(f"get_markets failed: {e}")
        all_passed = False

    # Test 4: Get markets closing within 24h
    try:
        closing_soon = await client.get_markets_closing_within_hours(hours=24, limit=5)
        print_success(f"Fetched {len(closing_soon)} markets closing within 24h")
    except Exception as e:
        print_error(f"get_markets_closing_within_hours failed: {e}")
        all_passed = False

    # Test 5: Get orderbook for a market (if we have markets)
    if markets:
        try:
            ticker = markets[0].ticker
            orderbook = await client.get_orderbook(ticker, depth=5)
            print_success(f"Fetched orderbook for {ticker}")
            if orderbook.best_yes_bid:
                print_info(f"Best YES bid: {orderbook.best_yes_bid}¢, spread: {orderbook.spread}¢")
        except Exception as e:
            print_error(f"get_orderbook failed: {e}")
            all_passed = False

    return all_passed


async def test_authenticated_endpoints(client: KalshiClient) -> bool:
    """Test authenticated API endpoints (requires API key + private key)."""
    print_header("Testing Authenticated Endpoints")
    all_passed = True

    # Test 1: Get balance
    try:
        balance = await client.get_balance()
        print_success(f"Balance: ${balance.balance_usd:.2f} | Portfolio: ${balance.payout_usd:.2f}")
    except KalshiAuthError as e:
        print_error(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print_error(f"get_balance failed: {e}")
        all_passed = False

    # Test 2: Get positions
    try:
        positions = await client.get_positions()
        print_success(f"Fetched {len(positions)} positions")
        for pos in positions[:3]:  # Show first 3
            side = "YES" if pos.position > 0 else "NO"
            print_info(f"  {pos.market_ticker}: {abs(pos.position)} {side}")
    except Exception as e:
        print_error(f"get_positions failed: {e}")
        all_passed = False

    # Test 3: Get orders
    try:
        orders = await client.get_orders(limit=5)
        print_success(f"Fetched {len(orders)} orders")
        for order in orders[:3]:  # Show first 3
            print_info(f"  {order.order_id[:8]}... {order.status} - {order.ticker}")
    except Exception as e:
        print_error(f"get_orders failed: {e}")
        all_passed = False

    # Test 4: Get fills
    try:
        fills = await client.get_fills(limit=5)
        print_success(f"Fetched {len(fills)} fills")
    except Exception as e:
        print_error(f"get_fills failed: {e}")
        all_passed = False

    return all_passed


async def test_market_model() -> None:
    """Test Market model parsing."""
    print_header("Testing Pydantic Models")

    # Test Market.from_api
    sample_data = {
        "ticker": "TEST-MARKET",
        "event_ticker": "TEST-EVENT",
        "title": "Test Market Title",
        "yes_sub_title": "Test Subtitle",
        "yes_bid": 45,
        "no_bid": 55,
        "yes_ask": 47,
        "no_ask": 53,
        "volume": 12500,
        "volume_24h": 1500,
        "close_time": "2025-01-20T12:00:00Z",
        "status": "open",
        "category": "Test",
    }

    market = Market.from_api(sample_data)
    assert market.ticker == "TEST-MARKET"
    assert market.yes_bid == 45
    assert market.formatted_volume == "12.5K"
    print_success("Market.from_api parsing works")

    # Test Balance model
    balance = Balance(balance=10000, payout=15000)
    assert balance.balance_usd == 100.0
    assert balance.payout_usd == 150.0
    print_success("Balance model conversion works")

    # Test Position model
    position = Position(market_ticker="TEST", position=10, realized_pnl=500)
    assert position.side == "yes"
    assert position.contracts == 10
    print_success("Position model works")

    position_no = Position(market_ticker="TEST", position=-5)
    assert position_no.side == "no"
    assert position_no.contracts == 5
    print_success("Position negative (NO) side works")


async def test_auth_signature() -> None:
    """Test RSA signature generation (without actual API calls)."""
    print_header("Testing RSA Signature Generation")

    # Create a test key (this is just for signature testing, not a real key)
    # In production, this comes from the environment
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        # Generate a test RSA key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        # Test auth class
        auth = KalshiTradingAuth("test-api-key", pem)
        headers = auth.get_auth_headers("GET", "/trade-api/v2/portfolio/balance")

        assert "KALSHI-ACCESS-KEY" in headers
        assert headers["KALSHI-ACCESS-KEY"] == "test-api-key"
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert len(headers["KALSHI-ACCESS-SIGNATURE"]) > 0
        print_success("RSA signature generation works")

        # Test signature format (base64)
        import base64
        try:
            base64.b64decode(headers["KALSHI-ACCESS-SIGNATURE"])
            print_success("Signature is valid base64")
        except Exception:
            print_error("Signature is not valid base64")

    except Exception as e:
        print_error(f"Signature test failed: {e}")


async def main() -> None:
    """Run all tests."""
    print("\n" + "🧪 KALSHI API CLIENT TEST SUITE ".center(60, "="))
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get settings to check if credentials are available
    settings = get_settings()
    rsa_key = settings.get_rsa_private_key()
    has_credentials = bool(settings.kalshi_api_key and rsa_key)

    # Determine mode
    paper_mode = settings.trading.paper_mode
    print(f"\nMode: {'📝 Paper' if paper_mode else '💰 Production'}")
    print(f"Auth: {'🔑 Enabled' if has_credentials else '🔓 Disabled (public only)'}")

    # Test model parsing (no API calls)
    await test_market_model()

    # Test RSA signature generation
    await test_auth_signature()

    # Test with actual API calls
    config = KalshiConfig(paper_mode=paper_mode)

    if has_credentials:
        async with KalshiClient(
            config,
            api_key=settings.kalshi_api_key,
            private_key_pem=rsa_key,
        ) as client:
            public_passed = await test_public_endpoints(client)
            auth_passed = await test_authenticated_endpoints(client)
    else:
        async with KalshiClient(config) as client:
            public_passed = await test_public_endpoints(client)
            auth_passed = True  # Skip auth tests
            print_header("Skipping Authenticated Endpoints")
            print_info("No credentials configured. Set KALSHI_API_KEY and RSA_PRIVATE_KEY in .env")

    # Summary
    print_header("Test Summary")
    print(f"  Public endpoints:       {'✅ PASSED' if public_passed else '❌ FAILED'}")
    if has_credentials:
        print(f"  Authenticated endpoints: {'✅ PASSED' if auth_passed else '❌ FAILED'}")
    else:
        print(f"  Authenticated endpoints: ⏭️ SKIPPED (no credentials)")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
