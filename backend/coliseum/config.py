"""Configuration management using Pydantic Settings."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class TradingConfig(BaseModel):
    """Trading operational parameters."""

    paper_mode: bool = True
    initial_bankroll: float = 100.0


class RiskConfig(BaseModel):
    """Risk management limits and thresholds."""

    max_position_pct: float = 0.10
    max_daily_loss_pct: float = 0.05
    max_open_positions: int = 10
    max_single_trade_usd: float = 10.0
    min_edge_threshold: float = 0.05
    min_ev_threshold: float = 0.10
    kelly_fraction: float = 0.50  # 1/2 Kelly for edge trading


class SchedulerConfig(BaseModel):
    """Job scheduling intervals in minutes."""

    scout_full_scan_minutes: int = 60
    scout_quick_scan_minutes: int = 15
    guardian_position_check_minutes: int = 15
    guardian_news_scan_minutes: int = 30


class ScoutConfig(BaseModel):
    """Scout agent market filtering parameters."""

    min_volume: int = 10000  # Minimum 24h volume (contracts)
    min_liquidity_cents: int = 10  # Minimum bid-ask spread tolerance (cents)
    min_close_hours: int = 96   # Minimum hours until close (4 days for edge trading)
    max_close_hours: int = 240  # Maximum hours until close (10 days for edge trading)
    max_opportunities_per_scan: int = 5  # Limit opportunities per scan

    # Quick scan settings (subset of full scan)
    quick_scan_min_volume: int = 50000  # Higher volume threshold for quick scans


class AnalystConfig(BaseModel):
    """Analyst agent research parameters."""

    max_research_time_seconds: int = 300
    required_sources: int = 3


class GuardianConfig(BaseModel):
    """Guardian agent monitoring parameters."""

    profit_target_pct: float = 0.70    # Take profit at 70% of edge captured
    stop_loss_pct: float = 0.10        # Cut loss at 10% down (tight stop)
    max_hold_days: int = 5             # Maximum days to hold any position
    edge_capture_pct: float = 0.70     # Target: capture 70% of identified edge


class ExecutionConfig(BaseModel):
    """Order execution and slippage parameters."""

    use_limit_orders_only: bool = True
    max_slippage_pct: float = 0.05
    order_check_interval_seconds: int = 300
    max_reprice_attempts: int = 3
    reprice_aggression: float = 0.02
    min_fill_pct_to_keep: float = 0.25
    max_order_age_minutes: int = 60


class TelegramConfig(BaseModel):
    """Telegram notification configuration."""

    send_trade_alerts: bool = True
    send_risk_alerts: bool = True
    send_position_alerts: bool = True
    send_opportunity_alerts: bool = True
    send_system_alerts: bool = False


class Settings(BaseSettings):
    """Main configuration class."""

    # Paths
    data_dir: Path = Path("data")

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

    # Nested configuration sections
    trading: TradingConfig = Field(default_factory=TradingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)

    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    scout: ScoutConfig = Field(default_factory=ScoutConfig)
    analyst: AnalystConfig = Field(default_factory=AnalystConfig)
    guardian: GuardianConfig = Field(default_factory=GuardianConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)

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

            for section_name in [
                "trading",
                "risk",
                "scheduler",
                "scout",
                "analyst",
                "guardian",
                "execution",
                "telegram",
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
    settings = Settings()
    settings.load_yaml_config()
    return settings
