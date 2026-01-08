"""
SettlementStage Class

Main stage implementation for settlement (Stage 4).

Triggered 2 hours after each event's close time.
Separate job per event (staggered settlements).

Process:
1. Fetch outcome from Kalshi API
2. Calculate PnL for each bet
3. Update bet records (status, pnl, outcome)
4. Update agent bankrolls atomically
5. Update event status to settled

Unlike Stages 1-3, writes immediately per event (not batched).
"""
