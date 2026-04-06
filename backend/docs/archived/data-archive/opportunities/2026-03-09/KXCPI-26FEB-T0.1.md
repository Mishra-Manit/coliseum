---
id: opp_00d31eba
event_ticker: KXCPI-26FEB
market_ticker: KXCPI-26FEB-T0.1
yes_price: 0.94
no_price: 0.07
close_time: '2026-03-11T12:29:00Z'
discovered_at: '2026-03-09T19:43:35.336034Z'
status: recommended
research_completed_at: '2026-03-09T19:52:01.841127+00:00'
research_duration_seconds: 208
recommendation_completed_at: '2026-03-09T19:52:09.778473+00:00'
action: null
---

# Will CPI rise more than 0.1% in February 2026?

**Outcome**: Above 0.1%

## Scout Assessment

**Rationale**: Outcome Status -- STRONGLY FAVORED: the Cleveland Fed Inflation Nowcasting page updated 03/09/2026 shows February 2026 headline CPI at 0.25% month-over-month, so this contract’s >0.1% threshold currently has a 0.15-point cushion. Supporting Evidence -- the forecasted 0.25% print is above the strike, and the U.S. Bureau of Labor Statistics lists the official February CPI release for Wednesday, March 11, 2026 at 8:30 a.m. ET, giving this market a fixed near-term resolution event. Resolution Source -- the official determining authority is the U.S. Bureau of Labor Statistics CPI release. Risk Checklist -- passed required items (clear resolution source; no formal appeals or review path identified for a routine CPI publication) and optional items (strong position versus threshold; recent corroboration from a same-day nowcast update). Risk Level -- LOW; after excluding Tier 1 crypto and Tier 2 speaking markets and deprioritizing Tier 3 weather, this was the single lowest-risk available candidate in the provided 31-market universe. Remaining Risks -- a downside CPI surprise to 0.1% or lower or an unexpected publication delay, but no formal challenge risk is identified. Sources -- https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting ; https://www.bls.gov/schedule/news_release/cpi.htm

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 94¢ ($0.94) |
| No Price | 7¢ ($0.07) |
| Closes | 2026-03-11 12:29 PM |

---

## Research Synthesis

**Flip Risk: NO**

**Event Status:**  
The underlying resolution event still appears scheduled for **Wednesday, March 11, 2026 at 8:30 a.m. ET** on the BLS calendar, and the January CPI release itself repeated that February CPI is due then [1][2]. I found **no current cancellation/postponement notice**, but the BLS March calendar still carries a warning that release dates are subject to change because of government-services lapses, so schedule risk is not zero [1].

**Key Evidence For YES:**
- The Cleveland Fed’s March 9 nowcast shows **February 2026 headline CPI at +0.25% m/m**, well above the 0.1% threshold [3].
- Independent previews are also above the strike: **Wells Fargo estimates +0.21% m/m** for headline CPI, and CEPR says headline CPI is likely to rise **0.3%–0.4%** in February [4][5].
- Recent component data do not show shelter collapsing: in January, **shelter +0.2%, rent +0.2%, OER +0.2%**; that was slower than December’s **shelter +0.4%, rent +0.3%, OER +0.3%**, but still positive and still the largest contributor in January [2][6].

**Key Evidence Against YES / Risks Found:**
- This threshold is not “automatic”: **December 2025 CPI was 0.0% m/m**, so this market type can resolve NO when headline inflation goes flat [6].
- The strongest bearish case I found is **rounding / contract-spec risk**: a mirror of a similar Kalshi PCE threshold market says settlement uses the **single-decimal month-over-month** figure. If CPI markets use the same mechanic, a raw print only marginally above 0.1 could still round to **0.1** and fail; I could not verify the exact CPI rule text from Kalshi’s own market page [7].
- Searches for “CPI delayed/cancelled/postponed March 11 2026” returned **no live delay notice**, but absence of a notice is not proof against an operational disruption [1][8].

**Resolution Mechanics:**  
Search results confirm this is the **CPI month-over-month** market family tied to the **BLS February 2026 CPI reading** [9][10]. However, I could not retrieve the exact Kalshi resolution text for **KXCPI-26FEB-T0.1** from the public market page. The closest analogous rule I found for a similar Kalshi macro market states settlement is based on the **published single-decimal monthly rate** [7], which creates a real but unverified ambiguity here.

**Unconfirmed:**
- Exact official Kalshi rule text for this specific ticker, including whether settlement uses the headline CPI-U monthly change and how rounding is handled.
- Whether the BLS calendar warning about government-service disruptions is purely boilerplate or still operationally relevant this week.
- Broader historical YES-hit-rate for **92–96¢** CPI threshold markets; I found one prior same-threshold example resolving YES, but not a robust base-rate dataset [10].

**Conclusion:**  
The evidence I found points to **YES likely holding**: every substantive February preview I located is above 0.1%, and the release is still on the calendar in two days [1][3][4][5]. My confidence is **MEDIUM** rather than high because the biggest remaining uncertainty is **resolution mechanics**—specifically whether Kalshi uses the published single-decimal CPI figure and, if so, how close-to-threshold values are treated.

Sources:
1. `https://www.bls.gov/schedule/2026/03_sched_list.htm`
2. `https://www.bls.gov/news.release/archives/cpi_02132026.htm`
3. `https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting`
4. `https://externalcontent.blob.core.windows.net/pdfs/WellsFargoCommentary20260306.pdf`
5. `https://cepr.net/publications/february-2026-cpi-preview/`
6. `https://www.bls.gov/news.release/archives/cpi_01132026.htm`
7. `https://www.quiverquant.com/news/Markets%2Bbet%2Bon%2Bwhether%2Bthe%2Brate%2Bof%2Bcore%2BPCE%2Binflation%2Bwill%2Bbe%2Babove%2B0.2%25%2Bin%2BJuly%2B2025`
8. `https://apnews.com/article/471e55ba4c3247051739ee1b50b2857a`
9. `https://kalshi.com/markets/kxeconstatcpi/month-over-month-inflation/kxeconstatcpi-26feb`
10. `https://octagonai.co/markets/economics/inflation/cpi-in-feb-2026/`