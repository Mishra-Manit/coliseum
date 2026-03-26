# Markets Data Dive: Updated 100% Win-Rate Filters

**Dataset**: `backend/monitoring/markets.csv`  
**Updated through**: Mar 26, 2026  
**Scope**: 1,583 completed trades from 1,771 tracked rows

---

## Baseline Performance

| Metric | Value |
|--------|-------|
| Total tracked rows | 1,771 |
| Completed trades | 1,583 |
| Wins (`close_price=100`) | 1,501 |
| Losses (`close_price=0`) | 82 |
| Overall win rate | 94.8% |
| Average entry price | ~94.4c |

The headline win rate stayed roughly the same, but the mix of losses changed. The older filter set is now stale in one important place: `KXTRUMPMENTION` is no longer unconditional-safe, while several price-gated weather prefixes now qualify for the 0-loss bucket.

---

## Where the 82 Losses Come From

### By Category

| Category | W | L | Win Rate | n |
|----------|---|---|----------|---|
| Economics | 34 | 0 | 100.0% | 34 |
| Entertainment | 36 | 0 | 100.0% | 36 |
| Sports | 53 | 1 | 98.1% | 54 |
| Crypto | 524 | 20 | 96.3% | 544 |
| Mentions | 171 | 9 | 95.0% | 180 |
| Climate and Weather | 569 | 30 | 95.0% | 599 |
| Financials | 104 | 16 | 86.7% | 120 |
| Politics | 6 | 3 | 66.7% | 9 |
| Science and Technology | 4 | 1 | 80.0% | 5 |

### Biggest Losing Prefixes

| Prefix | Losses | Notes |
|--------|--------|-------|
| `KXWTI` | 10 | Daily WTI is materially unsafe even at 95-96c |
| `KXBTCD` | 9 | Bitcoin directional remains safe only at 96c+ |
| `KXBTC` | 7 | Bitcoin range contracts are not safe, even at 96c |
| `KXHIGHNY` | 5 | NYC highs need a much stricter price gate |
| `KXHIGHDEN` | 5 | Denver highs remain unsafe at all practical gates |
| `KXETHD` | 2 | ETH directional safe only at 96c+ |
| `KXTRUMPMENTION` | 2 | Newly unsafe without a price gate |
| `KXNBAMENTION` | 3 | Unpredictable commentary remains lossy |

The strongest recurring pattern is unchanged: the bad losses cluster in event families where the final state can swing late or where wording/outcomes are intrinsically noisy.

---

## Deep Findings

## 1. Category-level rules are still too blunt

`Economics` and `Entertainment` still have zero losses and remain the safest unconditional allow-list.

But broad category gates are too coarse everywhere else:

- `Crypto` is only safe in select prefixes at `96c+`
- `Sports` is only clean for specific winner markets, not the whole category
- `Mentions` must now be prefix-specific and sometimes price-gated
- `Weather` is best handled by city-prefix plus price, not category alone

## 2. Crypto split matters more than category

### Directional crypto (`KXBTCD`, `KXETHD`, `KXETH`)

| Prefix / Rule | W | L | Win Rate | n |
|---------------|---|---|----------|---|
| `KXBTCD` all | 332 | 9 | 97.4% | 341 |
| `KXBTCD` @ `96+` | 80 | 0 | 100.0% | 80 |
| `KXETHD` all | 47 | 2 | 95.9% | 49 |
| `KXETHD` @ `96+` | 11 | 0 | 100.0% | 11 |
| `KXETH` all | 19 | 1 | 95.0% | 20 |
| `KXETH` @ `94+` | 9 | 0 | 100.0% | 9 |
| `KXETH` @ `96+` | 4 | 0 | 100.0% | 4 |

### Intraday/range crypto

| Prefix / Rule | W | L | Win Rate | n |
|---------------|---|---|----------|---|
| `KXBTC15M` | 9 | 0 | 100.0% | 9 |
| `KXETH15M` | 9 | 0 | 100.0% | 9 |
| `KXBTC` all | 87 | 7 | 92.6% | 94 |
| `KXBTC` @ `96+` | 22 | 1 | 95.7% | 23 |

Key update: `KXBTC` range markets should be explicitly rejected. They still lose at `96c`. Directional BTC/ETH stays usable, but only with the narrow `96c+` gate.

## 3. Weather got better if you use tighter city gates

The old writeup treated some cities as purely safe/unsafe. With more data, the better rule is:

- some cities are unconditional-safe
- some cities become safe only above a price threshold
- some cities still fail even at high prices and should stay blocked

### Unconditional-safe weather prefixes

| Prefix | W | L | n |
|--------|---|---|---|
| `KXHIGHMIA` | 47 | 0 | 47 |
| `KXLOWTLAX` | 26 | 0 | 26 |
| `KXLOWTMIA` | 16 | 0 | 16 |
| `KXHIGHTPHX` | 23 | 0 | 23 |
| `KXHIGHTMIN` | 20 | 0 | 20 |
| `KXLOWTMIN` | 5 | 0 | 5 |
| `KXHIGHTDAL` | 19 | 0 | 19 |
| `KXHIGHTOKC` | 11 | 0 | 11 |
| `KXHIGHTHOU` | 11 | 0 | 11 |
| `KXHIGHTSATX` | 9 | 0 | 9 |

### Newly safe with price gates

| Prefix | Safe Rule | W | L | n |
|--------|-----------|---|---|---|
| `KXHIGHCHI` | `entry_price >= 93` | 31 | 0 | 31 |
| `KXHIGHAUS` | `entry_price >= 93` | 30 | 0 | 30 |
| `KXHIGHTATL` | `entry_price >= 94` | 14 | 0 | 14 |
| `KXHIGHNY` | `entry_price >= 95` | 13 | 0 | 13 |
| `KXLOWTCHI` | `entry_price >= 94` | 10 | 0 | 10 |

### Still unsafe even with tight gates

| Prefix | Best practical result | Why reject |
|--------|------------------------|------------|
| `KXHIGHDEN` | 20W / 1L at `95+` | Still loses at high prices |
| `KXLOWTDEN` | 0-loss not established | Too little/noisy |
| `KXHIGHTSFO` | 2 losses | Microclimate risk |
| `KXHIGHTLV` | 2 losses | Range snap risk |
| `KXHIGHTBOS` | 2 losses | Forecast uncertainty |

New takeaway: Chicago, Austin, NYC highs, and Chicago lows can now be included safely, but only with explicit price gates.

## 4. Mentions need a revised allow-list

### Still safe without a price gate

| Prefix | W | L | n |
|--------|---|---|---|
| `KXPRESMENTION` | 13 | 0 | 13 |
| `KXSURVIVORMENTION` | 18 | 0 | 18 |
| `KXFEDMENTION` | 8 | 0 | 8 |
| `KXJENSENMENTION` | 5 | 0 | 5 |
| `KXENTMENTION` | 3 | 0 | 3 |
| `KXSCOTUSMENTION` | 4 | 0 | 4 |

### Safe only with a price gate

| Prefix | Safe Rule | W | L | n |
|--------|-----------|---|---|---|
| `KXTRUMPMENTION` | `entry_price >= 94` | 11 | 0 | 11 |

### Reject

| Prefix | Record | Why |
|--------|--------|-----|
| `KXTRUMPSAY` | 20W / 1L | phrase-specific variance |
| `KXNBAMENTION` | 42W / 3L | announcer wording remains unstable |
| `KXFIGHTMENTION` | 8W / 1L | too noisy |
| `KXSNLMENTION` | 3W / 1L | comedy/script variance |
| `KXPERSONMENTION` | 4W / 1L | too thin and already lossy |
| `KXMENTION` | 0W / 1L | outright unsafe |

Important update: `KXTRUMPMENTION` should no longer be in the unconditional safe list. The new NRCC dinner data introduced 2 losses at 92-93c, but `94c+` is still clean.

## 5. Sports are safe only for definitive winner markets

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXMLBSTGAME` all | 22 | 0 | 22 |
| `KXNASCARRACE` all | 13 | 0 | 13 |
| All Sports @ `94+` | 36 | 0 | 36 |
| `KXNASCARTOP10` | 0W / 1L | reject |

The broad sports gate still works historically at `94+`, but the safer implementation is to explicitly allow winner-style prefixes:

- `KXMLBSTGAME`
- `KXNASCARRACE`

and reject placement/prop variants like `KXNASCARTOP10`.

## 6. Financials remain mostly a trap, with one narrow exception

| Prefix / Rule | W | L | n |
|---------------|---|---|---|
| `KXWTI` | 43 | 10 | 53 |
| `KXWTIW` all | 26 | 1 | 27 |
| `KXWTIW` @ `94+` | 21 | 0 | 21 |
| `KXINX` | 11 | 2 | 13 |
| `KXINXU` | 10 | 2 | 12 |
| `KXNASDAQ100` | 1 | 1 | 2 |

Daily WTI, S&P, and Nasdaq should stay out. Weekly WTI (`KXWTIW`) is the only financial prefix that now clears a real sample-size threshold with 0 losses, but I would still treat it as optional because it is structurally more exposed to macro gaps than the other safe families.

---

## Recommended Scout Filter Set

This is the best updated 0-loss rule set from the current dataset.

### Core 100% filter set: 560W / 0L

| Rule Type | Rule |
|-----------|------|
| Category | `Economics` |
| Category | `Entertainment` |
| Crypto | `KXBTCD` and `entry_price >= 96` |
| Crypto | `KXETHD` and `entry_price >= 96` |
| Crypto | `KXETH` and `entry_price >= 96` |
| Sports | `KXMLBSTGAME` and `entry_price >= 94` |
| Sports | `KXNASCARRACE` and `entry_price >= 94` |
| Weather | `KXHIGHMIA`, `KXLOWTLAX`, `KXLOWTMIA`, `KXHIGHTPHX`, `KXHIGHTMIN`, `KXLOWTMIN`, `KXHIGHTDAL`, `KXHIGHTOKC`, `KXHIGHTHOU`, `KXHIGHTSATX` |
| Weather | `KXHIGHCHI` and `entry_price >= 93` |
| Weather | `KXHIGHAUS` and `entry_price >= 93` |
| Weather | `KXHIGHTATL` and `entry_price >= 94` |
| Weather | `KXHIGHNY` and `entry_price >= 95` |
| Weather | `KXLOWTCHI` and `entry_price >= 94` |
| Mentions | `KXPRESMENTION`, `KXSURVIVORMENTION`, `KXFEDMENTION`, `KXJENSENMENTION`, `KXENTMENTION`, `KXSCOTUSMENTION` |
| Mentions | `KXTRUMPMENTION` and `entry_price >= 94` |
| Other | `KXBTC15M`, `KXETH15M` |

### Optional expansion: 570W / 0L

Add:

- `KXWTIW` and `entry_price >= 94`

This improves coverage slightly, but I would keep it as an explicit opt-in rather than part of the default “maximum certainty” set.

---

## Performance of the Updated Core Filter

### Core set

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 560 |
| Losses | 0 |
| Coverage of completed trades | 35.4% |
| Average entry price | 94.68c |

### Core + optional `KXWTIW >= 94`

| Metric | Value |
|--------|-------|
| Win rate | 100.0% |
| Qualifying trades | 570 |
| Losses | 0 |
| Coverage of completed trades | 36.0% |
| Average entry price | 94.74c |

The updated filter increases zero-loss coverage meaningfully versus the older 416-trade rule set, mainly from:

- newly qualified weather gates (`KXHIGHCHI`, `KXHIGHAUS`, `KXHIGHNY`, `KXLOWTCHI`)
- retaining crypto only where the data still supports it
- tightening `KXTRUMPMENTION` instead of removing it entirely

---

## What Should Be Explicitly Rejected

| Reject | Reason |
|--------|--------|
| `KXBTC` | still loses at `96c` |
| `KXWTI` | daily oil remains structurally unsafe |
| `KXINX`, `KXINXU`, `KXNASDAQ100` | index gap risk |
| `KXHIGHDEN`, `KXLOWTDEN` | weather variability remains too high |
| `KXHIGHTSFO`, `KXHIGHTLV`, `KXHIGHTBOS` | microclimate / range-snap behavior |
| `KXNBAMENTION`, `KXTRUMPSAY`, `KXFIGHTMENTION`, `KXSNLMENTION`, `KXPERSONMENTION` | wording variance |
| `KXNASCARTOP10` | non-winner sports prop already failed |
| `Politics`, `Science and Technology` | too thin and already lossy |

---

## Scout Implementation Guidance

The Scout prefilter should stop thinking in broad categories outside of `Economics` and `Entertainment`. The winning pattern is:

1. derive `prefix = event_ticker.partition("-")[0]`
2. compute `entry_price = max(yes_ask, no_ask)`
3. allow only exact prefix/category rules with explicit price gates

Pseudo-shape:

```python
SAFE_CATEGORIES = {"Economics", "Entertainment"}

SAFE_PREFIXES = {
    "KXHIGHMIA",
    "KXLOWTLAX",
    "KXLOWTMIA",
    "KXHIGHTPHX",
    "KXHIGHTMIN",
    "KXLOWTMIN",
    "KXHIGHTDAL",
    "KXHIGHTOKC",
    "KXHIGHTHOU",
    "KXHIGHTSATX",
    "KXPRESMENTION",
    "KXSURVIVORMENTION",
    "KXFEDMENTION",
    "KXJENSENMENTION",
    "KXENTMENTION",
    "KXSCOTUSMENTION",
    "KXBTC15M",
    "KXETH15M",
}

PRICE_GATED_PREFIXES = {
    "KXBTCD": 96,
    "KXETHD": 96,
    "KXETH": 96,
    "KXMLBSTGAME": 94,
    "KXNASCARRACE": 94,
    "KXHIGHCHI": 93,
    "KXHIGHAUS": 93,
    "KXHIGHTATL": 94,
    "KXHIGHNY": 95,
    "KXLOWTCHI": 94,
    "KXTRUMPMENTION": 94,
    # optional:
    # "KXWTIW": 94,
}
```

Then:

- allow if category is in `SAFE_CATEGORIES`
- allow if prefix is in `SAFE_PREFIXES`
- allow if prefix is in `PRICE_GATED_PREFIXES` and `entry_price >= min_price`
- reject everything else by default

---

## Bottom Line

The best current “100% win-rate” filter is no longer just category + a few prefix safelists. It is now a precise allow-list of event families with selective price gates.

Most important updates versus the old analysis:

1. `KXTRUMPMENTION` must be changed from unconditional-safe to `94c+` only.
2. `KXBTC` range markets should be explicitly blocked.
3. `KXHIGHCHI`, `KXHIGHAUS`, `KXHIGHNY`, and `KXLOWTCHI` are now strong additions with strict gates.
4. `KXWTIW >= 94` is the only plausible financial expansion, but should stay optional.
