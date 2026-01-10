# How Kalshi Handles Multi-Outcome Events

## The Two Types of Events

### 1. **Binary Events** (YES/NO)
- **Example**: "Will Elon Musk visit Mars in his lifetime?"
- **Structure**:
  - 1 Event → 1 Market
  - Market has YES/NO prices
- **Event Field**: `mutually_exclusive: false`

```json
{
  "event_ticker": "KXELONMARS-99",
  "title": "Will Elon Musk visit Mars in his lifetime?",
  "mutually_exclusive": false
}
```

**Markets for this event:**
```json
{
  "ticker": "KXELONMARS-99-YES",
  "title": "Will Elon Musk visit Mars in his lifetime?",
  "yes_bid": 45,  // 45 cents = 45% probability
  "yes_ask": 47,
  "no_bid": 53,
  "no_ask": 55
}
```

---

### 2. **Multi-Outcome Events** (Multiple Options)
- **Example**: "Who will the next Pope be?"
- **Structure**:
  - 1 Event → Multiple Markets (one per candidate)
  - Each market is binary YES/NO for that specific outcome
- **Event Field**: `mutually_exclusive: true`

```json
{
  "event_ticker": "KXNEWPOPE-70",
  "title": "Who will the next Pope be?",
  "mutually_exclusive": true
}
```

**Markets for this event:**
```json
[
  {
    "ticker": "KXNEWPOPE-70-CARDINAL_A",
    "subtitle": "Cardinal Angelo De Donatis",
    "yes_bid": 15,  // 15% chance this person wins
    "yes_ask": 18
  },
  {
    "ticker": "KXNEWPOPE-70-CARDINAL_B",
    "subtitle": "Cardinal Pietro Parolin",
    "yes_bid": 25,  // 25% chance this person wins
    "yes_ask": 28
  },
  {
    "ticker": "KXNEWPOPE-70-CARDINAL_C",
    "subtitle": "Cardinal Luis Tagle",
    "yes_bid": 12,
    "yes_ask": 15
  },
  // ... more candidates
]
```

---

## Key Differences

| Feature | Binary Event | Multi-Outcome Event |
|---------|--------------|---------------------|
| `mutually_exclusive` | `false` | `true` |
| Number of markets | 1 | Multiple (one per outcome) |
| Market structure | YES/NO on the question | YES/NO on each specific outcome |
| Probabilities sum to | 100% (YES + NO) | ~100% across all outcome markets |

---

## How to Handle in Your App

### For Binary Events:
```python
# Fetch the event
event = get_event("KXELONMARS-99")

# Fetch its single market
markets = get_markets_for_event(event['event_ticker'])
market = markets[0]

# Show YES/NO prices
yes_price = market['yes_ask'] / 100  # Convert to percentage
no_price = market['no_ask'] / 100
```

### For Multi-Outcome Events:
```python
# Fetch the event
event = get_event("KXNEWPOPE-70")

# Fetch ALL markets (one per candidate)
markets = get_markets_for_event(event['event_ticker'])

# Show each outcome as a separate betting option
for market in markets:
    candidate = market['subtitle']
    probability = market['yes_ask'] / 100
    print(f"{candidate}: {probability}%")
```

---

## In Your Coliseum App

You should handle both types:

1. **Binary Events** → AI agents bet YES or NO
2. **Multi-Outcome Events** → AI agents pick which specific outcome to bet on (each outcome is still a YES bet on that specific market)

Example for "Who will win the election?":
- AI Agent 1: Bets YES on "Candidate A" market
- AI Agent 2: Bets YES on "Candidate B" market
- AI Agent 3: Bets YES on "Candidate C" market

Each is betting YES on their chosen outcome.
