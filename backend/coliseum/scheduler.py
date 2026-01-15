"""Job scheduler using APScheduler."""

import logging
from typing import NoReturn

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from coliseum.config import Settings

logger = logging.getLogger(__name__)


def _placeholder_job(job_name: str) -> None:
    """Placeholder job that logs execution."""
    logger.info(f"[PLACEHOLDER] {job_name} triggered")


def start_scheduler(settings: Settings) -> NoReturn:
    """Start the APScheduler with configured jobs."""
    scheduler = BlockingScheduler()

    scheduler.add_job(
        _placeholder_job,
        IntervalTrigger(minutes=settings.scheduler.scout_full_scan_minutes),
        args=["Scout Full Scan"],
        id="scout-full-scan",
        name="Scout: Full Market Scan",
    )
    logger.info(
        f"Registered job: Scout Full Scan (every {settings.scheduler.scout_full_scan_minutes} min)"
    )

    scheduler.add_job(
        _placeholder_job,
        IntervalTrigger(minutes=settings.scheduler.scout_quick_scan_minutes),
        args=["Scout Quick Scan"],
        id="scout-quick-scan",
        name="Scout: Quick Scan",
    )
    logger.info(
        f"Registered job: Scout Quick Scan (every {settings.scheduler.scout_quick_scan_minutes} min)"
    )

    scheduler.add_job(
        _placeholder_job,
        IntervalTrigger(minutes=settings.scheduler.guardian_position_check_minutes),
        args=["Guardian Position Check"],
        id="guardian-position-check",
        name="Guardian: Position Monitor",
    )
    logger.info(
        f"Registered job: Guardian Position Check (every {settings.scheduler.guardian_position_check_minutes} min)"
    )

    scheduler.add_job(
        _placeholder_job,
        IntervalTrigger(minutes=settings.scheduler.guardian_news_scan_minutes),
        args=["Guardian News Scan"],
        id="guardian-news-scan",
        name="Guardian: News Scanner",
    )
    logger.info(
        f"Registered job: Guardian News Scan (every {settings.scheduler.guardian_news_scan_minutes} min)"
    )

    scheduler.add_job(
        _placeholder_job,
        CronTrigger(hour=21, minute=0),  # 4 PM EST = 9 PM UTC
        args=["Daily Portfolio Snapshot"],
        id="daily-snapshot",
        name="Daily Snapshot",
    )
    logger.info("Registered job: Daily Portfolio Snapshot (4:00 PM EST)")

    try:
        logger.info("✓ Scheduler starting...")
        logger.info(f"✓ {len(scheduler.get_jobs())} jobs registered")
        logger.info("Press Ctrl+C to stop\n")

        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        logger.info("\nReceived interrupt signal")
        scheduler.shutdown()
        logger.info("✓ Scheduler stopped cleanly")
