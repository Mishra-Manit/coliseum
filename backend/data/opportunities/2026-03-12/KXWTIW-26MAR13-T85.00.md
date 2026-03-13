---
id: opp_8ec6503c
event_ticker: KXWTIW-26MAR13
event_title: WTI oil price on Mar 13, 2026?
market_ticker: KXWTIW-26MAR13-T85.00
yes_price: 0.08
no_price: 0.93
close_time: '2026-03-13T18:30:00Z'
rationale: 'STRONGLY FAVORED: NO — the market only loses if front-month WTI settles
  below $85.00 on March 13, and Kalshi still prices NO at 93¢ with a 1¢ spread. The
  combination of deep liquidity and an objective exchange-based settlement makes this
  the cleanest remaining non-crypto, non-speaking setup in the scan.'
discovered_at: '2026-03-12T23:01:39.720688Z'
status: recommended
outcome_status: STRONGLY FAVORED
risk_level: LOW
resolution_source: ICE WTI futures cash-settle to the official exchange settlement
  reference, so Kalshi resolution is mechanical and objective.
evidence_bullets:
- NO ask 93¢ vs YES ask 8¢, with a 1¢ spread in Kalshi market data [kalshi]
- Volume is 143,099 and open interest is 61,638, the deepest liquidity in this 25-market
  scan [kalshi]
- NYMEX April WTI settled at $87.25 on March 11, leaving a $2.25 cushion above the
  $85.00 cutoff [china.org.cn]
remaining_risks:
- Crude remains headline-sensitive and can move several dollars on war or reserve-release
  news
- A sharp risk-off move before the March 13 settlement window could still push WTI
  under $85
scout_sources:
- https://www.ice.com/products/213/wti-crude-
- https://www.cmegroup.com/trading/files/WTI-Fact-Card.pdf
- https://www.china.org.cn/world/Off_the_Wire/2026-03/12/content_118377799.shtml
research_completed_at: '2026-03-12T23:06:52.216781+00:00'
research_duration_seconds: 202
recommendation_completed_at: '2026-03-12T23:06:58.947546+00:00'
action: null
---

# Will the WTI front-month settle oil price be <85.00 on Mar 13, 2026?
**Event**: WTI oil price on Mar 13, 2026?

**Outcome**: $84.99 or below

## Scout Assessment

**STRONGLY FAVORED**  ·  **LOW RISK**

STRONGLY FAVORED: NO — the market only loses if front-month WTI settles below $85.00 on March 13, and Kalshi still prices NO at 93¢ with a 1¢ spread. The combination of deep liquidity and an objective exchange-based settlement makes this the cleanest remaining non-crypto, non-speaking setup in the scan.

**Evidence**
- NO ask 93¢ vs YES ask 8¢, with a 1¢ spread in Kalshi market data [kalshi]
- Volume is 143,099 and open interest is 61,638, the deepest liquidity in this 25-market scan [kalshi]
- NYMEX April WTI settled at $87.25 on March 11, leaving a $2.25 cushion above the $85.00 cutoff [china.org.cn]

**Resolution**
ICE WTI futures cash-settle to the official exchange settlement reference, so Kalshi resolution is mechanical and objective.

**Risks**
- Crude remains headline-sensitive and can move several dollars on war or reserve-release news
- A sharp risk-off move before the March 13 settlement window could still push WTI under $85

**Sources**
- https://www.ice.com/products/213/wti-crude-
- https://www.cmegroup.com/trading/files/WTI-Fact-Card.pdf
- https://www.china.org.cn/world/Off_the_Wire/2026-03/12/content_118377799.shtml

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 8¢ ($0.08) |
| No Price | 93¢ ($0.93) |
| Closes | 2026-03-13 06:30 PM |

---

## Research Synthesis

**Flip Risk:** NO

**Event Status:**
The event is still on schedule. ICE shows the relevant Apr26 WTI contract remains active until March 19, 2026, so March 13 is not a rollover edge case; CME holiday notices also show no March 13 exchange closure. Kalshi’s WTIOIL rules would therefore use the normal front-month contract for this date. citeturn14view0turn12view0turn1search3

**Key Evidence For YES:**
- The bearish case exists: EIA reported a 3.8 million-barrel U.S. crude inventory build for the week ended March 6, and the IEA announced a record 400 million-barrel emergency release on March 11. Both are pressure points that could drag WTI lower if war premium fades quickly. citeturn6view0turn21search0
- Before Thursday’s rebound, reserve-release headlines briefly knocked WTI near $84 on March 11 in market coverage, showing the `<85` strike is not mathematically impossible if de-escalation headlines hit before Friday settlement. citeturn20search0
- OPEC+ had been leaning toward resuming output increases from April, another medium-term bearish input, though not a same-day catalyst by itself. citeturn3search5

**Key Evidence Against YES:**
- Benchmark U.S. crude settled at $95.73 on Thursday, March 12, which is $10.73 above the $85 threshold one session before resolution. citeturn19view0
- CME’s March 11 bulletin had Apr26 NYMEX WTI settling at $87.25 even before Thursday’s latest surge, already above the line. citeturn2view0
- EIA said Brent settled at $94 on March 9, forecast Brent to stay above $95 for the next two months, and tied the strength to reduced Hormuz flows and shut-in Middle East output. IEA separately said Hormuz export volumes are below 10% of pre-conflict levels. citeturn22view0turn21search0
- Searches for fresh March 12-13 U.S. weather outages found no new storm-driven event likely to force WTI down; the live driver is still geopolitical supply risk, including attacks on Gulf energy infrastructure. citeturn23news12turn23news14

**Resolution Mechanics:**
This is cleaner than a speech market but not exactly what the scout described: Kalshi’s binding WTIOIL filing says the source agency is ICE, not CME, and the contract uses the ICE front-month WTI settlement. ICE in turn defines its settlement as the NYMEX penultimate settlement price for the relevant month. Because Apr26 last trades March 19, the March 13 market should still reference Apr26 rather than rolling to May26. citeturn12view0turn24view0turn14view0

**Unconfirmed:**
- No published dataset was found showing how often 92–96¢ oil strikes specifically hold to resolution; reliability here is inferred from objective-source mechanics, not proven by a base-rate study. A Reddit complaint about a different WTI min/max market suggests operational risk is low but not zero. citeturn17reddit21turn11search0

**Conclusion:**
Based on current price distance, official energy-agency commentary, and ongoing Hormuz disruption, the immediate flip risk from expensive NO to YES looks low. The main path to YES is a sharp overnight de-escalation or a reserve-release shock that drags Friday’s official settlement below $85, but the evidence found points the other way. Portfolio note: this opportunity would increase same-event concentration because you already hold KXWTIW-26MAR13-B91.5. Confidence: MEDIUM. Biggest uncertainty: overnight geopolitical headline volatility.

**Sources:**
- `https://www.ice.com/products/213/WTI-Crude-Futures/expiry`
- `https://kalshi-public-docs.s3.amazonaws.com/regulatory/notices/COMBINED%20WTIOIL%20Amendment%20for%20posting%20with%20redline.pdf`
- `https://apnews.com/article/oil-stocks-markets-iran-crude-trump-45f78a8cfe9a5c7e1a2279150a2f90f1`
- `https://www.eia.gov/petroleum/supply/weekly/`
- `https://www.iea.org/news/iea-member-countries-to-carry-out-largest-ever-oil-stock-release-amid-market-disruptions-from-middle-east-conflict`
- `https://www.eia.gov/pressroom/releases/press584.php`