from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

import httpx

from .auth import KalshiTradingAuth
from .config import KalshiConfig
from .exceptions import (
    KalshiAPIError,
    KalshiAuthError,
    KalshiNotFoundError,
    KalshiRateLimitError,
)
from .models import Balance, Market, Order, OrderBook, OrderBookLevel, Position

logger = logging.getLogger(__name__)


class KalshiClient:
    def __init__(
        self,
        config: KalshiConfig | None = None,
        api_key: str | None = None,
        private_key_pem: str | None = None,
    ):
        self.config = config or KalshiConfig()
        self._client: httpx.AsyncClient | None = None
        self._paper_orders: dict[str, Order] = {}
        self._paper_positions: dict[str, Position] = {}
        self._paper_balance_cents = int(self.config.paper_balance_usd * 100)

        if api_key and private_key_pem:
            self.auth = KalshiTradingAuth(api_key, private_key_pem)
        else:
            self.auth = None

        logger.info(
            f"Initialized KalshiClient (paper_mode={self.config.paper_mode}, "
            f"auth={'enabled' if self.auth else 'disabled'})"
        )

    async def __aenter__(self) -> KalshiClient:
        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
        )
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            limits=limits,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Closed KalshiClient")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "KalshiClient must be used as async context manager"
            )
        return self._client

    def _require_auth(self) -> KalshiTradingAuth:
        if self.auth is None:
            raise KalshiAuthError(
                "Authentication required. Provide api_key and private_key_pem."
            )
        return self.auth

    def _paper_enabled(self) -> bool:
        return self.config.paper_mode and self.auth is None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        auth_required: bool = False,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}

        if auth_required:
            auth = self._require_auth()
            full_path = f"/trade-api/v2/{endpoint.lstrip('/')}"
            headers.update(auth.get_auth_headers(method, full_path))

        retry_count = 0
        last_error: Exception | None = None

        while retry_count < self.config.max_retries:
            try:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                    headers=headers,
                )

                if response.status_code == 401:
                    raise KalshiAuthError("Authentication failed", status_code=401)
                elif response.status_code == 404:
                    raise KalshiNotFoundError(
                        f"Resource not found: {endpoint}", status_code=404
                    )
                elif response.status_code == 429:
                    wait_time = 2 ** retry_count
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                elif response.status_code >= 500:
                    wait_time = 2 ** retry_count
                    logger.warning(
                        f"Server error {response.status_code}, "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                retry_count += 1
                if retry_count < self.config.max_retries:
                    logger.warning(f"Timeout, retrying ({retry_count})...")
                    await asyncio.sleep(2)

            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Network error: {e}")
                break

        raise KalshiAPIError(
            f"Request failed after {retry_count} retries: {last_error}"
        )

    async def _paginate(
        self,
        endpoint: str,
        params: dict[str, Any],
        limit: int,
        result_key: str,
        auth_required: bool = False,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        cursor: str | None = None

        while len(all_items) < limit:
            current_params = params.copy()
            if cursor:
                current_params["cursor"] = cursor

            data = await self._request(
                "GET", endpoint, params=current_params, auth_required=auth_required
            )

            items = data.get(result_key, [])
            all_items.extend(items)

            cursor = data.get("cursor")
            if not cursor or not items:
                break

        return all_items[:limit]

    async def get_exchange_status(self) -> dict[str, Any]:
        return await self._request("GET", "exchange/status")

    async def get_events(
        self,
        limit: int = 100,
        status: str = "open",
        with_nested_markets: bool = False,
    ) -> list[dict[str, Any]]:
        params = {
            "limit": min(limit, self.config.default_page_size),
            "status": status,
            "with_nested_markets": str(with_nested_markets).lower(),
        }
        return await self._paginate("events", params, limit, "events")

    async def get_markets(
        self,
        limit: int = 100,
        status: str = "open",
        event_ticker: str | None = None,
    ) -> list[Market]:
        params: dict[str, Any] = {
            "limit": min(limit, self.config.default_page_size),
            "status": status,
        }
        if event_ticker:
            params["event_ticker"] = event_ticker

        raw_markets = await self._paginate("markets", params, limit, "markets")
        return [Market.from_api(m) for m in raw_markets]

    async def get_markets_for_event(self, event_ticker: str) -> list[Market]:
        data = await self._request("GET", f"events/{event_ticker}")
        raw_markets = data.get("markets", [])
        return [Market.from_api(m) for m in raw_markets]

    async def get_market(self, ticker: str) -> Market:
        data = await self._request("GET", f"markets/{ticker}")
        return Market.from_api(data.get("market", data))

    async def get_markets_closing_within_hours(
        self,
        hours: int = 24,
        limit: int = 1000,
        status: str = "open",
    ) -> list[Market]:
        current_time = int(time.time())
        max_close_ts = current_time + (hours * 3600)

        params = {
            "limit": min(limit, 200),
            "status": status,
            "min_close_ts": current_time,
            "max_close_ts": max_close_ts,
        }

        raw_markets = await self._paginate("markets", params, limit, "markets")
        return [Market.from_api(m) for m in raw_markets]

    async def get_orderbook(self, ticker: str, depth: int = 10) -> OrderBook:
        params = {"depth": depth}
        data = await self._request("GET", f"markets/{ticker}/orderbook", params=params)

        orderbook = data.get("orderbook", {})

        def parse_levels(levels: list[list[int]] | None) -> list[OrderBookLevel]:
            if not levels:
                return []
            return [OrderBookLevel(price=lvl[0], count=lvl[1]) for lvl in levels]

        return OrderBook(
            ticker=ticker,
            yes_bids=parse_levels(orderbook.get("yes", [])),
            yes_asks=parse_levels(orderbook.get("no", [])),  # Kalshi inverts this
            no_bids=parse_levels(orderbook.get("no", [])),
            no_asks=parse_levels(orderbook.get("yes", [])),
        )

    async def get_balance(self) -> Balance:
        if self._paper_enabled():
            return Balance(balance=self._paper_balance_cents, payout=0)
        data = await self._request("GET", "portfolio/balance", auth_required=True)
        return Balance(
            balance=data.get("balance", 0),
            payout=data.get("payout", 0),
        )

    async def get_positions(
        self,
        ticker: str | None = None,
        event_ticker: str | None = None,
        count_filter: str = "position",
    ) -> list[Position]:
        if self._paper_enabled():
            positions = list(self._paper_positions.values())
            if ticker:
                positions = [pos for pos in positions if pos.market_ticker == ticker]
            if event_ticker:
                positions = [pos for pos in positions if pos.event_ticker == event_ticker]
            return positions
        params: dict[str, Any] = {"count_filter": count_filter}
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker

        data = await self._request(
            "GET", "portfolio/positions", params=params, auth_required=True
        )

        positions = []
        for pos in data.get("market_positions", []):
            positions.append(
                Position(
                    market_ticker=pos.get("ticker", ""),
                    event_ticker=pos.get("event_ticker", ""),
                    event_exposure=pos.get("event_exposure", 0),
                    position=pos.get("position", 0),
                    realized_pnl=pos.get("realized_pnl", 0),
                    resting_orders_count=pos.get("resting_orders_count", 0),
                    total_traded=pos.get("total_traded", 0),
                )
            )
        return positions

    async def get_orders(
        self,
        ticker: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Order]:
        if self._paper_enabled():
            orders = list(self._paper_orders.values())
            if ticker:
                orders = [order for order in orders if order.ticker == ticker]
            if status:
                orders = [order for order in orders if order.status == status]
            return orders[:limit]
        params: dict[str, Any] = {"limit": min(limit, 200)}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status

        raw_orders = await self._paginate(
            "portfolio/orders", params, limit, "orders", auth_required=True
        )

        return [self._parse_order(o) for o in raw_orders]

    async def get_order_status(self, order_id: str) -> Order:
        if self._paper_enabled():
            return self._paper_orders.get(
                order_id,
                Order(order_id=order_id, status="canceled", remaining_count=0),
            )
        data = await self._request(
            "GET", f"portfolio/orders/{order_id}", auth_required=True
        )
        return self._parse_order(data.get("order", data))

    async def place_order(
        self,
        ticker: str,
        side: Literal["yes", "no"],
        action: Literal["buy", "sell"],
        count: int,
        type: Literal["limit"] = "limit",
        yes_price: int | None = None,
        no_price: int | None = None,
        client_order_id: str | None = None,
        expiration_time: datetime | None = None,
    ) -> Order:
        if type != "limit":
            raise ValueError("Only limit orders are allowed.")

        if yes_price is None and no_price is None:
            raise ValueError("Must specify yes_price or no_price for limit orders")

        if self._paper_enabled():
            price_cents = yes_price if yes_price is not None else no_price or 0
            order_id = f"paper_{uuid4().hex[:8]}"
            order = Order(
                order_id=order_id,
                ticker=ticker,
                side=side,
                type="limit",
                status="executed",
                yes_price=yes_price or 0,
                no_price=no_price or 0,
                remaining_count=0,
                action=action,
                client_order_id=client_order_id or "",
                maker_fill_count=count,
                maker_fill_cost=price_cents * count,
            )
            self._paper_orders[order_id] = order

            if action == "buy":
                self._paper_balance_cents = max(
                    0, self._paper_balance_cents - (price_cents * count)
                )
            elif action == "sell":
                self._paper_balance_cents += price_cents * count

            delta = count if side == "yes" else -count
            if action == "sell":
                delta = -delta
            position = self._paper_positions.get(
                ticker, Position(market_ticker=ticker)
            )
            position.position += delta
            position.total_traded += count
            position.event_exposure = position.position
            self._paper_positions[ticker] = position
            return order

        order_data: dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": type,
        }

        if yes_price is not None:
            order_data["yes_price"] = yes_price
        if no_price is not None:
            order_data["no_price"] = no_price
        if client_order_id:
            order_data["client_order_id"] = client_order_id
        if expiration_time:
            order_data["expiration_time"] = expiration_time.isoformat()

        logger.info(
            f"Placing order: {action} {count} {side} contracts on {ticker} "
            f"@ {yes_price or no_price}¢"
        )

        data = await self._request(
            "POST", "portfolio/orders", json_data=order_data, auth_required=True
        )
        return self._parse_order(data.get("order", data))

    async def cancel_order(self, order_id: str) -> Order:
        logger.info(f"Cancelling order: {order_id}")
        if self._paper_enabled():
            order = self._paper_orders.get(
                order_id,
                Order(order_id=order_id, status="canceled", remaining_count=0),
            )
            order.status = "canceled"
            self._paper_orders[order_id] = order
            return order
        data = await self._request(
            "DELETE", f"portfolio/orders/{order_id}", auth_required=True
        )
        return self._parse_order(data.get("order", data))

    async def amend_order(
        self,
        order_id: str,
        count: int | None = None,
        price: int | None = None,
    ) -> Order:
        amend_data: dict[str, Any] = {}
        if count is not None:
            amend_data["count"] = count
        if price is not None:
            amend_data["price"] = price

        logger.info(f"Amending order {order_id}: {amend_data}")
        if self._paper_enabled():
            order = self._paper_orders.get(
                order_id,
                Order(order_id=order_id, status="resting"),
            )
            if price is not None:
                if order.side == "yes":
                    order.yes_price = price
                else:
                    order.no_price = price
            if count is not None:
                order.remaining_count = count
            self._paper_orders[order_id] = order
            return order
        data = await self._request(
            "POST",
            f"portfolio/orders/{order_id}/amend",
            json_data=amend_data,
            auth_required=True,
        )
        return self._parse_order(data.get("order", data))

    async def get_fills(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if self._paper_enabled():
            return []
        params: dict[str, Any] = {"limit": min(limit, 200)}
        if ticker:
            params["ticker"] = ticker
        if order_id:
            params["order_id"] = order_id

        return await self._paginate(
            "portfolio/fills", params, limit, "fills", auth_required=True
        )

    def _parse_order(self, data: dict[str, Any]) -> Order:
        return Order(
            order_id=data.get("order_id", ""),
            ticker=data.get("ticker", ""),
            event_ticker=data.get("event_ticker", ""),
            side=data.get("side", "yes"),
            type=data.get("type", "limit"),
            status=data.get("status", "resting"),
            yes_price=data.get("yes_price", 0),
            no_price=data.get("no_price", 0),
            remaining_count=data.get("remaining_count", 0),
            queue_position=data.get("queue_position"),
            expiration_time=data.get("expiration_time"),
            action=data.get("action", ""),
            created_time=data.get("created_time"),
            updated_time=data.get("updated_time"),
            client_order_id=data.get("client_order_id", ""),
            order_group_id=data.get("order_group_id", ""),
            taker_fill_count=data.get("taker_fill_count", 0),
            taker_fill_cost=data.get("taker_fill_cost", 0),
            maker_fill_count=data.get("maker_fill_count", 0),
            maker_fill_cost=data.get("maker_fill_cost", 0),
        )


def create_kalshi_client(
    paper_mode: bool = True,
    api_key: str | None = None,
    private_key_pem: str | None = None,
) -> KalshiClient:
    config = KalshiConfig(paper_mode=paper_mode)
    return KalshiClient(config, api_key, private_key_pem)
