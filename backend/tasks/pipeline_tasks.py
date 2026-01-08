"""
Daily Pipeline Task

Celery task for 09:00 EST daily pipeline execution.

Triggered by: Celery Beat schedule
Retry: 3 attempts with exponential backoff for retryable errors

Process:
1. Create DailyPipelineState
2. Run PipelineRunner through all stages
3. Schedule settlement tasks for each event
4. Return batch_id on success
"""
