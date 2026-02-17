"""Job scheduler using APScheduler."""

import logging
from typing import NoReturn

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from coliseum.agents.guardian import guardian_job
from coliseum.agents.scout import scout_scan_job
from coliseum.config import Settings

logger = logging.getLogger(__name__)


def _placeholder_job(job_name: str) -> None:
    """Placeholder job that logs execution."""
    logger.info(f"[PLACEHOLDER] {job_name} triggered")


def start_scheduler(settings: Settings) -> NoReturn:
    """Start the APScheduler with configured jobs."""
    scheduler = BlockingScheduler()

    scheduler.add_job(
        scout_scan_job,
        IntervalTrigger(minutes=settings.scheduler.scout_full_scan_minutes),
        id="scout-scan",
        name="Scout: Market Scan",
    )
    logger.info(
        f"Registered job: Scout Market Scan (every {settings.scheduler.scout_full_scan_minutes} min)"
    )

    scheduler.add_job(
        guardian_job,
        IntervalTrigger(minutes=settings.scheduler.guardian_position_check_minutes),
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

    try:
        logger.info("✓ Scheduler starting...")
        logger.info(f"✓ {len(scheduler.get_jobs())} jobs registered")
        logger.info("Press Ctrl+C to stop\n")

        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        logger.info("\nReceived interrupt signal")
        scheduler.shutdown()
        logger.info("✓ Scheduler stopped cleanly")
