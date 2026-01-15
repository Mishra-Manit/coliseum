"""
Pipeline Exception Hierarchy

Custom exceptions with retry logic for pipeline resilience.

Exception Classes:
- PipelineExecutionError: Base exception (retryable=False)
- StageExecutionError: Fatal stage failure (non-retryable)
- ExternalAPIError: Kalshi/OpenRouter/Exa AI API error (retryable=True)
- ValidationError: Data validation failed (non-retryable)

Retry Logic:
- Retryable errors trigger Celery retry with exponential backoff
- Non-retryable errors fail-fast and alert admin
"""
