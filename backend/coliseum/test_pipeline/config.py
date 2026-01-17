"""Test configuration for pipeline testing.

The test pipeline uses production code but saves data to test_data/ directory
instead of data/. This keeps test artifacts isolated from production data.
"""

from pathlib import Path


# Test data directory for storing test artifacts
# Located at backend/test_data/ (parallel to backend/data/)
TEST_DATA_DIR: Path = Path(__file__).parent.parent.parent / "test_data"
