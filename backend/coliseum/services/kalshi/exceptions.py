"""Kalshi API exceptions."""

from coliseum.services.exceptions import ServiceAPIError


class KalshiAPIError(ServiceAPIError):
    """Base exception for Kalshi API errors."""
    pass


class KalshiAuthError(KalshiAPIError):
    """Authentication failed."""
    pass


class KalshiRateLimitError(KalshiAPIError):
    """Rate limit exceeded."""
    pass


class KalshiNotFoundError(KalshiAPIError):
    """Resource not found."""
    pass
