---
id: opp_fb952a2b
event_ticker: KXHIGHMIA-26MAR09
market_ticker: KXHIGHMIA-26MAR09-B84.5
yes_price: 0.93
no_price: 0.09
close_time: '2026-03-10T03:59:00Z'
discovered_at: '2026-03-09T19:00:27.795489Z'
status: recommended
research_completed_at: '2026-03-09T19:07:11.695568+00:00'
research_duration_seconds: 151
recommendation_completed_at: '2026-03-09T19:07:14.882286+00:00'
action: null
---

# Will the high temp in Miami be 84-85° on Mar 9, 2026?

**Outcome**: 84° to 85°

## Scout Assessment

**Rationale**: 1) Outcome Status -- STRONGLY FAVORED: Miami International Airport has already reached 84°F at 1:53 pm and 2:53 pm EDT on March 9, 2026, and the official NWS digital forecast keeps the rest of the day at 84°F or lower, making the 84-85°F band the most likely settled outcome. 2) Supporting Evidence -- NOAA/NWS observation history shows 84°F at both 13:53 and 14:53 EDT, while the hourly forecast peaks at 84°F before easing this evening. 3) Resolution Source -- Kalshi states weather markets settle from the final NWS Daily Climate Report for the relevant station. 4) Risk Checklist -- clear resolution source identified, no formal appeal path, strong position from the observed high already inside the band, and same-day official corroboration all pass. 5) Risk Level -- LOW; this was the single lowest-risk available candidate and is selected as FORCED_FALLBACK because no Tier 4+ market in the prefetched universe was near-decided. 6) Remaining Risks -- A late 85°F reading still wins YES, but an unexpected 86°F+ spike would flip the market; otherwise none identified. 7) Sources -- https://forecast.weather.gov/data/obhistory/KMIA.html ; https://forecast.weather.gov/MapClick.php?FcstType=digital&lat=25.7947&lg=english&lon=-80.3371 ; https://help.kalshi.com/markets/popular-markets/weather-markets

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 93¢ ($0.93) |
| No Price | 9¢ ($0.09) |
| Closes | 2026-03-10 03:59 AM |

---

## Research Synthesis

**Flip Risk: NO**

**Event Status:**  
The determining event is still proceeding normally: NWS/NOAA are publishing live KMIA observations, and at 1:53 PM EDT on **March 9, 2026** Miami International Airport was reporting **84.0°F**, with the 6-hour and 24-hour maximums also at **84.0°F**. I searched for station outages / delayed climate products and found no relevant KMIA observation outage or climate-report disruption; the only hits were unrelated airport-delay stories. citeturn18view0turn16search0turn16search6

**Key Evidence For YES:**
- The latest official KMIA observation shows **84.0°F at 1:53 PM EDT**, already inside the **84°-85°** bracket, and the running 6-hour / 24-hour max was also **84.0°F** at that timestamp. citeturn18view0
- The NWS digital forecast updated at **2:31 PM EDT Mar 9** projects KMIA temperatures of **83, 83, then 84°F at 3-5 PM EDT**, followed by cooling into the evening; it does **not** project an 86°F+ late spike. citeturn8view0
- NWS Miami’s Area Forecast Discussion at **1:04 AM EDT Mar 9** expected Miami highs in the **mid-80s**, with the preliminary point forecast specifically showing **Miami 84** and **no MFL watches/warnings/advisories**. citeturn10view0

**Key Evidence Against YES / Risks Found:**
- **Operational risk:** Kalshi’s weather-market help page says settlement can be delayed if the final NWS climate high is inconsistent with 6-hour/24-hour METAR highs or if the final report comes in lower than earlier reports. citeturn2view1turn14view0
- **Window-definition risk:** because NWS climate reports use **local standard time**, the relevant day during DST runs from **1:00 AM Mar 9 to 12:59 AM Mar 10 EDT**. Overnight temperatures in the NWS forecast are only in the low-to-mid 70s, so this looks low-risk but it is a real rule nuance. citeturn2view1turn8view0
- **Base-rate evidence is limited:** I did not find a public dataset for how often 92-96¢ daily-temperature brackets fail. The closest official guidance is Kalshi’s note that the forecasted-high bracket is **usually, but not always**, favored; community posts also show occasional confusion when live observations and the climate report diverge. That is evidence of edge-case risk, not proof of safety. citeturn12search8turn15reddit19

**Resolution Mechanics:**  
For **MIAHIGH**, Kalshi resolves to the **maximum temperature published in the NWS Daily Climate Report for Miami, FL**. A **“between”** market is inclusive on both ends, so **84-85° means YES if the expiration value is 84 or 85**. Revisions after expiration are ignored, but determination may be delayed until **11 AM ET** if the final high conflicts with METAR highs or earlier reports. citeturn14view0turn2view1

**Unconfirmed:**
- The final **CLIMIA** report for **March 9, 2026** is not yet published.  
- I did not find authoritative historical outcome data specifically for **93¢** same-day Miami high-temp bands. citeturn14view0turn12search8

**Conclusion:**  
The best current evidence supports **NO flip risk**: the official station has already reached the target band, the latest NWS forecast keeps the rest of the climate day at or below **84°F**, and the rules make **84 or 85** a YES resolution. Confidence is **MEDIUM** rather than high because weather markets can still be affected by final climate-report quirks, and the single biggest remaining uncertainty is whether the **final NWS Daily Climate Report** could differ from the live/6-hour maximum already showing 84°F. citeturn18view0turn8view0turn14view0

Sources:
1. `https://tgftp.nws.noaa.gov/weather/current/KMIA.html`
2. `https://forecast.weather.gov/MapClick.php?FcstType=digital&lat=25.7947&lg=english&lon=-80.3371`
3. `https://forecast.weather.gov/product.php?format=CI&glossary=1&issuedby=mfl&product=AFD&site=NWS&version=1`
4. `https://kalshi-public-docs.s3.amazonaws.com/contract_terms/MIAHIGH.pdf`
5. `https://help.kalshi.com/en/articles/13823837-weather-markets`
6. `https://news.kalshi.com/p/trading-the-weather`
7. `https://forecast.weather.gov/data/obhistory/KMIA.html`
8. `https://www.reddit.com/r/Kalshi/comments/12elwrd/weather_sources/`
9. `https://www.nbcmiami.com/news/local/flight-delays-and-cancellations-seen-at-south-florida-airports-after-historic-chill/3757916/`
10. `https://www.local10.com/news/local/2026/01/14/ground-stop-issued-for-flights-coming-to-miami-international-airport-due-to-weather//`