"""Telegram service exceptions."""


class TelegramServiceError(Exception):
    """Base Telegram service exception (named to avoid collision with python-telegram-bot SDK's TelegramError)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


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
