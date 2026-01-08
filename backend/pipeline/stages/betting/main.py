"""
BettingStage Class

Main stage implementation for betting (Stage 3).

Process:
1. Load agent context (bankroll, history, persona)
2. For each agent × event, generate betting decision
3. Validate bet sizes (max 10% of bankroll)
4. Parse and store decisions

Outputs to pipeline_state:
- agent_decisions: List[BetDecision]
- betting_metadata: Dict with call counts, timeouts
"""
