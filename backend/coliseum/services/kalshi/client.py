from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
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

        if api_key and private_key_pem:
            self.auth = KalshiTradingAuth(api_key, private_key_pem)
        else:
            self.auth = None

        if self.auth:
            auth_status = "enabled"
        else:
            auth_status = "disabled"

        logger.info(f"Initialized KalshiClient (auth={auth_status})")

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
                elif response.status_code >= 400:
                    # Surface the Kalshi error body (e.g. deprecated_v1_order_endpoint)
                    # instead of a bare HTTPStatusError that escapes our except clauses.
                    raise KalshiAPIError(
                        f"Kalshi API error {response.status_code} on "
                        f"{method} {endpoint}: {response.text}",
                        status_code=response.status_code,
                    )

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
        series_ticker: str | None = None,
    ) -> list[Market]:
        params: dict[str, Any] = {
            "limit": min(limit, self.config.default_page_size),
            "status": status,
        }
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker

        raw_markets = await self._paginate("markets", params, limit, "markets")
        return [Market.from_api(m) for m in raw_markets]

    async def get_event(self, event_ticker: str) -> dict[str, Any]:
        """Fetch event metadata for a given event ticker."""
        data = await self._request("GET", f"events/{event_ticker}")
        return data.get("event", {})

    async def get_markets_for_event(self, event_ticker: str) -> list[Market]:
        data = await self._request("GET", f"events/{event_ticker}")
        raw_markets = data.get("markets", [])
        return [Market.from_api(m) for m in raw_markets]

    async def get_market(self, ticker: str) -> Market:
        data = await self._request("GET", f"markets/{ticker}")
        return Market.from_api(data.get("market", data))

    async def get_markets_closing_in_range(
        self,
        min_hours: int = 0,
        max_hours: int = 24,
        limit: int = 10000,
        status: str = "open",
        series_tickers: Sequence[str] | None = None,
    ) -> list[Market]:
        """Fetch markets closing within a specified hour range from now.

        When series_tickers is given, each series is queried separately. An
        unscoped /markets scan is dominated by a handful of enormous parlay
        series (KXMVESPORTSMULTIGAMEEXTENDED alone exceeds 16k open markets),
        so a blind bulk page-walk exhausts its limit before reaching anything
        tradable. Scoping by series is the only way to see the whole shortlist.
        """
        current_time = int(time.time())
        base_params: dict[str, Any] = {
            "status": status,
            "min_close_ts": current_time + (min_hours * 3600),
            "max_close_ts": current_time + (max_hours * 3600),
        }

        if not series_tickers:
            params = {**base_params, "limit": min(limit, self.config.default_page_size)}
            raw_markets = await self._paginate("markets", params, limit, "markets")
            return [Market.from_api(m) for m in raw_markets]

        per_series = max(1, limit // len(series_tickers))
        markets: list[Market] = []
        seen: set[str] = set()
        for series in series_tickers:
            params = {
                **base_params,
                "series_ticker": series,
                "limit": min(per_series, self.config.default_page_size),
            }
            try:
                raw = await self._paginate("markets", params, per_series, "markets")
            except KalshiAPIError as e:
                # One dead series must not blank the whole scan.
                logger.warning(f"Series fetch failed for {series}: {e}")
                continue
            for m in raw:
                ticker = m.get("ticker", "")
                if ticker and ticker not in seen:
                    seen.add(ticker)
                    markets.append(Market.from_api(m))

        return markets

    async def get_orderbook(self, ticker: str, depth: int = 10) -> OrderBook:
        """Fetch the book. V2 returns orderbook_fp with dollar-string levels.

        Only resting bids are published, one array per outcome. The opposing
        ask is the mirror of the other outcome's bid: a resting bid to buy NO
        at 95c is the only thing a YES buyer can lift, and it costs them 5c.
        """
        params = {"depth": depth}
        data = await self._request("GET", f"markets/{ticker}/orderbook", params=params)

        book = data.get("orderbook_fp") or {}
        yes_raw = book.get("yes_dollars") or []
        no_raw = book.get("no_dollars") or []

        def parse_levels(levels: Any, invert: bool = False) -> list[OrderBookLevel]:
            parsed: list[OrderBookLevel] = []
            for level in levels or []:
                if not level or len(level) < 2:
                    continue
                price_cents = round(float(level[0]) * 100)
                count = int(float(level[1]))
                if invert:
                    price_cents = 100 - price_cents
                if 0 < price_cents < 100:
                    parsed.append(OrderBookLevel(price=price_cents, count=count))
            return parsed

        return OrderBook(
            ticker=ticker,
            yes_bids=parse_levels(yes_raw),
            yes_asks=parse_levels(no_raw, invert=True),
            no_bids=parse_levels(no_raw),
            no_asks=parse_levels(yes_raw, invert=True),
        )

    async def get_balance(self) -> Balance:
        data = await self._request("GET", "portfolio/balance", auth_required=True)
        # The integer `balance` field truncates sub-cent amounts (14.1880 -> 1418);
        # prefer the dollar string so fee dust does not silently accumulate.
        balance_dollars = data.get("balance_dollars")
        if balance_dollars is not None:
            balance_cents = round(float(balance_dollars) * 100)
        else:
            balance_cents = data.get("balance", 0)

        return Balance(
            balance=balance_cents,
            portfolio_value=data.get("portfolio_value", 0),
        )

    async def get_positions(
        self,
        ticker: str | None = None,
        event_ticker: str | None = None,
        count_filter: str = "position",
    ) -> list[Position]:
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
            def _c(key: str) -> int:
                v = pos.get(key)
                if v is not None:
                    return round(float(v) * 100)
                else:
                    return 0

            positions.append(
                Position(
                    market_ticker=pos.get("ticker", ""),
                    # V2 market_positions carries no event_ticker; derive it from
                    # the market ticker (KXRT-SPI-92 -> KXRT-SPI) so downstream
                    # reconciliation can still group by event.
                    event_ticker=pos.get("ticker", "").rpartition("-")[0],
                    event_exposure=_c("market_exposure_dollars"),
                    position=int(float(pos.get("position_fp") or 0)),
                    realized_pnl=_c("realized_pnl_dollars"),
                    resting_orders_count=pos.get("resting_orders_count") or 0,
                    fees_paid=_c("fees_paid_dollars"),
                    total_traded=_c("total_traded_dollars"),
                )
            )
        return positions

    async def get_orders(
        self,
        ticker: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Order]:
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
        data = await self._request(
            "GET", f"portfolio/orders/{order_id}", auth_required=True
        )
        return self._parse_order(data.get("order", data))

    @staticmethod
    def _to_book_order(
        side: Literal["yes", "no"],
        action: Literal["buy", "sell"],
        price_cents: int,
    ) -> tuple[Literal["bid", "ask"], int]:
        """Map yes/no + buy/sell to the V2 single-book model.

        V2 quotes everything from the YES side: bid = buy YES, ask = sell YES.
        A NO order at price q is the mirrored YES order at 100 - q.
        """
        if side == "yes":
            if action == "buy":
                book_side: Literal["bid", "ask"] = "bid"
            else:
                book_side = "ask"
            return book_side, price_cents

        if action == "buy":
            book_side = "ask"
        else:
            book_side = "bid"
        return book_side, 100 - price_cents

    def _order_from_v2_response(
        self,
        data: dict[str, Any],
        ticker: str,
        side: Literal["yes", "no"],
        action: str,
    ) -> Order:
        """Build an Order from a V2 create/amend response (partial shape)."""
        def _i(key: str) -> int:
            v = data.get(key)
            if v is not None:
                return int(float(v))
            else:
                return 0

        fill_count = _i("fill_count")
        remaining_count = _i("remaining_count")
        if remaining_count == 0 and fill_count > 0:
            status = "executed"
        else:
            status = "resting"

        return Order(
            order_id=data.get("order_id", ""),
            ticker=ticker,
            side=side,
            status=status,
            remaining_count=remaining_count,
            fill_count=fill_count,
            action=action,
            client_order_id=data.get("client_order_id", "") or "",
        )

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

        if side == "yes":
            if yes_price is not None:
                price_cents = yes_price
            else:
                price_cents = 100 - no_price
        else:
            if no_price is not None:
                price_cents = no_price
            else:
                price_cents = 100 - yes_price

        if not 1 <= price_cents <= 99:
            raise ValueError(f"Order price {price_cents}¢ outside valid 1-99¢ range")

        book_side, book_price_cents = self._to_book_order(side, action, price_cents)

        order_data: dict[str, Any] = {
            "ticker": ticker,
            "side": book_side,
            "count": f"{count:.2f}",
            "price": f"{book_price_cents / 100:.4f}",
            "time_in_force": "good_till_canceled",
            "self_trade_prevention_type": "taker_at_cross",
        }
        if client_order_id:
            order_data["client_order_id"] = client_order_id
        if expiration_time:
            order_data["expiration_time"] = int(expiration_time.timestamp())

        logger.info(
            f"Placing V2 order: {action} {count} {side} contracts on {ticker} "
            f"@ {price_cents}¢ (book: {book_side} @ {book_price_cents}¢)"
        )

        data = await self._request(
            "POST", "portfolio/events/orders", json_data=order_data, auth_required=True
        )
        return self._order_from_v2_response(data, ticker, side, action)

    async def cancel_order(self, order_id: str) -> Order:
        """Cancel a resting order. A missing order is treated as already terminal.

        The reprice loop cancels orders that may have filled moments earlier; V2
        returns 404 once an order leaves the book, and that is the state cancel
        was asking for. Raising there would fail a trade that actually succeeded,
        so the caller re-polls status to learn the real outcome.
        """
        logger.info(f"Cancelling order: {order_id}")
        try:
            data = await self._request(
                "DELETE", f"portfolio/events/orders/{order_id}", auth_required=True
            )
        except KalshiNotFoundError:
            logger.info(f"Order {order_id} no longer resting; treating as canceled")
            return Order(order_id=order_id, status="canceled")

        return Order(
            order_id=data.get("order_id", order_id),
            status="canceled",
            client_order_id=data.get("client_order_id", "") or "",
        )

    async def amend_order(
        self,
        order_id: str,
        ticker: str,
        side: Literal["yes", "no"],
        action: Literal["buy", "sell"],
        count: int,
        price: int,
    ) -> Order:
        """Amend a resting order. Price is in cents of the order's own side."""
        if not 1 <= price <= 99:
            raise ValueError(f"Amend price {price}¢ outside valid 1-99¢ range")

        book_side, book_price_cents = self._to_book_order(side, action, price)
        amend_data: dict[str, Any] = {
            "ticker": ticker,
            "side": book_side,
            "count": f"{count:.2f}",
            "price": f"{book_price_cents / 100:.4f}",
        }

        logger.info(f"Amending order {order_id}: {amend_data}")
        data = await self._request(
            "POST",
            f"portfolio/events/orders/{order_id}/amend",
            json_data=amend_data,
            auth_required=True,
        )
        return self._order_from_v2_response(data, ticker, side, action)

    async def get_fills(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": min(limit, 200)}
        if ticker:
            params["ticker"] = ticker
        if order_id:
            params["order_id"] = order_id

        return await self._paginate(
            "portfolio/fills", params, limit, "fills", auth_required=True
        )

    def _parse_order(self, data: dict[str, Any]) -> Order:
        def _c(key: str) -> int:
            """Convert FixedPointDollars string to cents int."""
            v = data.get(key)
            if v is not None:
                return round(float(v) * 100)
            else:
                return 0

        def _i(key: str) -> int:
            """Convert FixedPointCount string to int."""
            v = data.get(key)
            if v is not None:
                return int(float(v))
            else:
                return 0

        # V2 reports the order from the single YES book: `side`/`action` describe
        # the book leg, so a "buy NO" comes back as side=yes/action=sell. The
        # outcome the order actually acquires lives in `outcome_side`, and the
        # user-facing action is recovered by inverting _to_book_order.
        outcome_side = data.get("outcome_side") or data.get("side") or "yes"
        book_side = data.get("book_side", "")
        if book_side:
            if (outcome_side == "yes") == (book_side == "bid"):
                action = "buy"
            else:
                action = "sell"
        else:
            action = data.get("action", "")

        return Order(
            order_id=data.get("order_id", ""),
            ticker=data.get("ticker", ""),
            event_ticker=data.get("event_ticker", ""),
            side=outcome_side,
            type=data.get("type", "limit"),
            status=data.get("status", "resting"),
            yes_price=_c("yes_price_dollars"),
            no_price=_c("no_price_dollars"),
            remaining_count=_i("remaining_count_fp"),
            fill_count=_i("fill_count_fp"),
            queue_position=data.get("queue_position"),
            expiration_time=data.get("expiration_time"),
            action=action,
            created_time=data.get("created_time"),
            updated_time=data.get("last_update_time") or data.get("updated_time"),
            client_order_id=data.get("client_order_id", ""),
            order_group_id=data.get("order_group_id") or "",
            taker_fill_cost=_c("taker_fill_cost_dollars"),
            maker_fill_cost=_c("maker_fill_cost_dollars"),
        )
