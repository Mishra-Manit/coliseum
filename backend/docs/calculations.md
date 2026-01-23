# Trading Calculations

This document explains the mathematical foundations used by Coliseum agents to evaluate and size positions in prediction markets.

## Overview

The calculations module provides four pure functions that work together to quantify trading opportunities:

1. **Edge** - How mispriced is the market?
2. **Expected Value (EV)** - What's the expected return?
3. **Kelly Criterion** - How much should we bet?
4. **Position Sizing** - What percentage of portfolio?

## 1. Edge Calculation

**Purpose**: Measure the difference between true probability and market price.

**Formula**:
```
Edge = Estimated Probability - Market Price
```

**Example**:
- You estimate 65% chance of YES
- Market prices YES at 45¢
- Edge = 0.65 - 0.45 = **0.20 (20% edge)**

**Interpretation**: Positive edge means the market is underpricing the outcome. This is your theoretical advantage.

**Validation**: Both probabilities must be between 0 and 1 (inclusive).

---

## 2. Expected Value (EV)

**Purpose**: Calculate the average profit per dollar risked.

**Formula**:
```
Payout Ratio = (1 / Market Price) - 1
EV = (Estimated Prob × Payout Ratio) - (1 - Estimated Prob)
```

**Example**:
- Estimated probability: 65%
- Market price: 45¢
- Payout if win: $1 (profit = 55¢)
- Payout ratio: (1 / 0.45) - 1 = 1.22x

Calculation:
```
EV = (0.65 × 1.22) - 0.35 = 0.44 (44% expected return)
```

**Interpretation**: For every dollar risked, you expect to profit 44¢ on average.

**Validation**: Both probabilities must be strictly between 0 and 1 (exclusive) to avoid division by zero.

---

## 3. Kelly Criterion

**Purpose**: Determine the optimal fraction of bankroll to bet for maximum long-term growth.

**Formula**:
```
Kelly Full = (b × p - q) / b

Where:
  b = odds received (win_payout / loss_amount)
  p = probability of winning
  q = probability of losing (1 - p)

Kelly Fractional = Kelly Full × kelly_fraction
```

**Why Fractional Kelly?**

Full Kelly maximizes growth but has high volatility. We use **1/4 Kelly (0.25)** by default to reduce risk while still capitalizing on edge.

**Example**:
- Win probability: 65%
- Payout: 1.22x
- Loss: 1.0

```
b = 1.22 / 1.0 = 1.22
Full Kelly = (1.22 × 0.65 - 0.35) / 1.22 = 0.32 (32%)
1/4 Kelly = 0.32 × 0.25 = 0.08 (8% of bankroll)
```

**Edge Cases**:
- If Kelly ≤ 0, return 0.0 (negative EV, don't bet)
- Kelly is capped at 1.0 (never bet more than 100% of bankroll)

**Validation**:
- Win probability must be strictly between 0 and 1
- Win payout must be positive
- Kelly fraction must be between 0 and 1

---

## 4. Position Size Percentage

**Purpose**: Convenience wrapper combining EV and Kelly calculations.

**Process**:
1. Calculate payout ratio from market price
2. Apply Kelly Criterion with default 1/4 fraction
3. Return suggested position size as decimal

**Example**:
```python
calculate_position_size_pct(
    estimated_prob=0.65,
    market_price=0.45,
    kelly_fraction=0.25
)
# Returns: 0.08 (suggest 8% of portfolio)
```

**Safety**: Returns 0.0 if market price or estimated probability are at extremes (0 or 1) to prevent division by zero.

---

## Risk Management Integration

These calculations feed into the risk management system (see `agents/risk.py`):

- **Min Edge**: Reject trades below 5% edge
- **Min EV**: Reject trades below 10% expected value
- **Max Position**: Cap individual positions at 10% of portfolio (overrides Kelly)
- **Max Trade Size**: Hard limit of $1,000 per trade

The Kelly Criterion suggests the *optimal* size, but risk limits enforce *maximum* constraints.

---

## Mathematical Properties

**Edge vs EV**:
- Edge is additive (percentage points)
- EV is multiplicative (return on investment)
- High edge doesn't guarantee high EV if payout odds are poor

**Kelly Criterion Properties**:
- Maximizes geometric growth rate
- Assumes infinite repeated bets
- Sensitive to probability estimation errors (hence fractional Kelly)

**Fractional Kelly Benefits**:
- Reduces volatility by 4x (for 1/4 Kelly)
- More forgiving of estimation errors
- Slower growth but more sustainable

---

## Usage in Agent Pipeline

```
Scout → discovers market
   ↓
Analyst → estimates true probability
   ↓
   Edge = estimated_prob - market_price
   EV = calculate_expected_value(estimated_prob, market_price)
   ↓
   [Risk Check: edge > 5%, EV > 10%]
   ↓
   Position Size = calculate_position_size_pct(estimated_prob, market_price)
   ↓
Trader → executes with position size capped by risk limits
```

---

## References

- **Kelly Criterion**: J. L. Kelly Jr., "A New Interpretation of Information Rate" (1956)
- **Fractional Kelly**: Edward O. Thorp, "The Kelly Criterion in Blackjack Sports Betting, and the Stock Market" (2008)
- **Prediction Market Math**: Robin Hanson, "Logarithmic Market Scoring Rules for Modular Combinatorial Information Aggregation" (2003)
