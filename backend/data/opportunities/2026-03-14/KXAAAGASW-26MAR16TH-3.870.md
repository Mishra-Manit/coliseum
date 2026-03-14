---
id: opp_16d31698
event_ticker: KXAAAGASW-26MAR16TH
event_title: US gas prices this week
market_ticker: KXAAAGASW-26MAR16TH-3.870
yes_price: 0.07
no_price: 0.94
close_time: '2026-03-16T03:59:00Z'
rationale: 'STRONGLY FAVORED: NO — AAA’s published U.S. regular-gas average remains
  well below the $3.870 strike, and the contract resolves from a mechanical source
  rather than discretionary review. NO is offered at 94¢ with a 1¢ spread.'
discovered_at: '2026-03-14T04:07:24.825745Z'
status: recommended
outcome_status: STRONGLY FAVORED
risk_level: LOW
resolution_source: Kalshi’s AAAGAS contract terms name AAA as the source agency for
  the published average regular-gas price, with post-expiration revisions ignored.
evidence_bullets:
- AAA’s national regular-gas average was $3.630 on 3/13/26, which is 24.0¢ below the
  $3.870 strike [gasprices.aaa.com]
- AAA’s 3/12/26 fuel note showed $3.598 nationally versus $3.251 a week earlier, so
  even after a 34.7¢ week-over-week jump the market still sat 27.2¢ below the strike
  on that publication [gasprices.aaa.com]
- AAAGAS contract terms set last trading at 11:59 PM ET on the day before the reference
  date and ignore revisions published after expiration [kalshi-public-docs.s3.amazonaws.com]
- This market is priced NO 94¢ / YES 7¢ with a 1¢ spread and 30,330 contracts of volume
  in the prefetched Kalshi data [kalshi.com]
remaining_risks:
- A fresh weekend oil shock could accelerate pump-price pass-through before the reference
  print
- If AAA fails to publish the reference-date value, contract terms fall back to the
  last available day’s data
scout_sources:
- https://gasprices.aaa.com/
- https://gasprices.aaa.com/rising-pump-prices-higher-gas-demand-as-spring-break-begins/
- https://gasprices.aaa.com/about-aaa/
- https://kalshi-public-docs.s3.amazonaws.com/contract_terms/AAAGAS.pdf
- https://kalshi.com/markets/kxaaagasw/us-gas-price-up
research_completed_at: '2026-03-14T04:11:56.220826+00:00'
research_duration_seconds: 237
recommendation_completed_at: '2026-03-14T04:12:04.457518+00:00'
action: null
---

# Will average gas prices be above $3.870?
**Event**: US gas prices this week

**Outcome**: Above $3.870

## Scout Assessment

**STRONGLY FAVORED**  ·  **LOW RISK**

STRONGLY FAVORED: NO — AAA’s published U.S. regular-gas average remains well below the $3.870 strike, and the contract resolves from a mechanical source rather than discretionary review. NO is offered at 94¢ with a 1¢ spread.

**Evidence**
- AAA’s national regular-gas average was $3.630 on 3/13/26, which is 24.0¢ below the $3.870 strike [gasprices.aaa.com]
- AAA’s 3/12/26 fuel note showed $3.598 nationally versus $3.251 a week earlier, so even after a 34.7¢ week-over-week jump the market still sat 27.2¢ below the strike on that publication [gasprices.aaa.com]
- AAAGAS contract terms set last trading at 11:59 PM ET on the day before the reference date and ignore revisions published after expiration [kalshi-public-docs.s3.amazonaws.com]
- This market is priced NO 94¢ / YES 7¢ with a 1¢ spread and 30,330 contracts of volume in the prefetched Kalshi data [kalshi.com]

**Resolution**
Kalshi’s AAAGAS contract terms name AAA as the source agency for the published average regular-gas price, with post-expiration revisions ignored.

**Risks**
- A fresh weekend oil shock could accelerate pump-price pass-through before the reference print
- If AAA fails to publish the reference-date value, contract terms fall back to the last available day’s data

**Sources**
- https://gasprices.aaa.com/
- https://gasprices.aaa.com/rising-pump-prices-higher-gas-demand-as-spring-break-begins/
- https://gasprices.aaa.com/about-aaa/
- https://kalshi-public-docs.s3.amazonaws.com/contract_terms/AAAGAS.pdf
- https://kalshi.com/markets/kxaaagasw/us-gas-price-up

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 7¢ ($0.07) |
| No Price | 94¢ ($0.94) |
| Closes | 2026-03-16 03:59 AM |

---

## Research Synthesis

**Flip Risk:** NO

**Event Status:**
This is a mechanical data-release market, not a discretionary event. AAA’s fuel page was updating normally and showed the U.S. regular-gas average at **$3.630 as of March 13, 2026**; I found no announced interruption to AAA publication. AAAGAS rules also say that if no AAA value is available at expiration, Kalshi uses the **last available day’s data**. [AAA current] [AAAGAS rules] citeturn10view0turn19view1

**Key Evidence For YES:**
- AAA’s national average rose from **$3.320 week-ago to $3.630 current**, a **31.0¢** jump in seven days; AAA tied the move to spring-break demand and sharply higher crude prices. [AAA current] [AAA Mar. 12 note] citeturn10view0turn21view0
- EIA’s latest petroleum data showed gasoline demand rising to **9.24 million b/d**, total gasoline inventories falling **3.7 million barrels**, and refineries running at **90.8%** utilization. [WPSR] citeturn14view0
- EIA’s March STEO says higher crude prices are adding roughly **60¢/gal** to March gasoline prices versus last month’s forecast, and that most of the pass-through will show up in coming weeks. [EIA STEO] citeturn28view0turn28view1

**Key Evidence Against YES:**
- The strike is **$3.870**, leaving a **24.0¢** gap from AAA’s current **$3.630**. [AAA current] citeturn10view0turn27calculator0
- EIA’s latest U.S. regular-gas average was **$3.502** for the week of **March 9, 2026**, still **36.8¢** below the strike; WPSR also says gasoline inventories remain **5% above** the five-year average. [EIA gasoline update] [WPSR] citeturn11view1turn14view0
- If AAA’s last 7-day pace merely persisted for three more days, the implied level would be about **$3.763**, still below **$3.870**. That is an inference, not a published forecast. [AAA current] [calc] citeturn10view0turn27calculator1turn27calculator2
- No specific nationwide refinery outage or AAA publication failure surfaced in searches for **"March 2026 refinery outage gasoline prices United States"** and **"AAA gas prices outage March 2026."**

**Resolution Mechanics:**
The critical source question matters here. Kalshi has an older **GAS** contract on file that resolves off **EIA All Grades – Conventional Areas**, but the newer **AAAGAS** rulebook for this series says the Underlying is **AAA’s average price for regular gas** in the specified area/date, and YES resolves only if that AAA value is above the strike. [AAAGAS filing] [older GAS filing] citeturn19view1turn9view0

**Unconfirmed:**
- I did not find a public archive quantifying how often **AAAGASW** markets priced at **92–96¢** resolve as expected; base-rate evidence for this exact price band is thin.
- I did find conflicting public commentary on near-term upside: one analyst quoted by Axios saw a peak around **$3.50** in coming weeks, while another cited an **80% chance of $4** within the next month. Both horizons are broader than this contract’s March 16 target. [Axios] citeturn26news12turn26news13

**Conclusion:**
The bearish case against YES is still stronger. Current AAA and latest EIA readings are materially below **$3.870**, and the exact resolution source appears to be the mechanical **AAA regular-gas** print, not a discretionary review. The real flip path is a war-driven weekend repricing shock that pushes the national average up another 24 cents almost immediately; I found evidence of upward pressure, but not enough to show that jump is likely by **March 16, 2026**. Final sentence: Confidence: MEDIUM. Biggest uncertainty: war-driven weekend pump repricing.

**Sources:**
- AAA fuel page / AAA March 12 market note citeturn10view0turn21view0
- EIA Gasoline and Diesel Fuel Update / Weekly Petroleum Status Report / March STEO citeturn11view1turn14view0turn28view0turn28view1
- CFTC-filed AAAGAS and GAS contract rules citeturn19view1turn19view0turn9view0
- Market-context reporting on analyst upside cases citeturn26news12turn26news13turn26search1