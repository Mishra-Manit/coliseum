"""Shared ID generation utilities for domain models."""

from uuid import uuid4


def generate_prefixed_id(prefix: str) -> str:
    """Generate a short unique ID with a prefix, e.g. 'opp_a1b2c3d4'."""
    return f"{prefix}_{uuid4().hex[:8]}"
