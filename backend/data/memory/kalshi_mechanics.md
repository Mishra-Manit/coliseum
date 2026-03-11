# Kalshi Platform Mechanics

Operational reference for the Coliseum trading system. Current as of March 2026.

---

## Fee Structure

Kalshi uses a probability-weighted fee model. Both makers (limit orders) and takers (quick orders)
pay the same formula as of July 2025.

**Formula:** `fee = 0.07 × P × (1 - P)` per contract, where P is the fill price as a decimal.

**Fee and net profit at our 92–96¢ target range (YES held to resolution):**

| Entry Price | Fee per Contract | Net Profit per Contract | Return on Capital |
|-------------|-----------------|------------------------|-------------------|
| 92¢         | 0.515¢          | 7.485¢                 | 8.1%              |
| 93¢         | 0.456¢          | 6.544¢                 | 7.0%              |
| 94¢         | 0.395¢          | 5.605¢                 | 6.0%              |
| 95¢         | 0.333¢          | 4.667¢                 | 4.9%              |
| 96¢         | 0.269¢          | 3.731¢                 | 3.9%              |

Net profit = `(1.00 - entry_price) - fee`

**Key operational facts:**
- Fees at 92–96¢ are minimal (0.27–0.52¢ per contract). Fee drag is not the risk — a flip is.
- Maximum fee is 1.75¢ per contract at 50¢ (the midpoint).
- S&P 500 and Nasdaq-100 markets use a discounted formula: `0.035 × P × (1 - P)` (50% off).
- Fees are only charged on the portion of an order that executes. Resting limit orders incur
  zero fees until filled.

---

## Order Book & Execution

**Binary contract structure:** YES and NO are two sides of the same contract. A YES at price P
implies NO at price (1 - P). They do not sum to exactly 100¢ — the gap is the spread.

**Order book display:** Kalshi's UI shows only the BID side. The ASK you pay for YES is derived
from NO holders bidding on the other side.

Example: If the best NO bid is 4¢, the best YES ask is 96¢ (100 - 4 = 96). The 1¢ spread between
a YES bid of 95¢ and a YES ask of 96¢ represents the market's liquidity cost.

**Order types:**

| Type | Execution | Fee Timing | Best Used When |
|------|-----------|------------|----------------|
| Limit order (maker) | Posts to book; fills when matched | Only on execution | Standard entry; allows price control |
| Quick order (taker) | Immediate at best available price | Immediately on fill | Under 30 min to close; fill is critical |

**Partial fills:** A limit order that partially fills leaves the remainder resting on the book.
Fees only apply to the filled portion.

**Cancellation:** Unfilled limit orders can be cancelled at any time before they execute or the
market closes. All resting orders expire automatically at market closure.

---

## Collateral & Capital Model

Kalshi is **fully cash-collateralized.** There is no margin, no leverage, and no borrowing.

- Buying YES at 95¢ → 95¢ locked as collateral per contract. Max loss: 95¢. Max gain: 5¢.
- Buying NO at 5¢ → 5¢ locked per contract. Max loss: 5¢. Max gain: 95¢.

Capital tied to open positions is **unavailable for new trades** until settlement completes.
Factor this into position sizing — deployed capital is illiquid for 30 minutes to 48 hours
depending on market type.

**No margin calls. No forced liquidations. Maximum loss is capped at what you deployed.**

Position sizing implication: at 95¢ YES with a $25k position limit, maximum contracts = 26,315.
At 93¢ YES, maximum contracts = 26,881.

---

## Position Limits

| Market Type | Per-Market Limit |
|-------------|-----------------|
| Standard markets | $25,000 |
| Large/high-volume markets | $7M–$50M |
| Presidential election contracts | $7M (retail); up to $100M (ECP) |

Limit is measured in collateral at risk, not notional payout. Standard limit of $25k at 95¢ YES =
26,315 contracts; at 5¢ NO (same market, other side) = 500,000 contracts.

---

## Settlement & Resolution

**Timeline by market category:**

| Category | Resolution Method | Typical Time After Event |
|----------|------------------|--------------------------|
| Sports (game results) | Automated (official score feeds) | 30–60 minutes |
| Economic data (BLS, BEA, Fed) | Automated (official government releases) | 1–3 hours post-publication |
| Political / congressional | Manual review by Markets Team | 12–48 hours |
| Mention / speech markets | Manual review of broadcast transcripts | 2–8 hours post-broadcast |
| Entertainment / awards | Manual review | Up to 48 hours |

**Resolution authority:** Kalshi's internal Markets Team makes final determinations using
predefined data sources. Traders may file a "Request to Settle" — this is advisory only and
does not bind Kalshi's decision.

**Outcome Review Committee:** A board subcommittee handles disputed or ambiguous outcomes. Its
decisions are **final.** There is no external arbitration, no independent ombudsman, and no formal
appeal mechanism for traders.

**Funds release:** Winning contracts pay $1.00 per contract; losing contracts pay $0.00.
Settlement funds typically appear in accounts 1–3 hours after resolution is confirmed.

---

## Critical Rules

### Rule 6.3(c) — Unresolvable Outcome

If Kalshi deems an outcome unresolvable (missing data source, ambiguous event, contract spec
ambiguity, or disputed determination), the market settles at the **last traded price before the
ambiguity arose** — NOT voided, NOT forced to $0 or $1.

**Example:** Cardi B Super Bowl halftime market was ruled "ambiguous." YES settled at ~26¢
(last traded price) despite the event occurring. Traders who bought YES at 94¢ lost ~68¢ per
contract.

**This rule is the primary operational risk for:**
- Mention/speech markets where broadcast source or exact word matching is ambiguous
- Entertainment/awards markets with subjective determination criteria
- Any market where the resolution source is not explicitly named in the contract spec

**Always verify the contract spec for the specific resolution source — not just the market title.**

### Rule 6.3(e) — Death of Living Individuals (Effective March 2026)

Contracts on living individuals now settle at the **last traded price before death confirmation**
rather than auto-resolving YES on death. The settlement price may be rolled back to pre-news
levels, potentially far below the post-death trading price.

**Origin:** Khamenei died February 28, 2026. Kalshi did not pay YES on death-related contracts;
instead invoked 6.3(c) to settle at last-traded price. Class-action lawsuit followed.
Rule 6.3(e) was codified in March 2026 to formalize this behavior going forward.

**Operational rule: Do not trade any contract whose YES resolution depends on the death,
incapacitation, or departure of a living individual.** The Guardian and Scout must both
apply this filter. Rule 6.3(e) makes the expected payout on these contracts unpredictable
regardless of the underlying event occurring.

---

## Market Category Risk Summary

| Category | Dispute Risk | Rule 6.3(c) Exposure | Notes |
|----------|-------------|---------------------|-------|
| Sports (game results) | Low | Low | Official score feeds; rare ambiguity |
| Economic data (BLS, GDP, CPI) | Low | Low | Government releases are definitive; shutdown delay is the real risk |
| Political (votes, elections) | Medium | Medium | Manual review; edge cases in procedure |
| Mention / speech markets | Medium-High | High | Word matching and transcript source are common dispute triggers |
| Entertainment / awards | High | High | Rule 6.3(c) invocations documented; avoid |
| Death / departure of living persons | Extreme | Extreme | Rule 6.3(e) applies; **never trade** |
| Crypto spot price | Medium | Medium | Exchange source ambiguity; high pre-settlement volatility |

---

## Known Dispute History

- **Khamenei death market (Feb 2026):** Did not resolve YES on death. Settled at last-traded
  price per Rule 6.3(c). Rule 6.3(e) codified afterward. Kalshi reimbursed losses in this case,
  but that was a one-time goodwill action — not guaranteed policy.
- **Cardi B Super Bowl halftime market:** Outcome ruled "ambiguous." Rule 6.3(c) invoked.
  Settled at ~26¢ rather than YES or NO.
- **Tennis "Did Not Play" market:** Match never occurred. Settled at last-traded fair price
  (~$0.30) rather than voiding. Trader lost $30k. Kalshi's voiding practices differ from
  traditional sportsbooks — no-play does NOT automatically void.

**Operational takeaway:** When the underlying event does not occur, or occurs ambiguously,
Kalshi uses last-traded-price settlement rather than voiding. This is the single largest
structural difference from sportsbooks and other prediction platforms.
