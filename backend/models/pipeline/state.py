"""
DailyPipelineState Dataclass

Central in-memory state object that flows through all pipeline stages.
Each stage reads from and writes to this state object.

Fields:
- Pipeline metadata: batch_id, execution_date, trigger_time
- Stage 1 outputs (Ingestion): selected_events, ingestion_metadata
- Stage 2 outputs (Research): intelligence_briefs dict, research_metadata
- Stage 3 outputs (Betting): agent_decisions list, betting_metadata
- Tracking: stage_timings dict, errors list

Key Design:
- All intermediate data stays in memory during execution
- Enables atomic database write after Stage 3
- Easy to serialize for debugging/logging
"""
