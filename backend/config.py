"""
Application Configuration

Pydantic Settings for environment-based configuration.

Settings:
- MONGODB_URI: MongoDB connection string
- KALSHI_API_KEY: Kalshi API credentials
- OPENROUTER_API_KEY: OpenRouter API key
- EXA_API_KEY: Exa AI API key
- LOGFIRE_API_KEY: Logfire observability key
- REDIS_URL: Redis connection for Celery
- ENVIRONMENT: dev | staging | prod

Validation: All required keys checked at startup.
"""
