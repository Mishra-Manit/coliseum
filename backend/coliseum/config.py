"""Configuration management using Pydantic Settings."""

import logging
from datetime import date as date_type
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from coliseum.runtime import bootstrap_runtime

logger = logging.getLogger(__name__)


class TradingConfig(BaseModel):
    """Trading operational parameters."""

    paper_mode: bool = True
    contracts: int = Field(default=1, ge=1)


class ScoutConfig(BaseModel):
    """Scout agent market filtering parameters."""

    min_close_hours: int = 0
    max_close_hours: int = 48
    min_price: int = 92
    max_price: int = 96
    max_spread_cents: int = 3
    min_volume: int = 5000
    market_fetch_limit: int = 10000


class GuardianConfig(BaseModel):
    """Guardian agent monitoring parameters."""

    stop_loss_price: float = 0.80


class ExecutionConfig(BaseModel):
    """Order execution and slippage parameters."""

    max_slippage_pct: float = 0.05
    order_check_interval_seconds: int = 120
    max_reprice_attempts: int = 3
    reprice_aggression: float = 0.02
    min_fill_pct_to_keep: float = 0.25
    max_order_age_minutes: int = 60


class DaemonConfig(BaseModel):
    """Daemon process configuration."""

    heartbeat_interval_minutes: int = 60
    guardian_interval_minutes: int = 15
    max_consecutive_failures: int = 5


class DashboardDisplayConfig(BaseModel):
    """Dashboard display filtering parameters."""

    start_date: str | None = None

    @field_validator("start_date", mode="after")
    @classmethod
    def validate_start_date(cls, v: str | None) -> str | None:
        """Validate that start_date is a valid YYYY-MM-DD string if provided."""
        if v is None:
            return None
        try:
            date_type.fromisoformat(v)
        except ValueError:
            raise ValueError(f"start_date must be YYYY-MM-DD format, got: {v}")
        return v


class Settings(BaseSettings):
    """Main configuration class."""

    # Paths
    data_dir: Path = Path("data")

    # Database
    supabase_db_url: str = ""  # postgresql+asyncpg://... set via SUPABASE_DB_URL in .env

    # API Keys
    kalshi_api_key: str = ""
    rsa_private_key: str = ""
    rsa_private_key_path: str = ""  # Alternative: path to PEM file
    exa_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    fireworks_api_key: str = ""
    anthropic_api_key: str = ""
    logfire_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_send_alerts: bool = True

    # Nested configuration sections
    trading: TradingConfig = Field(default_factory=TradingConfig)
    scout: ScoutConfig = Field(default_factory=ScoutConfig)
    guardian: GuardianConfig = Field(default_factory=GuardianConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)
    dashboard_display: DashboardDisplayConfig = Field(default_factory=DashboardDisplayConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("data_dir", mode="after")
    @classmethod
    def resolve_data_dir(cls, v: Path) -> Path:
        """Resolve data directory to absolute path."""
        return v.resolve()

    def get_rsa_private_key(self) -> str:
        """Get RSA private key from either direct value or file path."""
        # If direct key is provided, use it
        if self.rsa_private_key:
            return self.rsa_private_key

        # If path is provided, read from file
        if self.rsa_private_key_path:
            key_path = Path(self.rsa_private_key_path)
            if key_path.is_file():
                return key_path.read_text()
            if key_path.exists():
                logger.warning(f"RSA key path is not a file: {key_path}")
            else:
                logger.warning(f"RSA key file not found: {key_path}")

        return ""

    def load_yaml_config(self) -> None:
        """Load and merge YAML configuration."""
        config_path = self.data_dir / "config.yaml"

        if not config_path.exists():
            logger.warning(
                f"Config file not found: {config_path}. "
                "Using defaults. Run 'python -m coliseum init' to create it."
            )
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)

            if not yaml_config:
                logger.warning(f"Empty config file: {config_path}")
                return

            if "telegram_send_alerts" in yaml_config:
                self.telegram_send_alerts = yaml_config["telegram_send_alerts"]

            for section_name in [
                "trading",
                "scout",
                "guardian",
                "execution",
                "daemon",
                "dashboard_display",
            ]:
                if section_name in yaml_config:
                    section = getattr(self, section_name)
                    yaml_section = yaml_config[section_name]

                    section_dict = section.model_dump()
                    section_dict.update(yaml_section)

                    new_section = section.__class__(**section_dict)
                    setattr(self, section_name, new_section)

            logger.info(f"Loaded configuration from {config_path}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise


@lru_cache()
def get_settings() -> Settings:
    """Get singleton Settings instance."""
    bootstrap_runtime()
    settings = Settings()
    settings.load_yaml_config()
    return settings


