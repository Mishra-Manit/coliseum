from pydantic import BaseModel


class KalshiConfig(BaseModel):
    """Configuration for Kalshi API client."""

    production_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    demo_base_url: str = "https://demo-api.kalshi.co/trade-api/v2"
    paper_mode: bool = True
    timeout_seconds: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    default_page_size: int = 200
    max_retries: int = 3

    @property
    def base_url(self) -> str:
        """Return appropriate base URL based on paper_mode."""
        return self.demo_base_url if self.paper_mode else self.production_base_url
