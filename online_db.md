# Coliseum — Supabase Schema

**ORM:** SQLAlchemy 2.0 (async, via `asyncpg`)
**Connection:** Direct Postgres URL (not PostgREST)
**Migrations:** Alembic
**Config:** Stays local (`config.yaml`)

---

## Tables

### `opportunities`
Replaces `data/opportunities/*.md`. Hot table — queryable metadata only. Heavy text lives in `opportunity_analysis`.

```sql
CREATE TABLE opportunities (
    id                          TEXT PRIMARY KEY,           -- "opp_c1cdf7d5"
    market_ticker               TEXT NOT NULL,
    event_ticker                TEXT NOT NULL,
    event_title                 TEXT NOT NULL,              -- primary display title in detail header
    title                       TEXT NOT NULL,              -- fallback title + feed row label
    subtitle                    TEXT,                       -- rendered below header if non-null
    yes_price                   NUMERIC(5,4) NOT NULL,
    no_price                    NUMERIC(5,4) NOT NULL,
    close_time                  TIMESTAMPTZ NOT NULL,
    discovered_at               TIMESTAMPTZ NOT NULL,
    status                      TEXT NOT NULL,              -- "pending" | "recommended" | "failed" | "skipped"
    outcome_status              TEXT NOT NULL,              -- "CONFIRMED" | "NEAR-DECIDED" | "STRONGLY FAVORED"
    risk_level                  TEXT NOT NULL,              -- "NEGLIGIBLE" | "LOW" | "MODERATE" | "HIGH"
    action                      TEXT,                       -- "BUY_YES" | "BUY_NO" | "ABSTAIN" | NULL
    trader_decision             TEXT,                       -- "EXECUTE_BUY_YES" | "EXECUTE_BUY_NO" | "REJECT" | NULL
    research_completed_at       TIMESTAMPTZ,
    recommendation_completed_at TIMESTAMPTZ,
    failed_stage                TEXT,
    failure_error               TEXT,
    failed_at                   TIMESTAMPTZ,
    paper                       BOOLEAN NOT NULL DEFAULT TRUE
);
```

---

### `opportunity_analysis`
Cold table. Joined only when a user opens a specific opportunity detail view. Never scanned for filtering or feed rendering.

```sql
CREATE TABLE opportunity_analysis (
    opportunity_id            TEXT PRIMARY KEY REFERENCES opportunities(id),
    rationale                 TEXT NOT NULL,                -- Scout long-form rationale
    resolution_source         TEXT,
    evidence_bullets          TEXT[] NOT NULL DEFAULT '{}',
    remaining_risks           TEXT[] NOT NULL DEFAULT '{}',
    scout_sources             TEXT[] NOT NULL DEFAULT '{}',
    research_synthesis        TEXT,                        -- Analyst free-form markdown (~3-4 KB)
    trader_tldr               TEXT,
    research_duration_seconds INT
);
```

---

### `open_positions`
Open positions only. Closed positions move to `closed_positions`.

```sql
CREATE TABLE open_positions (
    id              TEXT PRIMARY KEY,                       -- "pos_03293886"
    market_ticker   TEXT NOT NULL,
    side            TEXT NOT NULL,                         -- "YES" | "NO"
    contracts       INT NOT NULL,
    average_entry   NUMERIC(5,4) NOT NULL,
    current_price   NUMERIC(5,4) NOT NULL,
    opportunity_id  TEXT REFERENCES opportunities(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),    -- first time Coliseum persisted the position
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()     -- last portfolio reconciliation/update
);
```

---

### `closed_positions`
```sql
CREATE TABLE closed_positions (
    id              SERIAL PRIMARY KEY,
    market_ticker   TEXT NOT NULL,
    side            TEXT NOT NULL,                         -- "YES" | "NO"
    contracts       INT NOT NULL,
    entry_price     NUMERIC(5,4) NOT NULL,
    exit_price      NUMERIC(5,4) NOT NULL,
    pnl             NUMERIC(12,2) NOT NULL,
    opportunity_id  TEXT,                                  -- no FK: can be "sync_xxx" legacy values
    closed_at       TIMESTAMPTZ,
    entry_rationale TEXT
);
```

---

### `trades`
Replaces `data/trades/buy/*.jsonl`. Insert-only.

```sql
CREATE TABLE trades (
    id              TEXT PRIMARY KEY,                       -- "trade_0c83cd63"
    position_id     TEXT,
    opportunity_id  TEXT,
    market_ticker   TEXT NOT NULL,
    side            TEXT NOT NULL,                         -- "YES" | "NO"
    action          TEXT NOT NULL,                         -- "BUY" | "SELL"
    contracts       INT NOT NULL,
    price           NUMERIC(5,4) NOT NULL,
    total           NUMERIC(12,2) NOT NULL,
    paper           BOOLEAN NOT NULL,
    executed_at     TIMESTAMPTZ NOT NULL
);
```

---

### `trade_closes`
Replaces `data/trades/close/*.jsonl`. Insert-only.

```sql
CREATE TABLE trade_closes (
    id              TEXT PRIMARY KEY,                       -- "close_5e6abcd6"
    opportunity_id  TEXT,
    market_ticker   TEXT NOT NULL,
    side            TEXT NOT NULL,
    contracts       INT NOT NULL,
    entry_price     NUMERIC(5,4) NOT NULL,
    exit_price      NUMERIC(5,4) NOT NULL,
    pnl             NUMERIC(12,2) NOT NULL,
    entry_rationale TEXT,
    closed_at       TIMESTAMPTZ NOT NULL
);
```

---

### `portfolio_state`
Singleton current portfolio row. This is the authoritative source for live cash and valuation state.

```sql
CREATE TABLE portfolio_state (
    id              INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    cash_balance    NUMERIC(12,2) NOT NULL,
    positions_value NUMERIC(12,2) NOT NULL,
    total_value     NUMERIC(12,2) NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### `portfolio_snapshots`
New table. Appended every Guardian cycle. Powers PnL chart over time.

```sql
CREATE TABLE portfolio_snapshots (
    id              SERIAL PRIMARY KEY,
    total_value     NUMERIC(12,2) NOT NULL,
    cash_balance    NUMERIC(12,2) NOT NULL,
    positions_value NUMERIC(12,2) NOT NULL,
    open_positions  INT NOT NULL,
    realized_pnl    NUMERIC(12,2) NOT NULL,                -- SUM(closed_positions.pnl) at snapshot time
    snapshot_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### `seen_tickers`
Replaces `state.yaml -> seen_tickers[]`.

```sql
CREATE TABLE seen_tickers (
    ticker          TEXT PRIMARY KEY,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### `decisions`
Replaces `data/memory/decisions.jsonl`. Guardian back-fills `outcome` after resolution.

```sql
CREATE TABLE decisions (
    id               SERIAL PRIMARY KEY,
    ts               TIMESTAMPTZ NOT NULL,
    opportunity_id   TEXT,
    ticker           TEXT NOT NULL,
    action           TEXT NOT NULL,                        -- "EXECUTE_BUY_YES" | "EXECUTE_BUY_NO" | "REJECT"
    price            NUMERIC(5,4) NOT NULL,
    contracts        INT NOT NULL,
    confidence       NUMERIC(5,4) NOT NULL,
    reasoning        TEXT NOT NULL,
    tldr             TEXT,
    execution_status TEXT NOT NULL,
    outcome          TEXT                                  -- NULL until Guardian fills post-resolution
);
```

---

### `run_cycles`
Replaces `data/memory/journal/*.md`. One row per daemon cycle.

```sql
CREATE TABLE run_cycles (
    id               SERIAL PRIMARY KEY,
    cycle_at         TIMESTAMPTZ NOT NULL,
    duration_seconds INT NOT NULL,
    guardian_synced  INT NOT NULL DEFAULT 0,
    guardian_closed  INT NOT NULL DEFAULT 0,
    scout_scanned    INT NOT NULL DEFAULT 0,
    scout_found      INT NOT NULL DEFAULT 0,
    analyst_results  JSONB,                                -- {"TICKER": "recommended"} map
    trader_results   JSONB,                                -- {"TICKER": "EXECUTE_BUY_NO"} map
    cash_balance     NUMERIC(12,2),
    positions_value  NUMERIC(12,2),
    total_value      NUMERIC(12,2),
    open_positions   INT,
    errors           TEXT[] NOT NULL DEFAULT '{}'
);
```

---

### `learnings`
Replaces `data/memory/learnings.md`. Analyst appends rows; all active rows reconstructed into prompt context at runtime.

```sql
CREATE TABLE learnings (
    id          SERIAL PRIMARY KEY,
    category    TEXT NOT NULL,                             -- "Market Patterns" | "Execution Patterns" | "Error Patterns"
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active      BOOLEAN NOT NULL DEFAULT TRUE              -- soft-delete without losing history
);
```

---

## What stays local

| File | Reason |
|------|--------|
| `config.yaml` | Operator-controlled settings, not agent state |
| `data/memory/kalshi_mechanics.md` | Always passed as context; local keeps it fast and version-controlled |

---

## Storage layer changes

| Current file | Replaced by |
|---|---|
| `storage/state.py` | Queries on `portfolio_state`, `open_positions`, `closed_positions`, `seen_tickers` |
| `storage/files.py` | Writes to `opportunities` + `opportunity_analysis`; reads join both on detail fetch |
| `storage/sync.py` | Same logic, writes to above tables |
| `storage/_io.py` | Removed — SQLAlchemy handles atomicity via transactions |
| `memory/decisions.jsonl` | `decisions` table |
| `memory/journal/*.md` | `run_cycles` table |
| `memory/learnings.md` | `learnings` table |
| `memory/kalshi_mechanics.md` | Stays local — always passed as agent context |

New file: `services/supabase/db.py` — SQLAlchemy async engine + session factory using `SUPABASE_DB_URL` from `.env`.
