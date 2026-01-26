"""Telegram notification client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Bot
from telegram.error import TelegramError

from .config import TelegramConfig
from .exceptions import (
    TelegramAuthError,
    TelegramConfigError,
)
from .models import NotificationResult

logger = logging.getLogger(__name__)


class TelegramClient:
    """Async Telegram notification client."""

    def __init__(
        self,
        config: TelegramConfig | None = None,
        bot_token: str | None = None,
        default_chat_id: str | None = None,
    ):
        """Initialize Telegram client."""
        self.config = config or TelegramConfig()

        if bot_token:
            self.config.bot_token = bot_token
        if default_chat_id:
            self.config.default_chat_id = default_chat_id

        if not self.config.bot_token:
            raise TelegramConfigError(
                "bot_token is required. Provide via config or constructor."
            )

        self._bot: Bot | None = None
        logger.info("Initialized TelegramClient")

    async def __aenter__(self) -> TelegramClient:
        """Enter async context manager."""
        try:
            self._bot = Bot(token=self.config.bot_token)
            bot_info = await self._bot.get_me()
            logger.info(f"Connected to Telegram bot: @{bot_info.username}")
        except TelegramError as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise TelegramAuthError(f"Invalid bot token: {e}")

        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        if self._bot:
            logger.info("Closed TelegramClient")

    @property
    def bot(self) -> Bot:
        """Return bot instance."""
        if self._bot is None:
            raise RuntimeError(
                "TelegramClient must be used as async context manager"
            )
        return self._bot

    async def send_alert(
        self,
        message: str,
        chat_id: str | None = None,
    ) -> NotificationResult:
        """Send a message with a single retry."""
        target_chat_id = chat_id or self.config.default_chat_id

        if not target_chat_id:
            raise TelegramConfigError(
                "chat_id is required. Provide via config or method argument."
            )

        retry_count = 0
        last_error: str | None = None

        for attempt in range(2):
            try:
                logger.info(
                    f"Sending Telegram message to {target_chat_id} "
                    f"(attempt {attempt + 1}/2)"
                )

                telegram_message = await self.bot.send_message(
                    chat_id=target_chat_id,
                    text=message,
                    parse_mode=self.config.parse_mode,
                )

                logger.info(
                    f"Message sent successfully to {target_chat_id} "
                    f"(message_id: {telegram_message.message_id})"
                )

                return NotificationResult(
                    success=True,
                    message_id=telegram_message.message_id,
                    recipient=target_chat_id,
                    retry_count=retry_count,
                )

            except TelegramError as e:
                last_error = e.message or "Telegram error"
                logger.warning(
                    f"Telegram send failed (attempt {attempt + 1}/2): "
                    f"{last_error}"
                )
            except Exception as e:
                last_error = str(e) or "Unexpected error"
                logger.warning(
                    f"Unexpected error sending to {target_chat_id} "
                    f"(attempt {attempt + 1}/2): {last_error}"
                )

            if attempt == 0:
                await asyncio.sleep(2)
                retry_count = 1

        return NotificationResult(
            success=False,
            recipient=target_chat_id,
            error=last_error or "Message send failed",
            retry_count=retry_count,
        )


def create_telegram_client(
    bot_token: str | None = None,
    chat_id: str | None = None,
    config: TelegramConfig | None = None,
) -> TelegramClient:
    """Create a TelegramClient instance."""
    return TelegramClient(
        config=config,
        bot_token=bot_token,
        default_chat_id=chat_id,
    )
