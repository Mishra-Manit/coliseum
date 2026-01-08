"""
PipelineRunner Orchestrator

Orchestrates sequential execution of pipeline stages.

Responsibilities:
- Execute stages in order: Ingestion -> Research -> Betting -> Settlement
- Pass DailyPipelineState between stages
- Handle stage failures and propagate errors
- Trigger atomic database write after Stage 3
- Schedule dynamic settlement tasks

Usage:
    runner = create_daily_pipeline()
    state = DailyPipelineState(execution_date=today)
    batch_id = await runner.run_daily_pipeline(state)
"""
