"""Shared runtime bootstrap helpers for CLI and API surfaces."""

from pathlib import Path

from dotenv import load_dotenv

_BOOTSTRAPPED = False


def bootstrap_runtime() -> None:
    """Load shared runtime environment exactly once."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    env_file = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_file)
    _BOOTSTRAPPED = True
