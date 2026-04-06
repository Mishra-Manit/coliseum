---
id: opp_87e066c7
event_ticker: KXCPI-26FEB
market_ticker: KXCPI-26FEB-T0.0
yes_price: 0.96
no_price: 0.05
close_time: '2026-03-11T12:29:00Z'
discovered_at: '2026-03-09T16:08:27.819299Z'
status: recommended
research_completed_at: '2026-03-09T16:14:41.683525+00:00'
research_duration_seconds: 196
recommendation_completed_at: '2026-03-09T16:14:46.564692+00:00'
action: null
---

# Will CPI rise more than 0.0% in February 2026?

**Outcome**: Above 0.0%

## Scout Assessment

**Rationale**: STRONGLY FAVORED: BUY_YES on "Will CPI rise more than 0.0% in February 2026?" because the February CPI release is scheduled for Wednesday, March 11, 2026 at 8:30 a.m. ET and recent economist previews point to a positive monthly print, with Bloomberg consensus at 0.2% m/m and Wells Fargo at 0.21% m/m, leaving a 0.0% or negative print as the residual tail outcome. Supporting Evidence: this market only requires any positive monthly increase after rounding, and both the consensus and Wells Fargo estimate sit about 0.2 percentage points above the strike; Resolution Source: the U.S. Bureau of Labor Statistics scheduled CPI release is the authoritative publication that determines settlement. Risk Checklist: passed clear resolution source, no formal appeals or official challenge path, recent corroboration within 72 hours, and stable inputs because February price data are already fixed before publication; Risk Level: LOW, and this was selected as the single lowest-risk available candidate after excluding Tier 1 crypto and Tier 2 speaking markets and ranking the remaining eligible markets by reversal risk. Remaining Risks: a surprise 0.0% or negative rounded headline print or an unexpected publication delay, but no formal challenge process is identified; Sources: https://www.bls.gov/schedule/2026/03_sched.htm https://www.bls.gov/schedule/2026/ https://externalcontent.blob.core.windows.net/pdfs/WellsFargoCommentary20260306.pdf https://externalcontent.blob.core.windows.net/pdfs/pdfs/WellsFargo06032026.pdf

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 96¢ ($0.96) |
| No Price | 5¢ ($0.05) |
| Closes | 2026-03-11 12:29 PM |

---

## Research Synthesis

**Flip Risk: NO**

**Event Status:**
The underlying event still appears to be proceeding normally. BLS still lists the **Consumer Price Index for February 2026** for **Wednesday, March 11, 2026 at 8:30 a.m. ET**, and the broader federal funding risk looks reduced because AP reported on **February 3, 2026** that the spending bill signed by President Trump funded **11 appropriations bills through September**, leaving Homeland Security as the main separate fight rather than Labor/BLS.

**Key Evidence For YES:**
- The Cleveland Fed’s **March 9, 2026** nowcast puts **February 2026 CPI at +0.25% m/m** and **March 2026 at +0.22% m/m**. A +0.25% print would clear a **0.0%** threshold comfortably after one-decimal rounding.
- BLS’s latest actual release showed **January 2026 CPI at +0.2% m/m**, with **shelter +0.2%** and shelter identified as the **largest factor** in the monthly increase.
- Zillow’s March 5 shelter forecast still expects **February 2026 OER +0.18% m/m** and **rent of primary residence +0.19% m/m**. Shelter is slowing, but the forecast is still positive rather than flat or negative.

**Key Evidence Against YES / Risks Found:**
- This is **not** a generic “inflation happened” market. The mirrored rules page says the contract resolves on the **single-decimal BLS monthly CPI value** for February 2026. That creates **rounding risk**: a small positive underlying print could still round to **0.0%** and resolve NO.
- Monthly CPI can miss these low strikes. CNBC’s report on the **March 2025 CPI** says headline CPI was **-0.1% m/m**, showing that “Above 0.0%” is usually favored but not automatic.
- Operationally, AP reported on **February 2, 2026** that a partial shutdown caused the Labor Department to delay the January jobs report. I found no evidence this risk is active for March 11, but it is a real historical failure mode.

**Resolution Mechanics:**
The best market-specific rule I found is the Solflare mirror of Kalshi’s event page: **YES if CPI increases by more than 0.0% (single-decimal) in February 2026**; market closes **8:29 a.m. ET on March 11, 2026**; if a federal shutdown affects source reliability, expiration extends to the earlier of the delayed release or six months after shutdown end. The biggest ambiguity is the dependence on the **published one-decimal value**, not an unrounded internal number.

**Unconfirmed:**
- I could not retrieve Kalshi’s own `rules_primary` field for this exact ticker directly.
- I did not find a public Reuters/Bloomberg consensus page for this exact market.
- I found no official BLS warning of a special February 2026 methodology break beyond the normal annual seasonal-factor revision; absence of such a warning is **not proof** that no surprise is possible.

**Conclusion:**
The evidence supports **low flip risk**: the release remains scheduled, BLS’s source agency appears funded, the Cleveland Fed nowcast is decisively positive, and key shelter inputs are still positive. Confidence is **MEDIUM** rather than high because the contract resolves on a **one-decimal rounded monthly print**, so the single biggest remaining uncertainty is **rounding/measurement risk around a very low strike**, not macro direction.

Sources:
1. `https://www.bls.gov/schedule/2026/03_sched.htm`
2. `https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting`
3. `https://www.bls.gov/news.release/archives/cpi_02132026.htm`
4. `https://www.zillow.com/research/cpi-forecast-2026-feb-36139/`
5. `https://www.solflare.com/prediction/economics/event/KXCPI-26FEB/`
6. `https://apnews.com/article/471e55ba4c3247051739ee1b50b2857a`
7. `https://apnews.com/article/0f327d71037f89afb818ea78b1162010`
8. `https://www.bls.gov/cpi/seasonal-adjustment/`
9. `https://www.bls.gov/opub/ted/2026/consumer-price-index-2025-in-review.htm`
10. `https://www.cnbc.com/2025/04/10/inflation-rate-eases-to-2point4percent-in-march-lower-than-expected.html`