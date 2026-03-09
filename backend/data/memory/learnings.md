# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters
- NBA “announcers say” word-mention props priced ~96% with tight spreads and high activity tend to resolve YES as expected when the broadcast occurs.
- BLS macro-statistic markets priced 95–96% YES require an explicit government-shutdown and release-timing check because a missed or postponed publication can still cause a total loss despite a correct underlying outcome.
- WTI daily-settlement threshold markets priced around 96% YES are reliable when the contract resolves from the exchange’s official published settlement and the remaining risk is only pre-settlement price movement.

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books
- Buying 95–96¢ YES in near-decided, high-liquidity markets requires confirming the resolution event will occur before market close, not just that the eventual underlying value is very likely.
- Buying 95–96¢ YES is justified in mechanically resolved reference-price markets when the source publication is fixed and there is no appeal or discretionary revision path.

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
- Government shutdowns can postpone scheduled BLS releases and break “deterministic publication” assumptions for macro-stat markets.