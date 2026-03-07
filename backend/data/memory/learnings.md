# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters
- NBA “announcers say” word-mention props priced ~96% with tight spreads and high activity tend to resolve YES as expected when the broadcast occurs.
- BLS macro-statistic markets (U-3 unemployment, nonfarm payroll thresholds) priced 95–96% YES require an explicit government-shutdown/delayed-release check because a missed or postponed publication can still cause a total loss despite a correct underlying outcome.

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books
- Buying 95–96¢ YES in near-decided, high-liquidity markets requires confirming the resolution event will occur before market close, not just that the eventual underlying value is very likely.

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
- Government shutdowns can postpone scheduled BLS releases and break “deterministic publication” assumptions for macro-stat markets.
