# Evaluation Guide

This document describes the active evaluation logic for Coliseum's trading workflow.

## Purpose

The current system focuses on selecting and executing near-decided markets with limited reversal risk.
It does not use historical mispricing-positioning formulas from the retired model.

## Scout Selection Rules

Scout prioritizes opportunities that satisfy all of the following:

1. **High implied certainty band**
   - Candidate price sits in configured price range.
2. **Short time-to-close**
   - Market closes within configured time horizon.
3. **Clear resolution path**
   - A credible authority and resolution mechanism exist.
4. **Low reversal risk**
   - No active formal process likely to flip final resolution.

## Analyst Output

The Analyst pipeline produces:

- a structured research section,
- a flip-risk-oriented recommendation narrative,
- an optional directional action (`BUY_YES`, `BUY_NO`, `ABSTAIN`).

The Recommender is intentionally lightweight and geared toward execution readiness, not quantitative pricing mismatch scoring.

## Trader Sizing and Execution

Trader execution is constrained by configuration limits:

- `risk.max_position_pct`
- `risk.max_single_trade_usd`
- `trading.contracts`

Orders are placed with limit-order discipline and repricing controls from `execution` settings.

## Current Pipeline Summary

```
Scout → finds near-decided market with lowest available reversal risk
   ↓
Analyst/Researcher → validates facts and resolution pathway
   ↓
Analyst/Recommender → provides execution-readiness recommendation
   ↓
Trader → confirms live price band and executes under hard risk caps
```

## Historical Notes

The legacy quantitative model has been retired from active runtime behavior.
Historical context is preserved in:

- `backend/docs/archived/edge_strategy.md`
