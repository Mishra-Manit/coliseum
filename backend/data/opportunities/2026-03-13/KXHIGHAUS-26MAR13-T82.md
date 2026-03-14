---
id: opp_5e66893f
event_ticker: KXHIGHAUS-26MAR13
event_title: Highest temperature in Austin on Mar 13, 2026?
market_ticker: KXHIGHAUS-26MAR13-T82
yes_price: 0.07
no_price: 0.94
close_time: '2026-03-14T04:59:00Z'
rationale: 'STRONGLY FAVORED FORCED_FALLBACK: BUY NO — official Austin guidance still
  tops out around 79-80°F, leaving a 3-4°F cushion below the 83°F YES trigger late
  in the day. The market is available at 94¢ NO.'
discovered_at: '2026-03-13T20:27:59.394782Z'
status: skipped
outcome_status: STRONGLY FAVORED
risk_level: LOW
resolution_source: Kalshi resolves this contract from the National Weather Service
  Austin/San Antonio daily climate report for Austin-Bergstrom International Airport,
  using the official maximum temperature for March 13.
evidence_bullets:
- NO ask is 94¢ versus YES ask 7¢, with a 1¢ spread and 18,631 volume [kalshi]
- Austin-Bergstrom was 77°F at 2:53 PM CDT on Mar. 13 [tgftp.nws.noaa.gov]
- NWS Austin/San Antonio point forecast calls for a high near 79°F this afternoon,
  4°F below the 83°F YES trigger [weather.gov]
- NWS preliminary point temps list Austin Bergstrom at 80°F for Mar. 13, still 3°F
  below the YES trigger [weather.gov]
remaining_risks:
- Late-day heating could still overperform the official forecast by 3°F or more
- Airport microclimate variance can still push the final reading to 83°F+
scout_sources:
- https://tgftp.nws.noaa.gov/weather/current/KAUS.html
- https://www.weather.gov/ewx/forecasts
- https://www.weather.gov/sanantonio
research_completed_at: '2026-03-13T20:33:26.110584+00:00'
research_duration_seconds: 177
recommendation_completed_at: '2026-03-13T20:33:31.481343+00:00'
action: null
---

# NO — Will the high temp in Austin be >82° on Mar 13, 2026?
**Event**: Highest temperature in Austin on Mar 13, 2026?

**Outcome**: 83° or above

## Scout Assessment

**STRONGLY FAVORED**  ·  **LOW RISK**

STRONGLY FAVORED FORCED_FALLBACK: BUY NO — official Austin guidance still tops out around 79-80°F, leaving a 3-4°F cushion below the 83°F YES trigger late in the day. The market is available at 94¢ NO.

**Evidence**
- NO ask is 94¢ versus YES ask 7¢, with a 1¢ spread and 18,631 volume [kalshi]
- Austin-Bergstrom was 77°F at 2:53 PM CDT on Mar. 13 [tgftp.nws.noaa.gov]
- NWS Austin/San Antonio point forecast calls for a high near 79°F this afternoon, 4°F below the 83°F YES trigger [weather.gov]
- NWS preliminary point temps list Austin Bergstrom at 80°F for Mar. 13, still 3°F below the YES trigger [weather.gov]

**Resolution**
Kalshi resolves this contract from the National Weather Service Austin/San Antonio daily climate report for Austin-Bergstrom International Airport, using the official maximum temperature for March 13.

**Risks**
- Late-day heating could still overperform the official forecast by 3°F or more
- Airport microclimate variance can still push the final reading to 83°F+

**Sources**
- https://tgftp.nws.noaa.gov/weather/current/KAUS.html
- https://www.weather.gov/ewx/forecasts
- https://www.weather.gov/sanantonio

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 7¢ ($0.07) |
| No Price | 94¢ ($0.94) |
| Closes | 2026-03-14 04:59 AM |

---

## Research Synthesis

**Flip Risk:** NO

**Event Status:**
The event window is ongoing on **Friday, March 13, 2026** and NWS Austin/San Antonio said Friday would stay dry, with **no watches/warnings/advisories** posted on the forecast page. I also searched for Austin-specific station outages or climate-report delays; I did **not** find an Austin notice, but that null result is not proof that no operational issue can emerge. [S1][S7] citeturn6view0turn14search2

**Key Evidence For YES:**
- Strongest pro-YES evidence: Austin-Bergstrom was already **71°F at 12:53 pm CDT** with sun and gusty south winds, and the live hourly forecast feed still showed **80°F at 4 pm** and **81°F at 5 pm**, so a late-day overshoot is the main bull case. [S2][S3] citeturn20view0turn13forecast0
- March 13 can run much warmer than normal at AUS: the current NWS climate report lists a **normal high of 72°F** and a **record high of 92°F**, so **83°F is meteorologically possible**, just not the base forecast today. [S4] citeturn11view0

**Key Evidence Against YES:**
- The NWS area forecast discussion issued **1:35 pm CDT Mar 13** put **Austin Bergstrom at 79°F** and **Austin Camp Mabry at 80°F** for Friday; the same page shows **83°F on Saturday** and **91°F on Sunday**, implying Friday is the cooler day. [S1] citeturn6view0
- The NWS point forecast for the Austin-Bergstrom area called for **“Sunny, with a high near 79”** this afternoon. [S2] citeturn20view0
- I searched specifically for Austin-specific disruptions/data issues and found no relevant Austin result; the only outage page returned was for **Augusta, Maine**, not Austin. [S7] citeturn14search2

**Resolution Mechanics:**
Kalshi’s **AUSHIGH** rules resolve from the **NWS Daily Climate Report for Austin Bergstrom**, not generic Austin app weather and not Camp Mabry; for a “greater than 82°” contract, **82 does not count**. Kalshi also says weather determinations can be delayed if the final climate report conflicts with METAR highs, and during DST the report uses **local standard time**, so the effective reporting window runs to **12:59 am local time the following day**. [S6][S8] citeturn4view0turn2search0

**Unconfirmed:**
- I found **no authoritative historical Kalshi dataset** showing how often weather contracts priced at 92-96¢ resolve as expected; the best base-rate proxy I found is climatology, where **83°F is 11°F above the Mar 13 normal high** at AUS. [S4][S5]
- Community discussion exists about weather-market rounding/source confusion, but I found no primary-source evidence of a similar Austin temperature dispute for this date. [S9] citeturn11view0turn17view0turn15reddit16

**Conclusion:**
The strongest primary-source evidence points to **Friday topping out around 79-81°F at Austin Bergstrom**, with the hotter air arriving **Saturday/Sunday**, so the 94¢ **NO** side does **not** currently show a strong flip setup. The real residual risk is not a schedule disruption but a **source mismatch / late temperature overshoot**: traders using Camp Mabry or app forecasts could misread a contract that actually settles on **Austin Bergstrom’s final NWS climate report**. **Confidence: MEDIUM. Biggest uncertainty: late-afternoon temperature overshoot at AUS.**

**Sources:**
- [S1] `https://www.weather.gov/ewx/forecasts`
- [S2] `https://forecast.weather.gov/MapClick.php?lat=30.1947&lon=-97.7375`
- [S3] `weather tool: Austin, TX hourly forecast for 2026-03-13`
- [S4] `https://forecast.weather.gov/product.php?site=EWX&issuedby=AUS&product=CLI&format=CI&version=1&glossary=1`
- [S5] `https://www.weather.gov/media/ewx/climate/AUSMarch.pdf`
- [S6] `https://kalshi-public-docs.s3.amazonaws.com/contract_terms/AUSHIGH.pdf`
- [S7] search: `Austin Bergstrom ASOS outage / climate report delayed March 13 2026`
- [S8] `https://help.kalshi.com/markets/popular-markets/weather-markets`
- [S9] `https://www.reddit.com/r/Kalshi/comments/12elwrd/weather_sources/`