"""Celery tasks module."""

from tasks.event_tasks import (
    select_daily_events,
    activate_event,
    check_and_close_events,
    generate_event_summary,
    launch_betting_sessions,
    run_betting_session,
)
from tasks.settlement_tasks import (
    check_settlements,
    settle_event,
)
from tasks.price_tasks import (
    update_prices,
)
from tasks.maintenance_tasks import (
    update_leaderboard,
    simulate_viewers,
    cleanup_old_data,
    initialize_models,
)

__all__ = [
    # Event tasks
    "select_daily_events",
    "activate_event",
    "check_and_close_events",
    "generate_event_summary",
    "launch_betting_sessions",
    "run_betting_session",
    # Settlement tasks
    "check_settlements",
    "settle_event",
    # Price tasks
    "update_prices",
    # Maintenance tasks
    "update_leaderboard",
    "simulate_viewers",
    "cleanup_old_data",
    "initialize_models",
]
