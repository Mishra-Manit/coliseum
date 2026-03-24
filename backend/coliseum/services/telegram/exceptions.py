"""Telegram service exceptions."""

from coliseum.services.exceptions import ServiceAPIError


class TelegramServiceError(ServiceAPIError):
    """Base Telegram service exception (named to avoid collision with python-telegram-bot SDK's TelegramError)."""
    pass


class TelegramAuthError(TelegramServiceError):
    """Authentication error."""
    pass


class TelegramRateLimitError(TelegramServiceError):
    """Rate limit error."""
    pass


class TelegramNetworkError(TelegramServiceError):
    """Network error."""
    pass


class TelegramConfigError(TelegramServiceError):
    """Config error."""
    pass
