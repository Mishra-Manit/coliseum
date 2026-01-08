"""
Payout Calculator

Calculates PnL for settled bets.

Formulas:
- Winning bet: gross_payout = bet_amount / locked_price
                fee = gross_payout * 0.07
                net_payout = gross_payout - fee
                pnl = net_payout - bet_amount
- Losing bet: pnl = -bet_amount
- VOID event: pnl = 0 (full refund)
- Abstention: pnl = 0
"""
