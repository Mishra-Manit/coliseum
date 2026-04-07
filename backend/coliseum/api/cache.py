"""In-memory TTL cache for dashboard API responses.

Stores computed results in a process-local dict with per-key expiration.
Designed for single-process deployments (e.g. Raspberry Pi) where external
cache infrastructure like Redis would be overkill.
"""

import time
from typing import Any, Awaitable, Callable

_store: dict[str, tuple[float, Any]] = {}


async def get_or_compute(
    key: str,
    ttl_seconds: float,
    factory: Callable[[], Awaitable[Any]],
) -> Any:
    """Return a cached value if fresh, otherwise await *factory* and cache the result."""
    now = time.monotonic()
    entry = _store.get(key)
    if entry is not None and (now - entry[0]) < ttl_seconds:
        return entry[1]
    result = await factory()
    _store[key] = (now, result)
    return result


def invalidate(*keys: str) -> None:
    """Remove specific keys from the cache."""
    for key in keys:
        _store.pop(key, None)


def invalidate_all() -> None:
    """Clear every cached entry."""
    _store.clear()
