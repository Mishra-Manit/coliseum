from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Market(BaseModel):
    ticker: str
    event_ticker: str = ""
    title: str = ""
    subtitle: str = ""
    yes_bid: int = 0
    no_bid: int = 0
    yes_ask: int = 0
    no_ask: int = 0
    volume: int = 0
    volume_24h: int = 0
    open_interest: int = 0
    close_time: datetime | None = None
    status: str = "unknown"
    category: str = "N/A"
    result: str | None = None

    @field_validator("close_time", mode="before")
    @classmethod
    def parse_close_time(cls, v: Any) -> datetime | None:
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @property
    def formatted_close_time(self) -> str:
        if not self.close_time:
            return "N/A"
        return self.close_time.strftime("%b %d, %I:%M%p")

    @property
    def formatted_volume(self) -> str:
        if self.volume >= 1_000_000:
            return f"{self.volume / 1_000_000:.1f}M"
        elif self.volume >= 1_000:
            return f"{self.volume / 1_000:.1f}K"
        return str(self.volume)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Market:
        return cls(
            ticker=data.get("ticker", ""),
            event_ticker=data.get("event_ticker", ""),
            title=data.get("title", ""),
            subtitle=data.get("yes_sub_title", data.get("subtitle", "")),
            yes_bid=data.get("yes_bid", 0),
            no_bid=data.get("no_bid", 0),
            yes_ask=data.get("yes_ask", 0),
            no_ask=data.get("no_ask", 0),
            volume=data.get("volume", 0),
            volume_24h=data.get("volume_24h", 0),
            open_interest=data.get("open_interest", 0),
            close_time=data.get("close_time"),
            status=data.get("status", "unknown"),
            category=data.get("category", "N/A"),
            result=data.get("result"),
        )


class Balance(BaseModel):
    balance: int = 0
    payout: int = 0

    @property
    def balance_usd(self) -> float:
        return self.balance / 100

    @property
    def payout_usd(self) -> float:
        return self.payout / 100


class Position(BaseModel):
    market_ticker: str
    event_ticker: str = ""
    event_exposure: int = 0
    position: int = 0
    realized_pnl: int = 0
    resting_orders_count: int = 0
    total_traded: int = 0

    @property
    def side(self) -> Literal["yes", "no"] | None:
        if self.position > 0:
            return "yes"
        elif self.position < 0:
            return "no"
        return None

    @property
    def contracts(self) -> int:
        return abs(self.position)


class OrderStatus(str, Enum):
    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class Order(BaseModel):
    order_id: str
    ticker: str = ""
    event_ticker: str = ""
    side: Literal["yes", "no"] = "yes"
    type: Literal["limit", "market"] = "limit"
    status: str = "resting"
    yes_price: int = 0
    no_price: int = 0
    remaining_count: int = 0
    queue_position: int | None = None
    expiration_time: datetime | None = None
    action: str = ""
    created_time: datetime | None = None
    updated_time: datetime | None = None
    client_order_id: str = ""
    order_group_id: str = ""
    taker_fill_count: int = 0
    taker_fill_cost: int = 0
    maker_fill_count: int = 0
    maker_fill_cost: int = 0

    @field_validator("created_time", "updated_time", "expiration_time", mode="before")
    @classmethod
    def parse_time(cls, v: Any) -> datetime | None:
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @property
    def fill_count(self) -> int:
        return self.taker_fill_count + self.maker_fill_count

    @property
    def is_filled(self) -> bool:
        return self.status == "executed" and self.remaining_count == 0

    @property
    def is_partial(self) -> bool:
        return self.fill_count > 0 and self.remaining_count > 0


class OrderBookLevel(BaseModel):
    price: int
    count: int


class OrderBook(BaseModel):
    ticker: str
    yes_bids: list[OrderBookLevel] = Field(default_factory=list)
    yes_asks: list[OrderBookLevel] = Field(default_factory=list)
    no_bids: list[OrderBookLevel] = Field(default_factory=list)
    no_asks: list[OrderBookLevel] = Field(default_factory=list)

    @property
    def best_yes_bid(self) -> int | None:
        if self.yes_bids:
            return max(level.price for level in self.yes_bids)
        return None

    @property
    def best_yes_ask(self) -> int | None:
        if self.yes_asks:
            return min(level.price for level in self.yes_asks)
        return None

    @property
    def spread(self) -> int | None:
        if self.best_yes_bid and self.best_yes_ask:
            return self.best_yes_ask - self.best_yes_bid
        return None
