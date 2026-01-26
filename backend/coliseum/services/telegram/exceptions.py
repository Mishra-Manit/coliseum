"""Telegram service exceptions."""


class TelegramError(Exception):
    """Base Telegram exception."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class TelegramAuthError(TelegramError):
    """Authentication error."""

    pass


class TelegramRateLimitError(TelegramError):
    """Rate limit error."""

    pass


class TelegramNetworkError(TelegramError):
    """Network error."""

    pass


class TelegramConfigError(TelegramError):
    """Config error."""

    pass
