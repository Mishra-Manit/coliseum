---
id: opp_b4c06bad
event_ticker: KXLOWTCHI-26MAR11
market_ticker: KXLOWTCHI-26MAR11-B28.5
yes_price: 0.05
no_price: 0.96
close_time: '2026-03-12T05:00:00Z'
discovered_at: '2026-03-11T22:47:45.040879Z'
status: recommended
research_completed_at: '2026-03-11T22:55:52.791146+00:00'
research_duration_seconds: 221
recommendation_completed_at: '2026-03-11T22:55:59.387581+00:00'
action: null
---

# Will the minimum temperature be 28-29° on Mar 11, 2026?

**Outcome**: 28° to 29°

## Scout Assessment

**Rationale**: FORCED_FALLBACK — STRONGLY FAVORED: among this prefetched universe, the lower-tier alternatives are pre-event price or polling markets with greater swing risk, so the least-risky available setup is BUY NO here; Chicago is currently 36°F and the latest forecast low for Wednesday, March 11 is 31°F, leaving the 28-29°F band a few degrees below forecast with only several overnight hours remaining. Supporting Evidence: the current market is priced at YES 0.05 / NO 0.96, and late-day weather inputs show cooling from the mid-30s rather than conditions already near the strike. Resolution Source: Kalshi weather markets settle from the National Weather Service final Daily Climate Report, giving a clear official authority. Risk Checklist: passed clear resolution source, no formal challenges identified, recent corroboration, and stable late-day inputs. Risk Level: LOW, and this was selected as the single lowest-risk available candidate. Remaining Risks: a sharper-than-forecast late-night drop into the exact 28-29°F band. Sources: https://help.kalshi.com/markets/popular-markets/weather-markets ; https://forecast.weather.gov/data/obhistory/KORD.html

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 5¢ ($0.05) |
| No Price | 96¢ ($0.96) |
| Closes | 2026-03-12 05:00 AM |

---

## Research Synthesis

**Flip Risk: NO**

**Event Status:**
The determining event is proceeding normally: Chicago Midway (KMDW) observation history is updating intraday, and the weather-market rule set points to the NWS Daily Climatological Report as the settlement source for Chicago low-temperature markets. By **4:53 pm CDT on March 11**, KMDW was still **35.1°F**, so the event has effectively been observed for most of the relevant day already. citeturn24view0turn18search1turn4view1

**Key Evidence For YES:**
- NWS Chicago normals list the **March 11 normal low for Chicago as 29.6°F**, which sits inside the 28-29 band; climatologically, the strike is not absurd. citeturn20search0
- Nearby suburban NWS point forecasts this afternoon called for lows around **29-30°F tonight**, so the surrounding air mass can support upper-20s temperatures nearby even if not necessarily at Midway. citeturn19search1turn19search3turn23view0
- Community discussion shows a real operational nuance: final NWS climate-report values can differ slightly from what traders infer from hourly displays because of measurement/rounding conventions. citeturn15reddit16turn15reddit21

**Key Evidence Against YES / Risks Found:**
- KMDW observations for **March 11** ran from **46°F at 12:53 am** down only to **35.1°F** by **1:53 pm** and again **4:53 pm**; no observed print has approached 28-29°F. citeturn24view0
- The official NWS hourly forecast for **Chicago Midway**, updated **2:26 pm CDT March 11**, keeps the station at **36→35°F through 11 pm on March 11**. The colder **31°F** forecast appears **after midnight on March 12**, which I infer should not count for a contract defined on **March 11 local time**. citeturn14view0turn4view1
- Searches surfaced weather-market complaints, but they are about rounding/settlement interpretation rather than Chicago daily-low markets being manually disputed, voided, or structurally ambiguous in the same way as speech/entertainment markets. citeturn15reddit12turn15reddit20turn15reddit21

**Resolution Mechanics:**
Same-family Coinbase/Kalshi weather pages say Chicago low-temp markets resolve from the NWS **Climatological Report (Daily)** using **CLIMDW / Chicago-Midway** data, and the CFTC-filed Kalshi temperature rules say the exchange uses the most recent Daily Climate Report, with **“between” interpreted inclusively** and the time period ending at **11:59:59 PM local time** unless otherwise specified. Ambiguity is low, but intraday dashboards can still mislead traders. citeturn18search1turn4view1

**Unconfirmed:**
- I did not find a public page for this exact strike with ticker-specific rule text.
- I did not find a quantified historical hit rate for **92-96¢ NO** in this exact market family.
- I found no official outage notice affecting NWS Chicago climate products in the sources checked, but that is still unconfirmed rather than guaranteed safe.

**Conclusion:**
Based on actual **KMDW March 11 observations** plus the official **same-day hourly forecast through 11 pm**, the 28-29°F YES outcome looks materially out of line with both observed and forecast conditions. My verdict is **NO flip risk** for the high-probability side, with **HIGH** confidence. The biggest remaining uncertainty is not cancellation or rule discretion; it is the small but real measurement/rounding gap between hourly displays and the final NWS climate report.

**Sources:**
1. `https://forecast.weather.gov/data/obhistory/KMDW.html`
2. `https://forecast.weather.gov/MapClick.php?FcstType=digital&lat=41.7868&lg=english&lon=-87.7455`
3. `https://www.coinbase.com/en-br/predictions/event/KXLOWTCHI-26FEB11`
4. `https://www.cftc.gov/filings/ptc/ptc03052640383.pdf`
5. `https://www.weather.gov/lot/march_normals_chicago`
6. `https://forecast.weather.gov/MapClick.php?CityName=Hines&state=IL&site=LOT&lat=41.8567&lon=-87.8318`
7. `https://www.reddit.com/r/Kalshi/comments/1pqjogk/either_im_doing_something_wrong_or_kalshi_is/`
8. `https://www.reddit.com/r/Kalshi/comments/12elwrd`
9. `https://www.reddit.com/r/Trading/comments/1r8pwd1/robinhood_temperature_settlement_discrepancy_kmdw/`
10. `https://www.reddit.com/r/Kalshi/comments/xb46x7`