# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters
- NBA “announcers say” word-mention props priced ~96% with tight spreads and high activity tend to resolve YES as expected when the broadcast occurs.
- BLS macro-statistic markets priced 95–96% YES require an explicit government-shutdown and release-timing check because a missed or postponed publication can still cause a total loss despite a correct underlying outcome.
- WTI daily-settlement threshold markets priced around 96% YES are reliable when the contract resolves from the exchange’s official published settlement and the remaining risk is only pre-settlement price movement.
- Rotten Tomatoes threshold markets are favorable YES buys when the live score is at least 2 points above the strike, the review count is already large, and the remaining risk is only late-review drift before the fixed snapshot time.
- Same-day weather band YES entries are favorable when the official station has already recorded a temperature inside the target band and the NWS digital forecast keeps the rest of the climate day at or below the band ceiling.
- CPI and Core CPI BLS threshold markets are favorable high-price YES buys when multiple fresh economist previews and the Cleveland Fed nowcast all clear the strike and the contract resolves only from the scheduled BLS release.
- CPI-family thresholds at 0.0% and 0.1% must be evaluated on the published one-decimal BLS figure because a raw positive print can still resolve NO after rounding.
- Same-day weather band NO entries are unsafe when the target band sits only 2–3°F below the latest forecast low and several overnight hours remain before the climate day ends.
- S&P 500 downside-threshold NO entries remain vulnerable to overnight macro shocks even with roughly 4% spot-to-strike cushion over a two-session holding window.

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books
- Buying 95–96¢ YES in near-decided, high-liquidity markets requires confirming the resolution event will occur before market close, not just that the eventual underlying value is very likely.
- Buying 95–96¢ YES is justified in mechanically resolved reference-price markets when the source publication is fixed and there is no appeal or discretionary revision path.
- In review-aggregate markets, paying up for YES is justified only after verifying the contract uses a strict-above threshold and checking that the current margin over the strike can absorb plausible late updates.
- For CPI-family markets, paying 93–96¢ YES is justified only when the best live forecasts still clear the contract threshold after one-decimal rounding rather than merely in raw percentage terms.
- Do not force fallback entries into 92–96¢ NO positions when the remaining risk window still includes overnight weather movement or multiple cash-equity sessions.

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
- Government shutdowns can postpone scheduled BLS releases and break “deterministic publication” assumptions for macro-stat markets.
