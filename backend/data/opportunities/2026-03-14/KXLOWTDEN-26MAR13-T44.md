---
id: opp_3b86ff43
event_ticker: KXLOWTDEN-26MAR13
event_title: Lowest temperature in Denver on Mar 13, 2026?
market_ticker: KXLOWTDEN-26MAR13-T44
yes_price: 0.94
no_price: 0.09
close_time: '2026-03-14T06:00:00Z'
rationale: 'NEAR-DECIDED: YES — KXLOWTDEN-26MAR13-T44 is priced at 94¢ into a 06:00
  UTC close, and the market only loses if the official Denver low slips below 45°F
  in the final hours. The remaining payout is 6¢ to resolution.'
discovered_at: '2026-03-14T03:48:45.980314Z'
status: recommended
outcome_status: NEAR-DECIDED
risk_level: LOW
resolution_source: National Weather Service / NOAA Denver International Airport observations,
  finalized through the official daily climate report for the station’s March 13 minimum
  temperature.
evidence_bullets:
- KDEN observations for Mar 13 have ranged from 54.0°F to 66.0°F so far, so the observed
  daily low still sits 10.0°F above the 44°F cutoff [weather.gov]
- Latest KDEN reading is 57.9°F at 20:53 MDT, leaving a 13.9°F gap above the failure
  threshold with roughly 2.1 hours left in the local day [weather.gov]
- The contract closes at 06:00 UTC (00:00 MDT), so the remaining exposure window is
  only about 2.2 hours from discovery [kalshi]
- YES is offered at 94¢ with a 3¢ spread, leaving 6¢ gross upside to resolution inside
  the target entry band [kalshi]
remaining_risks:
- A sharp late-evening temperature drop at KDEN below 45°F before local midnight would
  flip the market
- Final settlement waits for the official station-based climate print after the local
  day ends
scout_sources:
- https://forecast.weather.gov/data/obhistory/KDEN.html
- https://www.weather.gov/wrh/climate?wfo=bou
research_completed_at: '2026-03-14T03:56:49.487477+00:00'
research_duration_seconds: 277
recommendation_completed_at: '2026-03-14T03:56:57.376040+00:00'
action: null
---

# Will the minimum temperature be >44° on Mar 13, 2026?
**Event**: Lowest temperature in Denver on Mar 13, 2026?

**Outcome**: 45° or above

## Scout Assessment

**NEAR-DECIDED**  ·  **LOW RISK**

NEAR-DECIDED: YES — KXLOWTDEN-26MAR13-T44 is priced at 94¢ into a 06:00 UTC close, and the market only loses if the official Denver low slips below 45°F in the final hours. The remaining payout is 6¢ to resolution.

**Evidence**
- KDEN observations for Mar 13 have ranged from 54.0°F to 66.0°F so far, so the observed daily low still sits 10.0°F above the 44°F cutoff [weather.gov]
- Latest KDEN reading is 57.9°F at 20:53 MDT, leaving a 13.9°F gap above the failure threshold with roughly 2.1 hours left in the local day [weather.gov]
- The contract closes at 06:00 UTC (00:00 MDT), so the remaining exposure window is only about 2.2 hours from discovery [kalshi]
- YES is offered at 94¢ with a 3¢ spread, leaving 6¢ gross upside to resolution inside the target entry band [kalshi]

**Resolution**
National Weather Service / NOAA Denver International Airport observations, finalized through the official daily climate report for the station’s March 13 minimum temperature.

**Risks**
- A sharp late-evening temperature drop at KDEN below 45°F before local midnight would flip the market
- Final settlement waits for the official station-based climate print after the local day ends

**Sources**
- https://forecast.weather.gov/data/obhistory/KDEN.html
- https://www.weather.gov/wrh/climate?wfo=bou

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 94¢ ($0.94) |
| No Price | 9¢ ($0.09) |
| Closes | 2026-03-14 06:00 AM |

---

## Research Synthesis

**Flip Risk:** NO

**Event Status:**
[NWS CLI / KDEN obs] The determining event is still occurring normally: NWS Denver/Boulder published the March 13 daily climate report at 5:30 PM MDT with a preliminary Denver minimum of **51°F**, and KDEN hourly observations were still updating through **8:53 PM MDT**. I found no Denver weather-station outage or reporting disruption in targeted searches for `Denver airport ASOS outage March 13 2026`, `weather.gov Denver climate report unavailable March 13 2026`, and `KDEN weather observation outage March 13 2026`. citeturn5view0turn25view0

**Key Evidence For YES:**
- The official NWS climate report already lists the Mar. 13 minimum at **51°F**, with the low occurring at **3:14 AM local time**; that is **7°F above** the market threshold. [NWS CLI] citeturn5view0
- KDEN was still **57.9°F at 8:53 PM MDT**, so the temperature would need a sharp late drop to threaten the line. [KDEN obs] citeturn25view0
- The same NWS climate report says **"No significant weather was observed"** on March 13, which lowers disruption risk from precipitation/fog-type anomalies. [NWS CLI] citeturn5view0

**Key Evidence Against YES:**
- The bearish case is procedural, not meteorological: Kalshi settles weather markets on the **final NWS Daily Climate Report**, and during Daylight Saving Time the climate report uses **local standard time**, leaving a small post-midnight local window in which the Mar. 13 low can still change. [Kalshi Help] citeturn22view0
- Anecdotal community discussions show Kalshi temperature-market surprises from **rounding/source mismatches** and climate-report-versus-hourly-data confusion; I found no Denver-specific dispute for this date. [Community] citeturn27reddit16turn27reddit18

**Resolution Mechanics:**
Kalshi weather markets resolve from the **final NWS Daily Climate Report**, not app weather or raw exchange prices. Kalshi’s published temperature contract terms define **“greater than” strictly**; combined with this market’s label “45° or above,” that means **44°F is NO and 45°F is YES**. I did not locate the Denver-low PDF itself, so that strict-threshold point is an inference from Kalshi’s standard temperature-contract language plus the market label. citeturn22view0turn23search0

**Unconfirmed:**
- I did not find a public dataset showing how often **92–96¢ YES daily-temperature** contracts flip; absence of that evidence is not proof this setup is safe.
- I found no Denver-specific disruption alert for Mar. 13, but null search results are not confirmation of zero operational risk.

**Conclusion:**
The evidence found points toward YES holding: the official NWS preliminary low is already **51°F**, and late-evening KDEN observations remain well above the threshold. The remaining risk is mainly structural—the final NWS report and DST timing window—not a concrete sign that Denver is about to print **44°F or lower**. **Confidence: MEDIUM. Biggest uncertainty: DST/post-midnight climate-report window.**

**Sources:**
- `https://forecast.weather.gov/product.php?issuedby=DEN&product=CLI&site=NWS`
- `https://forecast.weather.gov/data/obhistory/KDEN.html`
- `https://help.kalshi.com/en/articles/13823837-weather-markets`
- `https://kalshi-public-docs.s3.amazonaws.com/contract_terms/NHIGH.pdf`
- `https://www.reddit.com/r/Kalshi/comments/1h2z3y8`
- `https://www.reddit.com/r/Kalshi/comments/12elwrd`