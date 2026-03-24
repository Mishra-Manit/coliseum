"""Telegram notification service."""

from .client import TelegramClient, create_telegram_client
from .config import TelegramConfig
from .exceptions import (
    TelegramAuthError,
    TelegramConfigError,
    TelegramNetworkError,
    TelegramRateLimitError,
    TelegramServiceError,
)
from .models import NotificationResult

__all__ = [
    "TelegramClient",
    "create_telegram_client",
    "TelegramConfig",
    "NotificationResult",
    "TelegramServiceError",
    "TelegramAuthError",
    "TelegramRateLimitError",
    "TelegramNetworkError",
    "TelegramConfigError",
]
