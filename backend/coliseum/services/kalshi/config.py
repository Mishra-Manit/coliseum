from pydantic import BaseModel


class KalshiConfig(BaseModel):
    """Configuration for Kalshi API client."""

    base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    paper_mode: bool = True
    paper_balance_usd: float = 100.0
    timeout_seconds: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    default_page_size: int = 200
    max_retries: int = 3
