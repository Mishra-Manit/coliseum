"""Test pipeline module for isolated agent testing.

This module runs production agents but saves all data to test_data/ directory
instead of data/, keeping test artifacts isolated from production data.

Usage:
    python -m coliseum.test_pipeline scout
    python -m coliseum.test_pipeline analyst --opportunity-id opp_123
    python -m coliseum.test_pipeline trader --recommendation-id rec_xyz
    python -m coliseum.test_pipeline guardian
    python -m coliseum.test_pipeline run --full
    python -m coliseum.test_pipeline clean
"""

from .config import TEST_DATA_DIR

from .run import (
    run_scout_test,
    run_analyst_test,
    run_trader_test,
    run_guardian_test,
    run_full_pipeline,
    clean_test_data,
)

__all__ = [
    # Config
    "TEST_DATA_DIR",
    # Run functions
    "run_scout_test",
    "run_analyst_test",
    "run_trader_test",
    "run_guardian_test",
    "run_full_pipeline",
    "clean_test_data",
]
