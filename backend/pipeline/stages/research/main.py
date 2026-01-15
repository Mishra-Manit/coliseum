"""
ResearchStage Class

Main stage implementation for research (Stage 2).

Process:
1. For each of 5 events, instantiate Research Agent
2. Use Exa AI Answer API for intelligence gathering
3. Generate standardized intelligence brief
4. Store brief in pipeline_state

Outputs to pipeline_state:
- intelligence_briefs: Dict[event_id, brief_text]
- research_metadata: Dict with call counts, timing
"""
