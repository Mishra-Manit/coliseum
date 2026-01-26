"""Telegram service config."""

from pydantic import BaseModel


class TelegramConfig(BaseModel):
    """Telegram config."""

    bot_token: str = ""
    default_chat_id: str = ""
    max_retries: int = 3
    timeout_seconds: float = 30.0
    parse_mode: str = "HTML"
