"""
Agent Runner

Parallel execution of agent betting decisions.

Runs all 8 agents synchronously per event (wait for all before next).
Handles timeouts (5 min per agent) with auto-ABSTAIN fallback.
"""
