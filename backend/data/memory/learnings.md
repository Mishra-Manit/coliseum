# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
