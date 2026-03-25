---
id: opp_282d41b4
event_ticker: KXSOLD-26MAR2517
event_title: SOL price on Mar 25, 2026 at 5pm EDT?
market_ticker: KXSOLD-26MAR2517-T82.9999
yes_price: 0.96
no_price: 0.05
close_time: '2026-03-25T21:00:00Z'
rationale: 'NEAR-DECIDED: YES is offered at 96¢ with a 1¢ spread, 3,225 contracts
  of volume, and 3,215 open interest, making it the strongest priced candidate in
  the scan. At a 96¢ entry, only 4¢ of payout remains before the Mar 25 close.'
discovered_at: '2026-03-24T23:34:39.642024Z'
status: recommended
outcome_status: NEAR-DECIDED
risk_level: LOW
resolution_source: Kalshi resolves this crypto contract using the average of the last
  60 seconds of the relevant CF Benchmarks Real-Time Index at 5:00 p.m. EDT on March
  25, 2026.
evidence_bullets:
- Kraken lists SOL at **$90.40**, which is **$7.40** above the **$83** strike [kraken.com]
- Kraken shows a **24H low of $88.51**, still **$5.51** above the strike [kraken.com]
- Kalshi’s SOL market hub lists the **'$83 to 83.9999'** Mar 25 range and the **'tomorrow
  at 5pm EDT'** SOL market family, matching this contract set [kalshi.com]
- Kalshi states crypto contracts settle from a **60-second** average of the relevant
  **CFB RTI** at expiration [help.kalshi.com]
remaining_risks:
- A sharp crypto selloff before 5:00 p.m. EDT on March 25, 2026 could still take SOL
  below $83.
- Settlement is based on CF Benchmarks' 60-second RTI average rather than any single
  exchange print.
scout_sources:
- https://www.kraken.com/prices/solana
- https://help.kalshi.com/markets/popular-markets/crypto-markets
- https://kalshi.com/category/crypto/sol
research_completed_at: '2026-03-24T23:39:44.252230+00:00'
research_duration_seconds: 200
recommendation_completed_at: '2026-03-24T23:39:46.699423+00:00'
action: null
---

# SOL price  on Mar 25, 2026?
**Event**: SOL price on Mar 25, 2026 at 5pm EDT?

**Outcome**: $83 or above

## Scout Assessment

**NEAR-DECIDED**  ·  **LOW RISK**

NEAR-DECIDED: YES is offered at 96¢ with a 1¢ spread, 3,225 contracts of volume, and 3,215 open interest, making it the strongest priced candidate in the scan. At a 96¢ entry, only 4¢ of payout remains before the Mar 25 close.

**Evidence**
- Kraken lists SOL at **$90.40**, which is **$7.40** above the **$83** strike [kraken.com]
- Kraken shows a **24H low of $88.51**, still **$5.51** above the strike [kraken.com]
- Kalshi’s SOL market hub lists the **'$83 to 83.9999'** Mar 25 range and the **'tomorrow at 5pm EDT'** SOL market family, matching this contract set [kalshi.com]
- Kalshi states crypto contracts settle from a **60-second** average of the relevant **CFB RTI** at expiration [help.kalshi.com]

**Resolution**
Kalshi resolves this crypto contract using the average of the last 60 seconds of the relevant CF Benchmarks Real-Time Index at 5:00 p.m. EDT on March 25, 2026.

**Risks**
- A sharp crypto selloff before 5:00 p.m. EDT on March 25, 2026 could still take SOL below $83.
- Settlement is based on CF Benchmarks' 60-second RTI average rather than any single exchange print.

**Sources**
- https://www.kraken.com/prices/solana
- https://help.kalshi.com/markets/popular-markets/crypto-markets
- https://kalshi.com/category/crypto/sol

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 96¢ ($0.96) |
| No Price | 5¢ ($0.05) |
| Closes | 2026-03-25 09:00 PM |

---

## Research Synthesis

**Flip Risk:** UNCERTAIN

**Event Status:**
The determining event has **not occurred yet**; this market resolves at **5:00 PM EDT on March 25, 2026** based on a Solana price print, not on a cancellable speech/game. Both **Solana** and **CF Benchmarks** status pages were **operational**, and I found no public evidence of a March 25 disruption that would obviously block the print. [CFTC SOL filing] [Solana Status] [CF Benchmarks Status]

**Key Evidence For YES:**
- Current market data showed SOL around **$90.93**, leaving roughly an **8.7%** cushion above the **$82.9999** YES cutoff one day before expiry. [Web finance]
- Solana’s official status page showed **100.0% uptime** across tracked components over the prior 90 days and no recent incidents in March. [Solana Status]
- Solana Foundation’s March 5 ecosystem report said SOL-denominated TVL crossed **80M SOL** at an all-time high, February transactions reached **3.4B**, and U.S.-based Solana ETFs had taken in **$900M+** cumulatively. [Solana Ecosystem Report]

**Key Evidence Against YES:**
- The same **$83 or above** strike recently resolved **NO** in closed Mar. 8 SOL markets at **9 PM EDT** and **10 PM EDT**, proving this threshold is not remote in current volatility. [Coinbase Mar. 8 9PM] [Coinbase Mar. 8 10PM]
- CF Benchmarks’ March 9 weekly note said Solana fell **6.5%** in the prior week amid geopolitical strain; another sharp risk-off move could still push SOL through the strike. [CF Benchmarks Weekly]
- I found no published base-rate dataset showing that **92-96¢** Kalshi crypto-threshold contracts resolve YES at near-certainty; searched historical Coinbase/Kalshi SOL pages and found mixed YES/NO outcomes around this same level. [Coinbase historical SOL pages]

**Resolution Mechanics:**
YES triggers only if the simple average of the **60 seconds** of **CF Benchmarks’ SOLUSD_RTI** immediately before **5:00 PM EDT** is **above $82.9999**. That makes the resolution source relatively objective, but **Kalshi** still controls settlement review, and if no underlying is available by **10:00 AM ET one week later**, the rules fall back to the closest prior underlying. [CFTC SOL filing] [Coinbase Mar. 9 rules]

**Unconfirmed:**
- I did not find the exact public rules page for ticker **KXSOLD-26MAR2517-T82.9999**; wording is inferred from Kalshi’s self-certified SOL contract terms and matching historical SOL market pages.
- No robust public study of high-priced Kalshi crypto market resolution rates.

**Conclusion:**
This is a cleaner market than mentions or discretionary resolutions: the source is objective, both the chain and benchmark operator appear **on schedule**, and recent fundamentals are supportive. But a **96¢** price still looks aggressive for a one-day crypto threshold only **~8.7%** below spot, especially because the same **$83** line flipped to **NO** in recent March markets. Confidence: **MEDIUM**. Biggest uncertainty: overnight crypto volatility.

**Sources:**
- https://www.cftc.gov/filings/ptc/ptc07102525857.pdf
- https://status.solana.com/
- https://status.cfbenchmarks.com/
- https://solana.com/news/state-of-solana-february-2026
- https://www.coinbase.com/en-fr/predictions/event/KXSOLD-26MAR0821
- https://www.coinbase.com/en-fr/predictions/event/KXSOLD-26MAR0822
- https://www.coinbase.com/predictions/event/KXSOLD-26MAR0917
- https://www.cfbenchmarks.com/blog/weekly-index-highlights-february-23-2026-2