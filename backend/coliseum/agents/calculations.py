"""Mathematical calculations for edge, expected value, and position sizing.

These pure functions are used by agents to quantify trading opportunities
and determine optimal position sizes.

For detailed explanations, formulas, and examples, see: docs/calculations.md
"""


def calculate_edge(estimated_prob: float, market_price: float) -> float:
    """Calculate edge (mispricing): estimated_prob - market_price."""
    if not (0 <= estimated_prob <= 1):
        raise ValueError(f"Estimated probability must be between 0 and 1, got {estimated_prob}")
    if not (0 <= market_price <= 1):
        raise ValueError(f"Market price must be between 0 and 1, got {market_price}")

    return estimated_prob - market_price


def calculate_expected_value(estimated_prob: float, market_price: float) -> float:
    """Calculate expected value per dollar risked."""
    if not (0 < estimated_prob < 1):
        raise ValueError(
            f"Estimated probability must be strictly between 0 and 1, got {estimated_prob}"
        )
    if not (0 < market_price < 1):
        raise ValueError(
            f"Market price must be strictly between 0 and 1, got {market_price}"
        )

    payout_ratio = (1 / market_price) - 1
    ev = (estimated_prob * payout_ratio) - (1 - estimated_prob)

    return ev


def calculate_kelly_fraction(
    win_prob: float,
    win_payout: float,
    loss_amount: float = 1.0,
    kelly_fraction: float = 0.25,
) -> float:
    """Calculate fractional Kelly position size (default 1/4 Kelly to reduce volatility)."""
    if not (0 < win_prob < 1):
        raise ValueError(
            f"Win probability must be strictly between 0 and 1, got {win_prob}"
        )
    if win_payout <= 0:
        raise ValueError(f"Win payout must be positive, got {win_payout}")
    if loss_amount <= 0:
        raise ValueError(f"Loss amount must be positive, got {loss_amount}")
    if not (0 < kelly_fraction <= 1):
        raise ValueError(f"Kelly fraction must be between 0 and 1, got {kelly_fraction}")

    b = win_payout / loss_amount
    p = win_prob
    q = 1 - p

    kelly_full = (b * p - q) / b

    if kelly_full <= 0:
        return 0.0

    kelly_fractional = kelly_full * kelly_fraction
    return min(kelly_fractional, 1.0)


def calculate_position_size_pct(
    estimated_prob: float,
    market_price: float,
    kelly_fraction: float = 0.25,
) -> float:
    """Calculate suggested position size as percentage of portfolio using Kelly Criterion."""
    if market_price <= 0 or market_price >= 1:
        return 0.0
    if estimated_prob <= 0 or estimated_prob >= 1:
        return 0.0

    payout = (1 / market_price) - 1
    kelly_size = calculate_kelly_fraction(
        win_prob=estimated_prob,
        win_payout=payout,
        kelly_fraction=kelly_fraction,
    )

    return kelly_size
