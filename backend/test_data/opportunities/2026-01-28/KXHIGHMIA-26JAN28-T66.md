---
id: opp_896b97d4
event_ticker: KXHIGHMIA-26JAN28
market_ticker: KXHIGHMIA-26JAN28-T66
yes_price: 0.62
no_price: 0.43
close_time: '2026-01-29T04:59:00Z'
discovered_at: '2026-01-28T07:54:39.349713Z'
status: skipped
research_completed_at: '2026-01-28T08:01:54.593631+00:00'
research_duration_seconds: 104
estimated_true_probability: 0.15
current_market_price: 0.62
expected_value: -0.7581
edge: -0.47
suggested_position_pct: 0.0
edge_no: 0.42
expected_value_no: 0.9767441860465117
suggested_position_pct_no: 0.18421052631578946
recommendation_completed_at: '2026-01-28T08:03:25.408213+00:00'
action: null
---

# Will the high temp in Miami be <66° on Jan 28, 2026?

**Outcome**: 65° or below

## Scout Assessment

**Rationale**: Market data — 5-cent spread, volume 10,672 (meets liquidity filter); yes_ask=62 → implied yes 62% that high ≤65°F. Closes 2026-01-29T04:59:00Z. Research: National Weather Service point forecasts for Miami (Miami Intl Airport area) show high temperature guidance well above 65°F (forecast discussion and point forecast pages updated Jan 27–28, 2026); corroborating public forecasts (timeanddate/weather-aggregators) and active Polymarket temperature markets show consensus favouring highs ≥66–68°F. Resolution for temperature markets uses the Miami Intl Airport (KMIA) historical/Wunderground record. Edge thesis: official meteorological forecasts and market consensus point to a high above 65°F, so the Kalshi market's 62% pricing for ≤65°F looks likely overstated — researchable edge to buy NO. Sources: https://forecast.weather.gov/MapClick.php?lat=25.77481000000006&lon=-80.19772999999998, https://www.timeanddate.com/weather/@z-us-33196, https://polymarket.com/event/highest-temperature-in-miami-on-january-28, https://www.wunderground.com/history/daily/us/fl/miami/KMIA/date/2026-01-28

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 62¢ ($0.62) |
| No Price | 43¢ ($0.43) |
| Closes | 2026-01-29 04:59 AM |

---

## Research Synthesis

### Researched Questions

- What did the National Weather Service (Miami - KMFL) point forecast and forecast discussion state for the high temperature at Miami (KMIA) on January 28, 2026? 
- What did public observation/aggregation sources record as the highest temperature at Miami Intl Airport (KMIA) on January 28, 2026, and which station/data product is used for settlement of temperature markets? 
- What is the climatological/base-rate context for Miami highs in late January (how common is a daily high ≤65°F at KMIA)? 
- What synoptic/weather drivers on Jan 27–28, 2026 (frontal passages, cold-air advection, cloud/wind) could plausibly push the daytime high at KMIA at-or-below 65°F or, conversely, support a warmer high? 

---

Research Synthesis

Event overview

The National Weather Service (Miami) point forecast valid for the Miami area that covers the Jan 28, 2026 local day showed a forecast daytime high in the upper-60s. The point-forecast page lists a Wednesday high of 67°F and the detailed text summary includes “High: 67 °F.” The Miami office’s Area Forecast Discussion (AFD) issued 00–01 UTC on Jan 28, 2026 characterizes the short-term expectation as "comfortable temperatures in the mid 60s" and gives preliminary point temps showing Miami with a daytime maximum near 68°F. Those forecasts were posted in the early-morning forecast products issued on Jan 28 and updated into the same morning.

Observed/resolution data and product used by markets

Public observation aggregators (hourly station observations and historic pages) show the observed hourly series for Miami International Airport on Jan 28, 2026 peaking in the upper 60s. Timeanddate’s hourly record for the Miami International Airport station (the same METAR location) shows an observed hourly maximum of 68°F at about 15:53 local time. Weather Underground’s KMIA daily-history page for Jan 28, 2026 appeared to show “No data recorded” at the time the page was loaded; some vendors and archival pages can lag or temporarily suppress display while final quality-control/post-processing occurs. Independent prediction-market venues that run Miami temperature markets (example: Polymarket) explicitly reference the Miami Intl Airport/Wunderground KMIA daily-history product as their resolution source for similar markets (and state that the Wunderground KMIA daily history will be used once finalized). Many trading guides and market descriptions for airport-based temperature markets note that settlement typically relies on an authoritative station record (NWS CLI or the ASOS/METAR-derived daily maximum recorded for the station) for the official daily high.

Base rates / historical precedent

Long-term normals and routine climatology indicate Miami’s January daily highs are well above 65°F. Climate-normal tables and local climate summaries list the typical maximum for late-January as roughly the mid-to-upper 70s F (for example, a daily normal maximum near 76–77°F is shown for late-January dates in Miami’s climate summaries). The Miami forecast office’s own climate summary product lists a “normal” maximum for the date near 77°F. That establishes that a daytime high of ≤65°F on a late-January day in Miami is below climatology and therefore less common as a base-rate event.

Key drivers and dependencies

Bullish-for-≤65 (factors that would push the high at-or-below 65):
- A strong cold-air intrusion combined with persistent onshore clouds / cool northerly flow and relatively low insolation could suppress daytime highs into the low-to-mid 60s. The Miami AFD and local media were explicitly monitoring an arctic front and a pronounced cold snap later in the forecast period (late weekend), showing that cold intrusions were part of the synoptic pattern in late January 2026. 
- Increased cloud cover and stronger onshore winds during the daytime would reduce solar heating, lowering the peak temperature compared to clear-sky forecasts.

Bearish-for-≤65 (factors that favor a high >65):
- The operational local forecast products issued the morning of Jan 28 called for mid-to-upper 60s (67–68°F) for Miami—above the ≤65 threshold. The AFD explicitly states “By this afternoon, comfortable temperatures in the mid 60s are expected area‑wide” and gives a Miami preliminary maximum near 68°F, which is already above 65.
- Hourly observations and independent aggregators show the hourly series reached upper 60s (Timeanddate peak 68°F), consistent with the operational forecast.
- Climatology favors highs well above 65 in late January; that means the burden for a ≤65 outcome is to have one or more of the suppressing factors dominate on that specific day.

Counterpoints and risks / data uncertainties

- Resolution-source timing and QA: some public-facing archives (e.g., Wunderground’s KMIA history page) may be temporarily incomplete or delayed; markets that name Wunderground as the resolution source will await the vendor’s finalized daily history. If Wunderground later reports a different final value than real-time aggregator snapshots, that could change the official settled value. 
- Microsite/urban effects and representativeness: airport stations can be influenced by local microclimate (runway, tarmac, nearby pavement, station siting); these micro-effects can create small differences from downtown or inland readings, but they are the canonical station used by markets and NWS products. 
- Rapid intra-day changes: a partly cloudy day with intermittent onshore breezes can produce hour-to-hour swings near the threshold—if the official station’s peak hour differs by a degree from an aggregator snapshot, the market outcome can flip because settlement uses whole-degree reporting.

Timeline and decision points

- Forecast issuance: NWS point forecast and AFD issued early on Jan 28 (first products updated ~02:00–05:00 EST) and showed highs in the 67–68°F range for the local day—these are the primary operational forecast products in effect during the market’s final trading window. 
- Observation/settlement window: the official daily maximum for the station is determined from the station’s 24‑hour observation (METAR/ASOS-derived maxima) and/or the CLI/daily summary—markets that cite Wunderground wait for that vendor’s finalized daily-history product. The key decision point for settlement is when that final daily history is posted and whether it records a maximum ≤65 or ≥66.

What would change the outlook (signals to watch)

- A post‑event revision or delayed finalization by Wunderground/KMIA that differs from the live-hourly snapshots would alter which contract outcome is correct. 
- Any mid‑day observational anomalies (e.g., a sudden cloud increase or frontal timing change that keeps the station below 66°F at the peak hour) would be the physical mechanism to produce a ≤65°F result. 
- Conversely, if the station’s finalized daily maximum equals the observed hourly peak shown in independent aggregators (upper 60s, e.g., 68°F), that would resolve the contract above the 65°F threshold.

Summary (objective facts only)

- NWS operational forecasts issued early on Jan 28, 2026 called for a Miami daytime high in the upper-60s (67–68°F). The AFD text and preliminary point temps explicitly list Miami highs near 67–68°F. 
- Hourly observation aggregators (Timeanddate hourly series for KMIA) show an observed hourly peak of 68°F on Jan 28, 2026 (15:53 local). Wunderground’s KMIA daily history page loaded with “No data recorded” at the time it was queried (some vendor pages can lag finalization). 
- Climatology indicates that January highs in Miami normally run in the mid‑ to upper‑70s; a high ≤65°F is below normal and therefore a less common event under typical conditions. 
- Markets and third‑party guides for airport temperature contracts typically rely on station-level official daily maxima (NWS CLI / ASOS/METAR-derived) or vendor-finalized history pages (e.g., Wunderground) for settlement; any final settled outcome depends on whichever authoritative record is specified by the market and its vendor’s finalized entry.

### Sources

1. https://forecast.weather.gov/MapClick.php?lat=25.77481000000006&lon=-80.19772999999998
2. https://forecast.weather.gov/product.php?format=CI&glossary=1&issuedby=MFL&product=AFD&site=MFL&version=1
3. https://www.wunderground.com/history/daily/us/fl/miami/KMIA/date/2026-01-28
4. https://www.timeanddate.com/weather/usa/miami/historic?month=1&year=2026
5. https://polymarket.com/event/highest-temperature-in-miami-on-january-28
6. https://www.cbsnews.com/miami/news/south-florida-weather-miami-fort-lauderdale-miami-dade-broward-january-27-2026/
7. https://www.usclimatedata.com/climate/miami/florida/united-states/usfl0316
8. https://kamala.cod.edu/offs/KMFL/2501280921.cdus42.MIA.html

---

## Trade Evaluation

| Side | Edge | EV | Suggested Size |
|------|------|-----|----------------|
| **YES** | -47% | -76% | 0.0% |
| **NO** | +42% | +98% | 18.4% |

**Status**: Pending

### Reasoning

Evidence quality is solid: credible, recent NWS point forecast and AFD (day‑of) called 67–68°F; independent hourly observations (Timeanddate) show a 68°F peak; climatology strongly disfavors ≤65°F in late January. Source diversity is good (NWS ops/climate products, aggregator observations, vendor used for settlement noted), with the main uncertainty being Wunderground’s final daily-history posting/QA lag. Conflicts are minimal and explained. Base rate and specific observations both indicate YES is unlikely. Given this, the market’s 62% YES appears overstated. Edge for YES is negative and below the 5% threshold; NO shows large positive edge, though settlement-source finalization risk remains.