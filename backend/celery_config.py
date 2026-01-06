"""
Celery configuration for distributed task queue.

This module configures the Celery application with:
- Redis broker and result backend
- Worker configuration
- Logfire instrumentation for observability

Note: Task includes and beat schedule will be added as business logic is implemented.
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
    include=[],  # Task modules will be added here as implemented
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

    # Task routing (will be configured as tasks are added)
    task_routes={},

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

# Celery Beat schedule for periodic tasks (empty - will be added as tasks are implemented)
celery_app.conf.beat_schedule = {}


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
