"""Manual test script for Exa AI service integration.

Usage:
    cd backend
    source venv/bin/activate
    python -m coliseum.services.exa.tests.test_exa
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from coliseum.services.exa import create_exa_client

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent.parent.parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Configure logging to write to both console and file
output_file = Path(__file__).parent / "test_output.md"

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []  # Clear any existing handlers

formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# File Handler
file_handler = logging.FileHandler(output_file, mode='w')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)


async def test_answer():
    """Test answer functionality."""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        logger.error("EXA_API_KEY not found in environment")
        return

    async with create_exa_client(api_key) as client:
        logger.info("Testing answer: 'What are experts saying about inflation in 2026?'")

        response = await client.answer(
            question="What are experts saying about inflation in 2026?",
            include_text=True,
        )

        logger.info(f"Query: {response.query}")
        logger.info(f"Answer: {response.answer}\n")
        logger.info(f"Citations ({len(response.citations)}):")

        for i, citation in enumerate(response.citations, 1):
            logger.info(f"  [{i}] {citation.title}")
            logger.info(f"      {citation.url}")
            logger.info("")

async def main():
    logger.info("=" * 60)
    logger.info("Exa AI Service Test Suite")
    logger.info("=" * 60)

    await test_answer()
    logger.info("\n" + "=" * 60 + "\n")

    logger.info("\n" + "=" * 60)
    logger.info("Tests complete")


if __name__ == "__main__":
    asyncio.run(main())
