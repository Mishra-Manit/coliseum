"""Coliseum autonomous trading daemon with heartbeat loop and graceful shutdown."""

import asyncio
import logging
import signal
from datetime import datetime, timezone

import logfire

from coliseum.agents.guardian import run_guardian
from coliseum.config import Settings
from coliseum.memory.errors import ErrorEntry, detect_recurring_error, log_error
from coliseum.pipeline import run_pipeline
from coliseum.services.telegram import TelegramClient

logger = logging.getLogger("coliseum.daemon")


class ColiseumDaemon:
    """Long-lived autonomous trading daemon."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._cycle_count = 0
        self._consecutive_failures = 0
        self._started_at: datetime | None = None
        self._last_cycle_at: datetime | None = None
        self._paused = False

    @property
    def heartbeat_interval_seconds(self) -> float:
        return self.settings.daemon.heartbeat_interval_minutes * 60

    @property
    def guardian_interval_seconds(self) -> float:
        return self.settings.daemon.guardian_interval_minutes * 60

    async def start(self, install_signal_handlers: bool = True) -> None:
        """Start the daemon: optionally install signal handlers and enter heartbeat loop."""
        self.running = True
        self._started_at = datetime.now(timezone.utc)
        if install_signal_handlers:
            self._install_signal_handlers()

        logger.info(
            "Daemon starting — heartbeat=%dm, guardian=%dm, max_failures=%d",
            self.settings.daemon.heartbeat_interval_minutes,
            self.settings.daemon.guardian_interval_minutes,
            self.settings.daemon.max_consecutive_failures,
        )

        try:
            await self._heartbeat_loop()
        finally:
            self.running = False
            logger.info("Daemon stopped. Cycles completed: %d", self._cycle_count)

    async def _heartbeat_loop(self) -> None:
        """Main loop: run full pipeline cycles with guardian-only checks in between."""
        while not self._shutdown_event.is_set():
            if self._paused:
                logger.warning(
                    "Daemon paused due to %d consecutive failures. "
                    "Waiting for manual intervention or next heartbeat to retry.",
                    self._consecutive_failures,
                )
                await self._interruptible_sleep(self.heartbeat_interval_seconds)
                self._paused = False
                self._consecutive_failures = 0
                continue

            cycle_start = datetime.now(timezone.utc)

            await self._run_full_cycle()

            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            remaining = max(0, self.heartbeat_interval_seconds - elapsed)

            if remaining > 0 and not self._shutdown_event.is_set():
                await self._run_guardian_intercycles(remaining)

    async def _run_full_cycle(self) -> None:
        """Execute one full pipeline cycle with error tracking."""
        self._cycle_count += 1
        try:
            await run_pipeline(self.settings)
            self._consecutive_failures = 0
            self._last_cycle_at = datetime.now(timezone.utc)
            logfire.info("pipeline cycle complete", cycle=self._cycle_count)
        except Exception as e:
            self._consecutive_failures += 1
            logfire.error(
                "pipeline cycle failed",
                cycle=self._cycle_count,
                failure=self._consecutive_failures,
                max_failures=self.settings.daemon.max_consecutive_failures,
                error=str(e),
            )
            logger.error(
                "Full pipeline cycle #%d failed (%d/%d): %s",
                self._cycle_count,
                self._consecutive_failures,
                self.settings.daemon.max_consecutive_failures,
                e,
                exc_info=True,
            )
            self._log_error(
                component="pipeline",
                error=str(e),
                resolution="auto_retry"
                if self._consecutive_failures
                < self.settings.daemon.max_consecutive_failures
                else "paused",
                attempts=self._consecutive_failures,
            )
            if (
                self._consecutive_failures
                >= self.settings.daemon.max_consecutive_failures
            ):
                logfire.critical(
                    "max consecutive failures reached, pausing daemon",
                    failures=self._consecutive_failures,
                )
                self._paused = True
                await self._send_escalation_alert(str(e))

        await self._send_heartbeat()

    async def _run_guardian_intercycles(self, remaining_seconds: float) -> None:
        """Run guardian-only checks in the gap between full pipeline cycles."""
        guardian_interval = self.guardian_interval_seconds

        if guardian_interval <= 0 or guardian_interval >= remaining_seconds:
            await self._interruptible_sleep(remaining_seconds)
            return

        elapsed_in_gap = 0.0
        while elapsed_in_gap + guardian_interval <= remaining_seconds:
            sleep_dur = guardian_interval
            await self._interruptible_sleep(sleep_dur)
            if self._shutdown_event.is_set():
                return

            elapsed_in_gap += sleep_dur
            logger.info("Guardian-only intercycle check starting")
            try:
                guardian_result = await run_guardian(settings=self.settings)
                logger.info(
                    "Guardian intercycle complete: synced=%d closed=%d",
                    guardian_result.positions_synced,
                    guardian_result.reconciliation.newly_closed,
                )
            except Exception as e:
                logger.error("Guardian intercycle failed: %s", e)
                self._log_error(
                    component="guardian_intercycle",
                    error=str(e),
                    resolution="skipped",
                )

        leftover = remaining_seconds - elapsed_in_gap
        if leftover > 0 and not self._shutdown_event.is_set():
            await self._interruptible_sleep(leftover)

    async def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep that can be interrupted by the shutdown event."""
        try:
            await asyncio.wait_for(self._shutdown_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    def _install_signal_handlers(self) -> None:
        """Install SIGTERM and SIGINT handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._request_shutdown, sig)

    def _request_shutdown(self, sig: signal.Signals) -> None:
        """Handle shutdown signal by setting the shutdown event."""
        logger.info("Received %s — initiating graceful shutdown", sig.name)
        self._shutdown_event.set()

    async def _send_heartbeat(self) -> None:
        """Send a Telegram status summary after each pipeline cycle."""
        if not self.settings.telegram_send_alerts:
            return
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            logfire.warn("telegram heartbeat skipped: bot_token or chat_id not configured")
            return

        uptime_h = 0.0
        if self._started_at:
            uptime_h = (datetime.now(timezone.utc) - self._started_at).total_seconds() / 3600

        status = "PAUSED" if self._paused else "RUNNING"
        last_cycle = self._last_cycle_at.isoformat() if self._last_cycle_at else "never"

        msg = (
            f"COLISEUM HEARTBEAT\n\n"
            f"Status: {status}\n"
            f"Uptime: {uptime_h:.1f}h\n"
            f"Cycles completed: {self._cycle_count}\n"
            f"Last cycle: {last_cycle}\n"
            f"Consecutive failures: {self._consecutive_failures}"
        )

        with logfire.span("telegram heartbeat"):
            try:
                async with TelegramClient(
                    bot_token=self.settings.telegram_bot_token,
                    default_chat_id=self.settings.telegram_chat_id,
                ) as tg:
                    result = await tg.send_alert(msg)
                    if result.success:
                        logfire.info(
                            "heartbeat sent",
                            cycle=self._cycle_count,
                            uptime_h=round(uptime_h, 1),
                        )
                    else:
                        logfire.warn("telegram heartbeat failed", error=result.error)
            except Exception as exc:
                logfire.error("failed to send telegram heartbeat", error=str(exc))

    async def _send_escalation_alert(self, error: str) -> None:
        """Send a Telegram alert when the daemon pauses due to repeated failures."""
        if not self.settings.telegram_send_alerts:
            return
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            logger.warning(
                "Telegram escalation skipped: bot_token or chat_id not configured"
            )
            return

        recurring, pattern_desc = detect_recurring_error(hours=1, threshold=3)
        pattern_line = (
            f"Recurring pattern: {pattern_desc}"
            if recurring
            else "No recurring pattern detected"
        )

        uptime_h = 0.0
        if self._started_at:
            uptime_h = (
                datetime.now(timezone.utc) - self._started_at
            ).total_seconds() / 3600

        msg = (
            "COLISEUM ALERT\n\n"
            f"Daemon paused after {self._consecutive_failures} consecutive failures.\n"
            f"Last error: {error}\n"
            f"{pattern_line}\n"
            f"Uptime: {uptime_h:.1f}h | Cycles completed: {self._cycle_count}\n"
            f"Last success: {self._last_cycle_at.isoformat() if self._last_cycle_at else 'never'}\n\n"
            "Action: Pipeline paused. Manual intervention required or daemon will retry after next heartbeat interval."
        )

        with logfire.span("telegram escalation alert"):
            try:
                async with TelegramClient(
                    bot_token=self.settings.telegram_bot_token,
                    default_chat_id=self.settings.telegram_chat_id,
                ) as tg:
                    result = await tg.send_alert(msg)
                    if result.success:
                        logfire.info("escalation alert sent", failures=self._consecutive_failures)
                    else:
                        logfire.warn("telegram escalation alert failed", error=result.error)
            except Exception as exc:
                logfire.error("failed to send telegram escalation alert", error=str(exc))

    def _log_error(
        self,
        component: str,
        error: str,
        resolution: str,
        attempts: int = 1,
        details: str = "",
    ) -> None:
        """Log an error to the persistent error history."""
        try:
            entry = ErrorEntry(
                component=component,
                error=error,
                resolution=resolution,
                attempts=attempts,
                details=details,
            )
            log_error(entry)
        except Exception as e:
            logger.warning("Failed to log error to memory: %s", e)

    def status_summary(self) -> dict:
        """Return a snapshot of daemon state for diagnostics."""
        now = datetime.now(timezone.utc)
        uptime = (now - self._started_at).total_seconds() if self._started_at else 0
        return {
            "running": self.running,
            "paused": self._paused,
            "uptime_seconds": int(uptime),
            "cycles_completed": self._cycle_count,
            "consecutive_failures": self._consecutive_failures,
            "last_cycle": self._last_cycle_at.isoformat()
            if self._last_cycle_at
            else None,
        }
