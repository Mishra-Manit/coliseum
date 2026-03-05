---
id: opp_ea36bd46
event_ticker: KXGDPYEAR-25
market_ticker: KXGDPYEAR-25-B2.3
yes_price: 0.96
no_price: 0.05
close_time: '2026-02-20T13:29:00Z'
discovered_at: '2026-02-19T22:52:30.510160Z'
research_completed_at: '2026-02-19T23:07:08.078073+00:00'
research_duration_seconds: 40
estimated_true_probability: 0.96
current_market_price: 0.96
expected_value: 0.0
edge: 0.0
suggested_position_pct: 0.05
edge_no: -0.009999999999999967
expected_value_no: -0.1999999999999993
suggested_position_pct_no: 0.0
recommendation_completed_at: '2026-02-19T23:07:13.487160+00:00'
action: null
strategy: sure_thing
status: recommended
---

# GDP growth in 2025?

**Outcome**: 2.1 to 2.5

## Scout Assessment

**Rationale**: CONFIRMED: The U.S. calendar-year 2025 GDP growth figure should be fully determined once BEA releases/has released Q4 2025 GDP (which completes the 2025 year) and Kalshi’s referenced GDP measure is therefore no longer subject to additional economic “prints.” Supporting Evidence: This is a backward-looking, publication-based market with a narrow remaining path to reversal once BEA data is published/locked; pricing at 96% YES implies the market expects the final published value to fall in the 2.1–2.5 band. Resolution Source: U.S. Bureau of Economic Analysis (BEA) GDP release for Q4 2025 / 2025 annual GDP accounting. Risk Checklist: clear resolution source ✓; structurally locked once BEA publication is final ✓; no formal appeals/reviews applicable ✓. Risk Level: LOW (data revision risk exists but is limited and rule-bound). Remaining Risks: Small risk from revisions/definition nuances depending on Kalshi’s contract specs. Sources: https://www.bea.gov/data/gdp/gross-domestic-product

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 96¢ ($0.96) |
| No Price | 5¢ ($0.05) |
| Closes | 2026-02-20 01:29 PM |

---

## Research Synthesis

### 1. Researched Questions
- What *exact* BEA statistic and publication does the market use to define “GDP growth in calendar year 2025,” and is it already published?
- Is the determining BEA release for “4th Quarter and Year 2025” final, or are additional BEA revisions scheduled that could move the annual 2025 growth rate across the 2.1–2.5 band?
- Were there any announced delays, shutdown effects, or methodological/annual-update changes that could materially affect the timing or definition used for settlement?
- Is there any non-BEA procedural risk (Kalshi rules/settlement mechanics) that could change resolution even if BEA data exists?

### 2. Resolution Status
- **Determining Event:** A BEA-published calendar-year 2025 real GDP growth number (likely “percent change from preceding year” for Real GDP in NIPA Table 1.1.1, per BEA’s standard annual real GDP growth framing).
- **Event Status:** **Not confirmed as fully “final/locked.”** BEA’s release calendar shows **“GDP (Advance Estimate), 4th Quarter and Year 2025” scheduled for January 29, 2026**. citeturn0search1  
  That strongly suggests the key “year 2025” print exists in an initial form by late January 2026, but it does **not** imply that no later revisions will occur.
- **Official Source:** The **U.S. Bureau of Economic Analysis (BEA)** is the authoritative publisher of the GDP estimate series and the release schedule for the relevant publication(s). citeturn0search1

**Timing note vs Scout rationale:** There is evidence that government operations/data reporting issues can delay GDP releases. A U.S. Treasury TBAC economic statement explicitly noted that, due to a government shutdown and delayed source data, **BEA had not yet released the advance estimate for 4Q25 as of January 30** (in that document’s framing). citeturn1search3turn2search2  
This creates a non-trivial timing/“what print exists today” ambiguity and argues against treating the market as already mechanically resolved unless you can see the specific BEA table value referenced in the contract.

### 3. Flip Risk Assessment
| Risk Factor | Status | Evidence |
|---|---|---|
| Pending appeals / review process | **N/A (economic statistic)** | BEA GDP is subject to scheduled revisions rather than “appeals.” BEA describes multiple annual vintages and later revisions (including annual updates and comprehensive revisions). citeturn0search4 |
| Scheduled events that could change settlement value | **YES (revisions/vintages remain possible)** | BEA documents that annual estimates go through multiple vintages (early annual; first/second/third annual), and are generally revised again at annual updates and comprehensive revisions (~every 5 years). citeturn0search4 |
| Official announcement already final | **Unclear** | BEA schedule shows the first “Year 2025” GDP print in the **Advance Estimate** on Jan 29, 2026, but “advance” by definition is not final. citeturn0search1 |
| Recent volatility / uncertainty signals | **Unclear from provided data** | You provided a 0.96 YES / 0.05 NO snapshot; I did not have access to a full price history to confirm whether there were late swings (a common uncertainty signal). (No on-platform chart accessible in this session.) |
| Definition / contract-spec mismatch risk | **YES (procedural)** | Kalshi’s help materials emphasize that each market has a rules summary and full rules that govern verification source and measured value; without the exact “full rules” text for KXGDPYEAR-25-B2.3, there is residual risk of a nuance (table/series, rounding, revision vintage cut) affecting settlement. citeturn4search1 |

### 4. Risk Classification
**OVERALL RISK: MEDIUM**

Primary driver: **revision/vintage risk + spec ambiguity.** Even if a “4Q and Year 2025” GDP release has occurred (or is scheduled), BEA itself describes a structured process where annual GDP estimates are revised in later vintages and annual updates, and only become broadly “sticky” after later annual revisions or comprehensive revisions. citeturn0search4  
Second driver: **timing ambiguity** from documented delays tied to government shutdown/source-data delays, which increases the chance that the market’s referenced “final” value (as defined by Kalshi rules) is not yet available or could be updated after the current close. citeturn1search3turn2search2  

What would downgrade to LOW risk: confirming (from the market’s **full rules**) (a) the exact BEA series/table/line and (b) the exact “as of” timestamp/vintage used for settlement (e.g., “advance estimate for 4Q & Year 2025” vs “third estimate” vs “annual update”)—and verifying that that specific publication has already been released and won’t be updated again before close.

### 5. Sources
1. https://www.bea.gov/index.php/news/schedule/next-year citeturn0search1
2. https://apps.bea.gov/scb/issues/2024/08-august/0824-revisions-to-gdp-gdi.htm citeturn0search4
3. https://home.treasury.gov/news/press-releases/sb0376 citeturn1search3turn2search2
4. https://help.kalshi.com/markets/markets-101/market-rules/rules-summary citeturn4search1

---

## Trade Evaluation

| Side | Edge | EV | Suggested Size |
|------|------|-----|----------------|
| **YES** | +0% | +0% | 5.0% |
| **NO** | -1% | -20% | 0.0% |

**Status**: Pending

### Reasoning

Risk level: MEDIUM (per research synthesis). Key residual flip risks are (1) BEA GDP revision/vintage risk—“advance estimate” is explicitly not final and later annual updates/comprehensive revisions can move the calendar-year growth figure across the 2.1–2.5 band; and (2) contract-spec ambiguity (exact BEA table/series, rounding, and which vintage/timestamp Kalshi uses) since full rules weren’t verified here. There is also timing ambiguity from documented release delays tied to shutdown/source-data issues. Outcome may still be likely, but not fully locked/irreversible by a clearly final publication, so sizing is capped at 5%.