"""
Celery configuration for distributed task queue.

This module configures the Celery application with:
- Redis broker and result backend
- Task routing to queues
- Retry policies and error handling
- Worker configuration
- Logfire instrumentation for observability
"""
import os
import sys
from pathlib import Path
import logfire
from celery import Celery
from celery.signals import worker_process_init
from config.redis_config import redis_settings

# Add project root to Python path for module imports
# This ensures Celery workers can resolve imports
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Initialize Celery application
celery_app = Celery(
    "coliseum",
    broker=redis_settings.broker_url,
    backend=redis_settings.result_backend,
    include=[
        "tasks.event_tasks",
        "tasks.settlement_tasks",
        "tasks.price_tasks",
        "tasks.maintenance_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json", "pickle"],  # pickle needed for exceptions

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task results
    result_expires=3600,
    result_extended=True,

    # Task routing
    task_routes={
        # Event tasks
        "tasks.select_daily_events": {"queue": "events"},
        "tasks.activate_event": {"queue": "events"},
        "tasks.check_and_close_events": {"queue": "events"},
        "tasks.launch_betting_sessions": {"queue": "events"},
        # AI tasks (summary, betting)
        "tasks.generate_event_summary": {"queue": "ai"},
        "tasks.run_betting_session": {"queue": "ai"},
        # Settlement tasks
        "tasks.check_settlements": {"queue": "settlements"},
        "tasks.settle_event": {"queue": "settlements"},
        # Price tasks
        "tasks.update_prices": {"queue": "prices"},
        "tasks.record_price_history": {"queue": "prices"},
        # Maintenance tasks
        "tasks.update_leaderboard": {"queue": "maintenance"},
        "tasks.simulate_viewers": {"queue": "maintenance"},
        "tasks.cleanup_old_data": {"queue": "maintenance"},
        "tasks.initialize_models": {"queue": "maintenance"},
    },

    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_concurrency=2,  # Adjust based on deployment resources

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Retry configuration
    # Handle retries at task level for better control
    task_autoretry_for=(),
    task_retry_kwargs={"max_retries": 0},

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Celery Beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Daily event selection at midnight UTC
    "select-daily-events": {
        "task": "tasks.select_daily_events",
        "schedule": crontab(hour=0, minute=0),
        "args": (5,),  # Select 5 events
    },
    # Check and close expired events every minute
    "check-close-events": {
        "task": "tasks.check_and_close_events",
        "schedule": 60.0,  # Every minute
    },
    # Check for settlements every 5 minutes
    "check-settlements": {
        "task": "tasks.check_settlements",
        "schedule": 300.0,  # Every 5 minutes
    },
    # Update prices every 30 seconds
    "update-prices": {
        "task": "tasks.update_prices",
        "schedule": 30.0,
    },
    # Record price history every 5 minutes
    "record-price-history": {
        "task": "tasks.record_price_history",
        "schedule": 300.0,
    },
    # Update leaderboard hourly
    "update-leaderboard": {
        "task": "tasks.update_leaderboard",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Simulate viewers every 10 seconds
    "simulate-viewers": {
        "task": "tasks.simulate_viewers",
        "schedule": 10.0,
    },
    # Cleanup old data daily at 3 AM UTC
    "cleanup-old-data": {
        "task": "tasks.cleanup_old_data",
        "schedule": crontab(hour=3, minute=0),
    },
}


@worker_process_init.connect
def init_worker_process(**kwargs) -> None:
    """
    Initialize each worker process with proper configuration.

    This runs once per worker process (not per task).
    Configures observability and logging for the worker.
    """
    # Re-establish sys.path in forked child process
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Configure Logfire for observability in worker processes
    if os.getenv("LOGFIRE_TOKEN"):
        logfire.configure(
            service_name="coliseum-celery-worker",
            send_to_logfire="if-token-present",
            console=False,
        )
    else:
        logfire.configure(
            send_to_logfire=False,
            console=False,
        )

    # Instrument pydantic-ai to capture agent runs and LLM calls via OpenRouter
    logfire.instrument_pydantic_ai()

    # Log worker initialization
    logfire.info(
        "Celery worker initialized",
        project_root=str(project_root),
        logfire_enabled=bool(os.getenv("LOGFIRE_TOKEN")),
    )


@celery_app.task(name="health_check")
def health_check() -> dict:
    """
    Health check task for monitoring worker status.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": "celery-worker"
    }
