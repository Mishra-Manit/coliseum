---
id: opp_2035ba6f
event_ticker: KXAAAGASW-26MAR23
event_title: US gas prices this week
market_ticker: KXAAAGASW-26MAR23-3.980
yes_price: 0.05
no_price: 0.96
close_time: '2026-03-23T03:59:00Z'
rationale: 'STRONGLY FAVORED: BUY NO — the market prices NO at 96¢ against a 5¢ YES,
  and AAA’s current national average remains below the $3.980 strike. With a 1¢ spread
  and very high volume, this is the cleanest low-reversal setup in the scanned universe.'
discovered_at: '2026-03-22T22:50:36.596350Z'
status: recommended
outcome_status: STRONGLY FAVORED
risk_level: LOW
resolution_source: AAA Fuel Prices’ U.S. regular-gas national average for March 23,
  2026, as published on gasprices.aaa.com; the market resolves mechanically against
  that posted figure.
evidence_bullets:
- AAA’s U.S. regular-gas average is **$3.942** on **3/22/26**, still **3.8¢ below**
  the $3.980 strike [aaa.com]
- AAA shows **$3.925 yesterday** and **$3.699 a week ago**, so the latest one-day
  move was only **+1.7¢** and the strike still needs another **+3.8¢** overnight [aaa.com]
- AAA’s March 19 update listed the national average at **$3.884** and WTI at **$96.32/bbl**,
  confirming rising pump prices that are still below the strike [aaa.com]
- Kalshi market data shows a **96¢ NO ask**, **1¢ spread**, **177,721** volume, and
  **104,901** open interest [kalshi.com]
remaining_risks:
- AAA regular-gas prices are still climbing day to day
- A one-day move greater than 3.8¢ would flip the market
scout_sources:
- https://kalshi.com/markets/kxaaagasw/us-gas-price-up/kxaaagasw-26mar23
- https://gasprices.aaa.com/?Country=US
- https://gasprices.aaa.com/as-spring-equinox-arrives-gas-prices-continue-to-climb/
research_completed_at: '2026-03-22T22:58:05.134703+00:00'
research_duration_seconds: 173
recommendation_completed_at: '2026-03-22T22:58:08.107294+00:00'
action: null
---

# Will average gas prices be above $3.980?
**Event**: US gas prices this week

**Outcome**: Above $3.980

## Scout Assessment

**STRONGLY FAVORED**  ·  **LOW RISK**

STRONGLY FAVORED: BUY NO — the market prices NO at 96¢ against a 5¢ YES, and AAA’s current national average remains below the $3.980 strike. With a 1¢ spread and very high volume, this is the cleanest low-reversal setup in the scanned universe.

**Evidence**
- AAA’s U.S. regular-gas average is **$3.942** on **3/22/26**, still **3.8¢ below** the $3.980 strike [aaa.com]
- AAA shows **$3.925 yesterday** and **$3.699 a week ago**, so the latest one-day move was only **+1.7¢** and the strike still needs another **+3.8¢** overnight [aaa.com]
- AAA’s March 19 update listed the national average at **$3.884** and WTI at **$96.32/bbl**, confirming rising pump prices that are still below the strike [aaa.com]
- Kalshi market data shows a **96¢ NO ask**, **1¢ spread**, **177,721** volume, and **104,901** open interest [kalshi.com]

**Resolution**
AAA Fuel Prices’ U.S. regular-gas national average for March 23, 2026, as published on gasprices.aaa.com; the market resolves mechanically against that posted figure.

**Risks**
- AAA regular-gas prices are still climbing day to day
- A one-day move greater than 3.8¢ would flip the market

**Sources**
- https://kalshi.com/markets/kxaaagasw/us-gas-price-up/kxaaagasw-26mar23
- https://gasprices.aaa.com/?Country=US
- https://gasprices.aaa.com/as-spring-equinox-arrives-gas-prices-continue-to-climb/

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 5¢ ($0.05) |
| No Price | 96¢ ($0.96) |
| Closes | 2026-03-23 03:59 AM |

---

## Research Synthesis

**Flip Risk:** YES

**Event Status:**
AAA is still publishing the daily U.S. regular-gas average, with **$3.942** posted for **March 22, 2026**, and I found no sign that the source publication has been delayed or cancelled. The weekly contract structure points to a **March 23, 2026** observation date rather than a seven-day arithmetic average. [AAA 3/22/26] [Robinhood gas-week page]

**Key Evidence For YES:**
- AAA’s national regular average is **$3.942** as of **3/22/26**, only **3.8¢** below the **$3.980** strike. [AAA 3/22/26]
- EIA’s Daily Prices page shows the AAA U.S. average at **$3.91 on 3/19/26**; that is a rise of about **3.2¢ in three days**, so another normal up-leg would threaten the strike immediately. [EIA Daily Prices 3/20]
- EIA’s March STEO says higher crude prices are contributing to gasoline prices about **60¢/gal higher in March** and roughly **70¢/gal higher in Q2** versus its prior outlook. [EIA STEO 3/10]
- Searches for near-term analyst views returned GasBuddy commentary that there is roughly an **80%** chance of **$4 gas within the next month or sooner**, which is not tomorrow-specific but does confirm upward pressure remains live. [GasBuddy/AOL roundup]

**Key Evidence Against YES:**
- Kalshi’s contract terms for **AAAGAS** use **AAA** as the source and **regular gas** as the underlying, so the main source-mismatch risk in the prompt (**AAA vs. EIA all-grades/regular**) does **not** apply here. [Kalshi AAAGAS rules]
- The latest EIA WPSR shows refinery utilization up to **91.4%** last week, while EIA Daily Prices show **WTI at $96.11** on **3/19/26** and wholesale gasoline down about **2.8%–2.9%** that day, which argues for at least some short-term stabilization. [EIA WPSR 3/18] [EIA Daily Prices 3/20]
- Kalshi’s rule says if no source data is available on the expiration date, the market resolves using the **last available day’s data**; today’s last posted AAA print is still below strike at **$3.942**. [Kalshi AAAGAS rules]
- None found — searched for **"Kalshi AAAGAS dispute gas prices resolved incorrectly"** and did not find a gas-specific settlement controversy.

**Resolution Mechanics:**
This market type resolves off the value documented by **AAA** for U.S. **regular gas** on the specified date; it is not an EIA weekly inventory or all-grades contract. The rule text is mechanically clean, but **Kalshi’s Markets Team** remains the settlement authority, and I could not confirm the exact expiration timestamp for this specific strike beyond the series-level window of **10:15 AM, 11:00 AM, or 3:00 PM ET**. 

**Unconfirmed:**
- Exact expiration timestamp for **KXAAAGASW-26MAR23-3.980**
- Whether AAA’s **3/23/26** print is posted before that timestamp

**Conclusion:**
The structure is cleaner than many Kalshi markets, but the price cushion is not. A **96¢ NO** is only **3.8¢** away from being wrong on the underlying source, and recent AAA moves have been large enough that a one-day breach is plausible. Confidence: **MEDIUM**. Biggest uncertainty: Monday AAA update timing versus one-day pump-price momentum.

**Sources:**
- https://gasprices.aaa.com/aaa-gas-prices/
- https://www.eia.gov/todayinenergy/prices.php
- https://www.eia.gov/petroleum/supply/weekly/pdf/wpsrall.pdf
- https://www.eia.gov/outlooks/steo/report/petro_prod.php
- https://kalshi-public-docs.s3.amazonaws.com/contract_terms/AAAGAS.pdf
- https://robinhood.com/us/en/prediction-markets/economics/events/us-gas-prices-this-week-mar-09-2026/
- https://www.aol.com/finance/gas-prices-could-hit-4-114410662.html