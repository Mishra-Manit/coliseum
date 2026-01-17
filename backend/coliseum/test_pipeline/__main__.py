"""Entry point for running test_pipeline as a module.

Usage:
    python -m coliseum.test_pipeline scout
    python -m coliseum.test_pipeline analyst --opportunity-id opp_123
    python -m coliseum.test_pipeline trader --recommendation-id rec_xyz
    python -m coliseum.test_pipeline guardian
    python -m coliseum.test_pipeline run --full
    python -m coliseum.test_pipeline clean
"""

from coliseum.test_pipeline.run import main

if __name__ == "__main__":
    main()
