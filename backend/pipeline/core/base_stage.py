"""
BasePipelineStage Abstract Class

Abstract base class that all pipeline stages must implement.

Contract:
- Read inputs from pipeline_state
- Perform business logic (API calls, LLM calls, calculations)
- Write outputs to pipeline_state
- Return StageResult with success/failure
- Do NOT write to database (except Stage 4 settlement)

Methods:
- execute(pipeline_state, progress_callback) -> StageResult
- _execute_stage(pipeline_state, progress_callback) -> None (abstract)

Automatic behaviors:
- Timing measurement
- Logfire logging
- Error handling wrapper
"""
