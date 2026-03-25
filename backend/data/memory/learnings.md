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
- CPI-family thresholds at **0.0%** and **0.1%** must be evaluated on the published one-decimal BLS figure because a raw positive print can still resolve NO after rounding.
- Same-day weather band NO entries are favorable when the latest official observation and NWS point forecast leave at least **4°F** of cushion below the target band and the remaining climate-day temperature path is flat or falling.
- Same-day weather threshold NO entries are favorable when an overnight or post-front pattern makes the daily high likely to occur well below the strike early in the climate window and temperatures are forecast to decline afterward.
- Same-day weather band NO entries are unsafe when the target band sits only **2–3°F** below the latest forecast low and several overnight hours remain before the climate day ends.
- Same-day weather threshold YES entries at **94–95¢** are unsafe when the official NWS climate day remains open under DST and the station can still print a lower overnight minimum after the preliminary CLI shows the threshold cleared.
- Coastal-airport weather NO entries remain favorable when the latest official reading is materially below the strike and the NWS forecast discussion cites marine-layer or onshore-flow caps that keep heating below the threshold.
- Same-day coastal-airport weather NO entries are favorable when the official station forecast shows multiple midday hours at or above the losing threshold and the market still prices NO inside the **93–94¢** range.
- WTI daily-settlement NO entries are favorable when the losing outcome is a narrow **$1** band or a far-away downside threshold and the latest confirmed settlement is still several dollars outside the losing range.
- S&P 500 downside-threshold NO entries remain vulnerable to overnight macro shocks even with roughly **4%** spot-to-strike cushion over a two-session holding window.
- **AAAGAS** weekly gas-price threshold NO entries are favorable when the named **AAA** regular-gas print sits at least **20¢** below the strike with only a few days remaining and the contract fallback still uses the last available **AAA** value.
- **AAAGAS** overnight threshold **NO** entries at **96¢** are acceptable when the latest **AAA** regular-gas print is still below the strike, the strike requires a next-day move larger than the latest one-day increase, and the contract resolves mechanically from **AAA** or its last available print.
- **KXBTCD** same-day downside-threshold **YES** entries at **96¢** are favorable when spot is already several percent above the strike, the same-day intraday low has also stayed above the strike, and the contract resolves from the final **60-second** **CF Benchmarks** average.

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books
- Buying **95–96¢** YES in near-decided, high-liquidity markets requires confirming the resolution event will occur before market close, not just that the eventual underlying value is very likely.
- Buying **95–96¢** YES is justified in mechanically resolved reference-price markets when the source publication is fixed and there is no appeal or discretionary revision path.
- In review-aggregate markets, paying up for YES is justified only after verifying the contract uses a strict-above threshold and checking that the current margin over the strike can absorb plausible late updates.
- For CPI-family markets, paying **93–96¢** YES is justified only when the best live forecasts still clear the contract threshold after one-decimal rounding rather than merely in raw percentage terms.
- Same-day weather NO entries at **94–96¢** are acceptable forced-fallback trades only after confirming the exact station resolution source, the DST-adjusted climate-day window, and a forecast path that still misses the band after plausible late-day variance.
- Same-day weather NO entries at **93–94¢** are acceptable when the official NWS station mapping is confirmed, the spread is **1¢**, and the forecast path shows several hours beyond the threshold rather than a single marginal print.
- Do not buy same-day weather YES above **94¢** if the remaining DST-adjusted climate window still includes post-midnight local-standard-time hours that can reset the daily minimum or maximum.
- Do not force fallback entries into **92–96¢** NO positions when the remaining risk window still includes overnight weather movement or multiple cash-equity sessions.
- In mechanical threshold markets, high-price **NO** entries are acceptable when the source is explicitly named, revisions after expiration are ignored, and the remaining move needed to lose is materially larger than the latest observed multi-day change.
- In crypto timestamp markets, paying **96¢** for **YES** is acceptable only after confirming the exact benchmark source and verifying both spot and the current-day low remain above the strike.

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
- Government shutdowns can postpone scheduled BLS releases and break “deterministic publication” assumptions for macro-stat markets.
- Do not enter same-day weather trades until the exact Kalshi market page or product certification confirms the station mapping and resolution source.
- In crypto markets, do not rely on exchange-app prints alone because Kalshi resolves from the named benchmark composite and the final **60-second** average can differ from a single venue snapshot.