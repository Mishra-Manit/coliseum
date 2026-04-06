---
id: opp_8a4a6c42
event_ticker: KXLOWTDEN-26MAR23
event_title: Lowest temperature in Denver on Mar 23, 2026?
market_ticker: KXLOWTDEN-26MAR23-B40.5
yes_price: 0.05
no_price: 0.96
close_time: '2026-03-24T07:00:00Z'
rationale: 'NEAR-DECIDED: NO — adjacent Denver bands show the market already centering
  the daily low above 41°, and this contract only loses if the official minimum lands
  exactly 40–41°. NO is offered at 96¢, leaving a 4¢ path to resolution.'
discovered_at: '2026-03-23T22:26:49.328399Z'
status: skipped
outcome_status: NEAR-DECIDED
risk_level: LOW
resolution_source: National Weather Service Climatological Report (Daily) for Denver
  determines the rounded whole-degree minimum temperature for March 23, 2026, and
  Kalshi resolves from that final reported low.
evidence_bullets:
- Adjacent Denver bands are priced at **93¢ YES** for 42–43° and **5¢ YES** for 40–41°,
  an **88¢** gap that centers the daily low just above this contract’s losing range
  [kalshi].
- NWS Denver’s forecast updated **2:46 pm MDT Mar 23** lists tonight’s low near **49°F**,
  which is **8°F** above the 40–41° YES band [weather.gov].
- The Denver point forecast was valid from **2pm MDT Mar 23** and the market closes
  at **1:00 am MDT Mar 24**, leaving only the evening cooling window before expiry
  [weather.gov].
remaining_risks:
- A sharper-than-forecast late-evening cool-down could still pull Denver into 40-41°F
- The official Denver climate report can differ slightly from nearby point-forecast
  conditions
scout_sources:
- https://forecast.weather.gov/MapClick.php?CityName=Denver&state=CO&site=BOU&textField1=39.75&textField2=-104.99&e=1
- https://www.weather.gov/wrh/Climate?wfo=bou
research_completed_at: '2026-03-23T22:30:40.237629+00:00'
research_duration_seconds: 200
recommendation_completed_at: '2026-03-23T22:30:44.304171+00:00'
action: null
---

# Will the minimum temperature be 40-41° on Mar 23, 2026?
**Event**: Lowest temperature in Denver on Mar 23, 2026?

**Outcome**: 40° to 41°

## Scout Assessment

**NEAR-DECIDED**  ·  **LOW RISK**

NEAR-DECIDED: NO — adjacent Denver bands show the market already centering the daily low above 41°, and this contract only loses if the official minimum lands exactly 40–41°. NO is offered at 96¢, leaving a 4¢ path to resolution.

**Evidence**
- Adjacent Denver bands are priced at **93¢ YES** for 42–43° and **5¢ YES** for 40–41°, an **88¢** gap that centers the daily low just above this contract’s losing range [kalshi].
- NWS Denver’s forecast updated **2:46 pm MDT Mar 23** lists tonight’s low near **49°F**, which is **8°F** above the 40–41° YES band [weather.gov].
- The Denver point forecast was valid from **2pm MDT Mar 23** and the market closes at **1:00 am MDT Mar 24**, leaving only the evening cooling window before expiry [weather.gov].

**Resolution**
National Weather Service Climatological Report (Daily) for Denver determines the rounded whole-degree minimum temperature for March 23, 2026, and Kalshi resolves from that final reported low.

**Risks**
- A sharper-than-forecast late-evening cool-down could still pull Denver into 40-41°F
- The official Denver climate report can differ slightly from nearby point-forecast conditions

**Sources**
- https://forecast.weather.gov/MapClick.php?CityName=Denver&state=CO&site=BOU&textField1=39.75&textField2=-104.99&e=1
- https://www.weather.gov/wrh/Climate?wfo=bou

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 5¢ ($0.05) |
| No Price | 96¢ ($0.96) |
| Closes | 2026-03-24 07:00 AM |

---

## Research Synthesis

**Flip Risk:** NO

**Event Status:**
The determining event is **ongoing, on schedule**: this market resolves from the daily low for **Mar 23, 2026**, and KDEN was reporting normally through **3:53 PM MDT** on March 23. There is no sports-style postponement/cancellation vector here; the only real open question is what the final overnight minimum prints in the NWS climate report. [NWS KDEN obs; CITYLOW]

**Key Evidence For YES:**
- The contract is **not dead yet**: under CITYLOW, the low is the minimum temperature for the full **Mar 23** climate day, and “between” bands are **inclusive**, so a late-evening dip to **40°F or 41°F** would still settle YES. [CITYLOW]
- Community documentation for Kalshi weather markets notes common confusion around **station choice** and CLI timing; if traders are anchoring to the wrong Denver station, that can create a surprise. Public search did not surface the market page’s source link. [r/Kalshi guide; searched “Kalshi Denver low temperature KDEN station”]

**Key Evidence Against YES:**
- Official KDEN observations show the low so far was already **43°F** at **6:53 AM** and again at **7:53 AM MDT**, above the **40-41°F** band. [NWS KDEN obs]
- KDEN had rebounded to **66.9°F** by **3:53 PM MDT**, so YES now requires a fresh overnight drop of **2-3°F** below the day’s earlier low. [NWS KDEN obs]
- The official NWS point forecast for **Denver International Airport** showed **Monday Night low around 43°F**, not 40-41°F. [NWS KDEN forecast]
- None found on disruption risk — searched for **Denver cancellation/postponement/disruption** and did not find a relevant threat to the observation process.

**Resolution Mechanics:**
This market resolves off the **National Weather Service** Daily Climate Report for the specified city station. Under Kalshi’s **CITYLOW** contract, the underlying is the **minimum temperature** for the specified date, revisions after expiration are ignored, and a “between” strike is **inclusive** of both endpoints; the main ambiguity is the exact station mapping users infer from “Denver.” [CITYLOW; Kalshi Weather Help]

**Unconfirmed:**
- Whether Kalshi’s user-facing source link for this exact market explicitly maps “Denver” to **KDEN**; public search found community claims, but not the market-page rules link.
- No authoritative public dataset surfaced on how often **92-96¢ NO** daily low-temperature buckets fail; community discussion suggests disputes are usually about source/station details, not weather-event cancellation.

**Conclusion:**
The evidence points to **NO** flip risk: the official station already printed a **43°F** low, and the available NWS forecast also centered the overnight low near **43°F**, not **40-41°F**. The remaining risk is mostly operational/microstructure — station mapping or an unexpected late-evening dip — rather than a broad event-status problem. Confidence: **MEDIUM**. Biggest uncertainty: exact station mapping on the market’s source link.

**Sources:**
- https://forecast.weather.gov/data/obhistory/KDEN.html
- https://www.cftc.gov/filings/ptc/ptc12032410040.pdf
- https://help.kalshi.com/markets/popular-markets/weather-markets
- https://forecast.weather.gov/MapClick.php?textField1=39.86&textField2=-104.67
- https://www.reddit.com/r/Kalshi/comments/1hfvnmj/an_incomplete_and_unofficial_guide_to_temperature/