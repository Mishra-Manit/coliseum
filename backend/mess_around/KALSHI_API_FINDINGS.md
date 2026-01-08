# Kalshi API Exploration Findings

**Date**: 2026-01-06
**Purpose**: Understand Kalshi API structure for event ingestion pipeline

---

## Key Discoveries

### ✅ Simple Binary Markets Exist!

We found simple YES/NO binary markets in the Kalshi API. They are available in specific **series** (like NFL games, NBA games, etc.).

### 📊 API Structure

**Kalshi has TWO main endpoints:**

1. **`/markets`** - Returns individual tradeable contracts
2. **`/events`** - Returns event containers (often without active markets)

**We should use `/markets` with series filters for the pipeline.**

---

## Market Types on Kalshi

### 1. Simple Binary Markets ✅
- Standard YES/NO markets
- Example: "Will Green Bay win vs Chicago?"
- These are what we want for the pipeline
- Found in series like: `KXNFLGAME`, `KXNBAGAME`, etc.

### 2. Multivariate/Parlay Markets ❌
- Combination of multiple markets
- Example: "YES Dallas wins AND YES Anthony Davis scores 15+"
- Have `mve_selected_legs` field
- Should be filtered out per DESIGN.md requirements

---

## Simple Binary Market Structure

```json
{
  "ticker": "KXNFLGAME-26JAN10GBCHI-GB",
  "title": "Green Bay at Chicago Winner?",
  "subtitle": "",
  "event_ticker": "KXNFLGAME-26JAN10GBCHI",
  "category": "",  // ⚠️ Empty! Need LLM classification
  "market_type": "binary",
  "close_time": "2026-01-25T01:00:00Z",
  "yes_bid": 50,  // Price in cents (50 = 50%)
  "yes_ask": 51,
  "no_bid": 49,
  "no_ask": 50,
  "volume": 119686,  // In dollars
  "liquidity": 9921816,  // In cents
  "open_interest": 107860,
  "rules_primary": "If Green Bay wins...",
  "rules_secondary": "If game is postponed...",
  // NO mve_selected_legs field (this indicates simple market)
}
```

---

## Critical Findings for Pipeline

### 1. Categories are Empty Strings
- The `category` field is `""` for all markets we tested
- **This confirms DESIGN.md requirement for LLM-based categorization**
- We'll need to use `title`, `subtitle`, and `rules_primary` to classify

### 2. Close Times Distribution
- Current markets (as of Jan 6, 2026):
  - **0-24 hours**: 0 markets
  - **24-48 hours**: 0 markets
  - **2-7 days**: 0 markets
  - **1-4 weeks**: Most markets
- **Implication**: May need to adjust DESIGN.md's "24-48 hour" window to "1-7 days" for more flexibility

### 3. Market Discovery Strategy
**DO NOT use**: `/events` endpoint (many return 404 when fetching markets)
**DO USE**: `/markets` endpoint with filters:
- `series_ticker`: Filter by specific series (NFL, NBA, etc.)
- `status`: `"open"`
- `limit`: Pagination (max 200 per page)

### 4. How to Filter for Simple Binary Markets

```python
def is_simple_binary(market: dict) -> bool:
    """Check if market is a simple binary YES/NO market."""
    # Must be marked as binary
    if market.get("market_type") != "binary":
        return False

    # Must NOT have multivariate legs
    if market.get("mve_selected_legs"):
        return False

    # Must have pricing data
    if "yes_ask" not in market or "yes_bid" not in market:
        return False

    return True
```

---

## Recommended Series for Ingestion

Based on exploration, these series have active simple binary markets:

| Series | Category | Example Markets | Volume |
|--------|----------|-----------------|--------|
| `KXNFLGAME` | Sports | NFL game winners | High |
| `KXNBAGAME` | Sports | NBA game winners | High |
| `FED` | Economics | Federal Reserve decisions | Medium |
| `INXD` | Finance | Stock market movements | Medium |
| (More to explore) | Politics | Political outcomes | High |

---

## Data Quality

### ✅ Good Quality
- `close_time`: Always present and accurate
- `yes_bid/yes_ask`: Pricing data available
- `volume`: Trading activity tracked
- `liquidity`: Market depth available
- `open_interest`: Position tracking

### ⚠️ Needs Processing
- `category`: Empty, requires LLM classification
- `subtitle`: Sometimes empty
- Price units: Given in cents (divide by 100 for percentages)

---

## Recommended Pipeline Adjustments

### 1. Event Selection Strategy
Instead of the original approach:
```
GET /events → Filter → Get markets for each event
```

Use this approach:
```
GET /markets?status=open&limit=1000
→ Filter for simple binary markets
→ Group by category (LLM classify)
→ Score and select top 5
```

### 2. Time Window Flexibility
- **Original DESIGN.md**: Markets closing in 24-48 hours
- **Reality**: Most active markets close in 1-7 days
- **Recommendation**: Make time window configurable (default: 1-7 days)

### 3. Category Classification Prompt

Example for LLM:
```
Classify this prediction market into ONE category:
- Politics
- Finance
- Sports
- Technology
- Other

Market: "{title}"
Rules: "{rules_primary}"

Category:
```

---

## Next Steps for Implementation

1. ✅ Exploration complete
2. **Create `KalshiClient` class** with methods:
   - `get_markets(status, limit, series_ticker)`
   - `filter_simple_binary(markets)`
   - `get_market_price(ticker)`
3. **Implement LLM Classifier** for categories
4. **Implement Multi-Factor Scoring**:
   - Volume/Liquidity score
   - Topic diversity
   - Price volatility (controversy)
5. **Implement Hard Quota Selector** (2-1-1-1)

---

## Code Examples from Exploration

See working scripts in `backend/mess_around/`:
- `explore_kalshi_api.py` - Main exploration
- `find_active_events.py` - Series-based discovery (SUCCESSFUL)
- `find_simple_markets.py` - Event ticker approach
- `explore_events_and_markets.py` - Events endpoint testing

**The `find_active_events.py` script successfully found simple binary markets!**

---

## Summary

✅ **Simple binary markets exist and are accessible**
✅ **Clear market structure with all needed fields**
✅ **Pricing, volume, and liquidity data available**
⚠️ **Categories need LLM classification (field is empty)**
⚠️ **Time windows may need adjustment (1-7 days vs 24-48 hours)**
📊 **Use `/markets` endpoint with series filters for best results**
