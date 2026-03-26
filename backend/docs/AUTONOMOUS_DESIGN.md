# Coliseum: Autonomous System Design

## Vision

Transform Coliseum from a CLI-invoked pipeline (`python -m coliseum run --once`) into a **fully autonomous, self-healing daemon** that continuously manages a Kalshi portfolio using the sure-thing strategy—with persistent memory, automatic recovery, and context continuity across cycles. Deployed on a **Raspberry Pi** for always-on, low-power operation.

Inspired by **OpenClaw's architecture** (heartbeat daemon + file-based memory + 4-tier self-healing) and **Temporal's durable execution** model (checkpoint/replay + fault tolerance), adapted for a single-purpose trading system running on a Raspberry Pi.

---

## Current State vs Target State

| Capability | Current | Target |
|-----------|---------|--------|
| **Execution mode** | One-shot CLI (`run --once`) | Long-lived daemon with heartbeat loop |
| **Scheduling** | None (APScheduler removed) | Built-in async event loop with configurable intervals |
| **Self-healing** | None — crash = dead | 3-tier recovery: restart → diagnose → escalate |
| **Memory** | `state.yaml` + opportunity files (stateless between runs) | Persistent memory system: run journal, decision log, learnings |
| **Context** | Each pipeline run starts from zero context | Accumulated context: past trades, market patterns, error history |
| **Auto-start** | Manual `python -m coliseum run` | Raspberry Pi systemd service — auto-start on boot |
| **Monitoring** | Logfire traces (optional) | Logfire + Telegram heartbeat + health endpoint |
| **Error handling** | Log and continue/crash | Structured error recovery with escalation tiers |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COLISEUM AUTONOMOUS DAEMON                       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     DAEMON CORE (daemon.py)                   │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │
│  │  │  Heartbeat   │  │   Scheduler  │  │   Health Server    │   │  │
│  │  │  Loop        │  │   (intervals)│  │   (GET /health)    │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────────────────┘   │  │
│  │         │                 │                                   │  │
│  │         ▼                 ▼                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │              PIPELINE ORCHESTRATOR (pipeline.py)        │  │  │
│  │  │   Guardian → Scout → Analyst → Trader → Guardian        │  │  │
│  │  └──────────────────────┬──────────────────────────────────┘  │  │
│  │                         │                                     │  │
│  │  ┌──────────────────────▼──────────────────────────────────┐  │  │
│  │  │              RECOVERY ENGINE (recovery.py)              │  │  │
│  │  │   Tier 1: Auto-retry  │  Tier 2: Diagnose + Fix         │  │  │
│  │  │   Tier 3: Escalate to human (Telegram)                  │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    MEMORY LAYER (memory/)                     │  │
│  │                                                               │  │
│  │  ┌──────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────┐   │  │
│  │  │ Run      │ │ Decision     │ │ Learnings │ │ Error      │   │  │
│  │  │ Journal  │ │ Log          │ │ Store     │ │ History    │   │  │
│  │  │          │ │              │ │           │ │            │   │  │
│  │  │ Per-cycle│ │ Why we       │ │ Patterns  │ │ What broke │   │  │
│  │  │ summary  │ │ bought/      │ │ the system│ │ and how it │   │  │
│  │  │          │ │ skipped      │ │ learned   │ │ was fixed  │   │  │
│  │  └──────────┘ └──────────────┘ └───────────┘ └────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   EXISTING LAYERS (unchanged)                 │  │
│  │  Agents (Scout/Analyst/Trader/Guardian) │ Storage │ Services  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Daemon Core (`coliseum/daemon.py`)

The heart of autonomy. A single long-lived async process that replaces the one-shot `run_pipeline()`.

**Pattern**: Async event loop with configurable heartbeat (inspired by OpenClaw's Gateway).

```python
# Conceptual structure
class ColiseumDaemon:
    """Long-lived autonomous trading daemon."""
    
    async def start(self) -> None:
        """Start the daemon: health server + heartbeat loop."""
        # 1. Load settings, init Logfire, validate environment
        # 2. Start health HTTP server (for watchdog)
        # 3. Enter heartbeat loop
        
    async def heartbeat_loop(self) -> None:
        """Main loop: run pipeline on schedule, handle errors."""
        while self.running:
            cycle_start = utcnow()
            try:
                await self.run_cycle()
            except Exception as e:
                await self.recovery_engine.handle(e, context="pipeline_cycle")
            
            # Wait until next cycle
            elapsed = utcnow() - cycle_start
            sleep_seconds = max(0, self.interval - elapsed.total_seconds())
            await asyncio.sleep(sleep_seconds)
    
    async def run_cycle(self) -> None:
        """One full pipeline cycle with memory context."""
        # 1. Load memory context (recent decisions, active positions, error patterns)
        # 2. Run pipeline: Guardian → Scout → Analyst → Trader → Guardian
        # 3. Write run journal entry
        # 4. Update learnings if applicable
        # 5. Send heartbeat Telegram (configurable: every N cycles or on events)
```

**Config additions** (in `config.yaml`):

```yaml
daemon:
  heartbeat_interval_minutes: 60     # How often to run a full pipeline cycle
  guardian_interval_minutes: 15      # Guardian-only checks between full cycles
  max_consecutive_failures: 5        # Failures before escalation

telegram_send_alerts: true           # Heartbeat sent after every pipeline cycle
```

---

### 2. Memory System (`coliseum/memory/`)

OpenClaw's key insight: **plain markdown files as persistent memory**. This fits perfectly with Coliseum's existing file-based architecture.

#### 2a. Run Journal (`data/memory/journal/`)

One file per day, append-only. Gives the system context about what happened recently.

```
data/memory/journal/
├── 2026-03-04.md
├── 2026-03-05.md
└── ...
```

**Format**:
```markdown
## Cycle 2026-03-05T14:30:00Z

- **Duration**: 47s
- **Guardian**: Synced 3 positions, closed 1 (KXNBA-2026-LAL-WIN resolved YES, PnL +$3.42)
- **Scout**: Scanned 18,432 markets → 1 opportunity (KXWEATHER-2026-NYC-SNOW)
- **Analyst**: Researched KXWEATHER-2026-NYC-SNOW → BUY_YES recommended (93¢, close in 6h)
- **Trader**: Executed BUY_YES 5 contracts @ 93¢ ($4.65)
- **Portfolio**: Cash $87.23 | Positions $12.77 | Total $100.00
- **Errors**: None
```

**Purpose**: 
- Agents can read recent journal entries to understand current portfolio context
- Humans can quickly scan what the system has been doing
- Post-mortems become easy

#### 2b. Decision Log (`data/memory/decisions.jsonl`)

Structured append-only log of every BUY/SKIP decision with reasoning. This is the system's "why" memory.

```jsonl
{"ts": "2026-03-05T14:30:00Z", "ticker": "KXNBA-LAL-WIN", "action": "BUY_YES", "price": 0.94, "contracts": 5, "confidence": 0.92, "reasoning": "Lakers lead 3-0, game 4 tonight...", "outcome": null}
{"ts": "2026-03-05T14:30:00Z", "ticker": "KXFED-RATE-HOLD", "action": "SKIP", "reason": "spread_too_wide", "spread_cents": 5}
```

**Purpose**:
- Avoid re-analyzing markets that were recently skipped (with reason)
- Track decision quality over time (outcome field updated by Guardian on resolution)
- Feed back into agent prompts as "recent decisions" context

#### 2c. Learnings Store (`data/memory/learnings.md`)

Long-lived markdown file that accumulates system-level insights. Updated rarely — only when a meaningful pattern is detected.

```markdown
# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters

## Execution Patterns  
- Orders placed within 2h of close fill faster (93% vs 71% fill rate)
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books

## Error Patterns
- Kalshi API returns 429 between 2-3am UTC during maintenance — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
```

**Purpose**:
- Injected into agent system prompts as persistent context
- Evolves over time as the system accumulates experience
- Human-editable — you can add insights manually

#### 2d. Error History (`data/memory/errors.jsonl`)

Structured log of every error with resolution status.

```jsonl
{"ts": "2026-03-05T02:30:00Z", "component": "scout", "error": "HTTPStatusError 429", "resolution": "auto_retry", "attempts": 2}
{"ts": "2026-03-05T03:00:00Z", "component": "trader", "error": "InsufficientFunds", "resolution": "escalated_telegram", "details": "Cash $2.10 < required $4.65"}
```

**Purpose**:
- Recovery engine reads recent errors to detect recurring patterns
- Escalation decisions based on error frequency (e.g., 3 same errors in 1h → escalate)
- Dashboard shows error trends

---

### 3. Self-Healing & Recovery

Three tiers, implemented directly in `daemon.py`, `pipeline.py`, and `memory/errors.py` — no separate `recovery.py` needed.

#### Tier 1: Auto-Retry (already implemented)
- **Scope**: Transient failures (API timeouts, rate limits, network blips)
- **Status**: Done. Both external clients have exponential-backoff retry built in:
  - `KalshiClient._request()` — handles 429, 5xx, and `httpx.TimeoutException` with `2^n` second backoff
  - `ExaClient._retry_wrapper()` — same pattern for the Exa SDK
- No additional work required.

#### Tier 2: Component Isolation (already implemented)
- **Scope**: One agent fails but others can continue
- **Status**: Done. `pipeline.py` wraps every stage in try/except and continues:
  - Guardian failure → logged, pipeline continues to Scout
  - Scout failure → logged, pipeline exits early
  - Analyst/Trader failure per opportunity → logged, skips to next opportunity
- Per-component health tracking (skip unhealthy components for N cycles) is not implemented — silent continuation already handles the common cases without the added complexity.

#### Tier 3: Escalate to Human (implemented)
- **Scope**: Repeated pipeline-level failures exhaust `max_consecutive_failures`
- **Status**: Done. `daemon._send_escalation_alert()` is called when `_paused` flips to True.
- **What it sends**: Error message, recurring-error pattern detection result (same error 3x in 1h), uptime, cycle count, last success timestamp.
- **Pattern detection**: `memory/errors.py:detect_recurring_error()` reads `errors.jsonl`, groups by error signature (first 120 chars), flags if any signature hits the threshold.
- **Gate**: Only fires if `settings.telegram_send_alerts = true` AND `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are set in `.env`.

```
COLISEUM ALERT

Daemon paused after 5 consecutive failures.
Last error: KalshiAPIError: Request failed after 3 retries: ...
Recurring pattern: 'KalshiAPIError: Request failed after 3 retri' seen 5x in the last 1h
Uptime: 3.2h | Cycles completed: 3
Last success: 2026-03-05T11:20:00Z

Action: Pipeline paused. Manual intervention required or daemon will retry after next heartbeat interval.
```

---

### 4. Auto-Start via systemd (`scripts/`)

The Raspberry Pi runs Raspberry Pi OS (Debian-based), which uses **systemd** as its init system. We define a systemd service unit to manage the Coliseum daemon as a first-class OS service.

#### Service Unit File

```ini
# /etc/systemd/system/coliseum.service
[Unit]
Description=Coliseum Autonomous Trading Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=coliseum
Group=coliseum
WorkingDirectory=/home/coliseum/coliseum/backend
EnvironmentFile=/home/coliseum/coliseum/backend/.env
ExecStart=/home/coliseum/coliseum/backend/venv/bin/python -m coliseum daemon
Restart=on-failure
RestartSec=30
StartLimitIntervalSec=300
StartLimitBurst=5
WatchdogSec=300

StandardOutput=journal
StandardError=journal
SyslogIdentifier=coliseum

[Install]
WantedBy=multi-user.target
```

#### What each directive does

- **`After=network-online.target`** — waits for network before starting (Kalshi API needs connectivity)
- **`User=coliseum`** — runs as a dedicated non-root user for security
- **`EnvironmentFile`** — loads `.env` (API keys, RSA key path) without embedding secrets in the unit file
- **`Restart=on-failure`** — systemd auto-restarts the daemon if it exits with a non-zero code
- **`RestartSec=30`** — 30-second cooldown between restarts to prevent crash loops
- **`StartLimitIntervalSec=300` / `StartLimitBurst=5`** — if the service fails 5 times within 5 minutes, systemd stops trying and marks it as failed (prevents infinite restart loops)
- **`WatchdogSec=300`** — systemd expects a watchdog ping every 5 minutes; if the daemon hangs (not just crashes), systemd kills and restarts it. The daemon must call `sd_notify("WATCHDOG=1")` periodically via the `sdnotify` Python package.
- **`StandardOutput=journal` / `StandardError=journal`** — all logs go to journald, queryable via `journalctl`

#### Watchdog Integration

The `WatchdogSec` directive provides hang detection — something a simple `Restart=on-failure` can't catch. The daemon's heartbeat loop sends a watchdog ping to systemd after each cycle:

```python
import sdnotify

notifier = sdnotify.SystemdNotifier()

async def heartbeat_loop(self) -> None:
    notifier.notify("READY=1")  # Signal successful startup
    while self.running:
        await self.run_cycle()
        notifier.notify("WATCHDOG=1")  # Tell systemd we're still alive
        await asyncio.sleep(self.interval)
```

If the daemon hangs mid-cycle (e.g., a blocking API call that never returns), it won't send the watchdog ping, and systemd will restart it after 300 seconds.

#### Setup Commands (on the Raspberry Pi)

```bash
# Create dedicated user
sudo useradd -r -m -s /bin/bash coliseum

# Deploy code to /home/coliseum/coliseum/ and set up venv
sudo -u coliseum bash -c 'cd /home/coliseum/coliseum/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt'

# Install the service
sudo cp scripts/coliseum.service /etc/systemd/system/coliseum.service
sudo systemctl daemon-reload
sudo systemctl enable coliseum.service  # Auto-start on boot
sudo systemctl start coliseum.service   # Start now
```

#### Management Commands

```bash
# Status and control
sudo systemctl status coliseum          # Check if daemon is running
sudo systemctl start coliseum           # Start daemon
sudo systemctl stop coliseum            # Stop daemon
sudo systemctl restart coliseum         # Restart daemon

# Logs via journald
journalctl -u coliseum -f               # Tail live logs
journalctl -u coliseum --since today    # Today's logs
journalctl -u coliseum -n 100           # Last 100 lines
```

#### CLI Helpers

Convenience commands that wrap systemctl (must be run on the Pi):

```bash
python -m coliseum daemon install   # Copy .service file, daemon-reload, enable + start
python -m coliseum daemon uninstall # Stop, disable, remove .service file
python -m coliseum daemon status    # systemctl status coliseum
python -m coliseum daemon logs      # journalctl -u coliseum -f
```

---

### 5. Context Injection Into Agents

The most impactful change: agents get **accumulated context** instead of starting cold every cycle.

#### What gets injected:

| Agent | Context Injected |
|-------|-----------------|
| **Scout** | Recent decisions (skip reasons for seen markets), current portfolio snapshot, learnings about market patterns |
| **Analyst** | Current portfolio state (to assess concentration risk), recent similar analyses, relevant learnings |
| **Trader** | Full portfolio state, recent trade outcomes, execution learnings (fill rates, spread behavior) |
| **Guardian** | No prompt injection — Guardian is fully deterministic (no LLM). Instead: **output enrichment**. When reconciling a newly closed position, Guardian reads the opportunity file via `opportunity_id` and embeds the original entry rationale into the `ClosedPosition` record for audit trail purposes. |

#### Implementation:

```python
# In pipeline.py, before each agent call
async def build_scout_context(self) -> str:
    """Build accumulated context for Scout agent."""
    journal = load_recent_journal(days=2)
    decisions = load_recent_decisions(hours=24)
    learnings = load_learnings(section="market_patterns")
    portfolio = load_state()
    
    return f"""
## Current Portfolio
Cash: ${portfolio.cash_balance:.2f} | Positions: {len(portfolio.open_positions)}

## Recent Decisions (last 24h)
{format_decisions(decisions)}

## System Learnings
{learnings}
"""
```

This context string gets prepended to the agent's prompt, giving it awareness of what has happened recently without re-running any analysis.

---

### 6. Health & Observability Enhancements

#### Health Endpoint (`GET /health`)

Lightweight HTTP endpoint the watchdog (or external monitoring) can poll:

```json
{
  "status": "healthy",
  "uptime_seconds": 43200,
  "last_cycle": "2026-03-05T14:30:00Z",
  "last_cycle_duration_seconds": 47,
  "cycles_completed": 12,
  "consecutive_errors": 0,
  "portfolio": {
    "total_value": 100.00,
    "open_positions": 3
  },
  "component_health": {
    "scout": "healthy",
    "analyst": "healthy", 
    "trader": "healthy",
    "guardian": "healthy"
  }
}
```

#### Telegram Heartbeat

Periodic "I'm alive" message (configurable, e.g., every 6 cycles = ~6 hours):

```
✅ COLISEUM HEARTBEAT — 2026-03-05 14:30 UTC

Uptime: 12h | Cycles: 12 | Errors: 0
Portfolio: $100.00 (Cash $87.23 + Positions $12.77)
Open positions: 3
Last trade: BUY_YES KXWEATHER-NYC-SNOW @ 93¢ (2h ago)
```

---

## Implementation Plan

### Phase 1: Daemon Core + Scheduling (Highest Impact)
1. Create `coliseum/daemon.py` with heartbeat loop
2. Add `DaemonConfig` to `config.py`
3. Add `daemon` CLI subcommand to `__main__.py`
4. Integrate Guardian-only cycles between full pipeline cycles
5. Add graceful shutdown (SIGTERM/SIGINT handling)

### Phase 2: Memory System
1. Create `coliseum/memory/` module (journal, decisions, learnings, errors)
2. Wire journal writes into `pipeline.py` (post-cycle summary)
3. Wire decision log into Trader (on every BUY/SKIP)
4. Wire error log into recovery engine
5. Create `data/memory/learnings.md` seed with initial content
6. Update `cmd_init` to create memory directory structure

### Phase 3: Self-Healing & Recovery (complete)
1. ~~Create `coliseum/recovery.py`~~ — not needed; logic lives in `daemon.py` and `memory/errors.py`
2. ~~Add retry decorator for external API calls~~ — already done in `KalshiClient._request()` and `ExaClient._retry_wrapper()`
3. ~~Add component health tracking to pipeline~~ — not implemented; pipeline's existing per-stage try/except is sufficient
4. Wire Tier 3 escalation to existing Telegram service — done in `daemon._send_escalation_alert()`
5. Add error pattern detection (same error 3x in 1h → escalate) — done in `memory/errors.py:detect_recurring_error()`

### Phase 4: Context Injection
1. Build context loaders (recent journal, decisions, portfolio)
2. Inject into Scout prompt (recent decisions, portfolio state)
3. Inject into Analyst prompt (portfolio concentration, similar analyses)
4. Inject into Trader prompt (execution history, fill rate patterns)
5. Enrich Guardian output (on close, read opportunity file via `opportunity_id` and embed original entry rationale into `ClosedPosition` record — no LLM prompt, pure deterministic output enrichment)

### Phase 5: Health & Observability
1. Add lightweight health HTTP server to daemon
2. Add Telegram heartbeat (periodic summary)
3. Add dashboard integration (surface daemon status in frontend)

### Phase 6: Auto-Start via systemd + CLI
1. Create `scripts/coliseum.service` systemd unit file
2. Add `sdnotify` to `requirements.txt` and wire watchdog pings into heartbeat loop
3. Add `daemon install/uninstall/status/logs` CLI commands (wrapping `systemctl` / `journalctl`)
4. Create setup script for Raspberry Pi (user creation, venv, service install)
5. Write deployment documentation for Raspberry Pi

---

## Key Design Decisions

### Why NOT Temporal?

Temporal is excellent for durable execution but introduces significant operational overhead:
- Requires running a Temporal server (another process to manage)
- Adds complexity for a single-machine, single-pipeline system
- Coliseum's pipeline is short-lived (~1min per cycle) — Temporal shines for hours/days-long workflows

**Instead**: We get 80% of the benefit with:
- **Checkpoint files** for pipeline state (which step completed)
- **systemd** for auto-restart + watchdog hang detection (equivalent to Temporal's worker restart, but OS-native)
- **Idempotent pipeline stages** (can safely re-run any stage)

### Why Raspberry Pi + systemd?

- **Always-on, low-power**: A Raspberry Pi draws ~5W — perfect for a 24/7 trading daemon without running up electricity costs
- **systemd is battle-tested**: It's the standard init system on Raspberry Pi OS (Debian). Auto-start on boot, auto-restart on crash, watchdog hang detection, and journald logging — all built in, zero dependencies
- **No cloud costs**: The system runs on hardware you own, with no monthly server bills
- **`WatchdogSec` catches hangs**: Unlike simple process restarters, systemd's watchdog detects when the daemon is alive but stuck (e.g., a blocking network call), and restarts it
- **`journalctl` for logs**: No need to manage log files or rotation — journald handles it natively with structured querying

### Why file-based memory over a database?

Following OpenClaw's philosophy:
- Human-readable and editable (you can tweak learnings manually)
- Git-friendly (version control your system's memory)
- No database server to manage
- Consistent with existing Coliseum storage model (YAML + Markdown)
- Performance is fine for our scale (one write per cycle ≈ 1/hour)

### Why 3 tiers instead of OpenClaw's 4?

OpenClaw's Tier 3 (AI diagnosis) uses Claude to read logs and fix issues. This is powerful but:
- Adds significant complexity and cost
- Risk of AI making wrong fixes to a financial system
- Our system is simpler (single pipeline) — most issues are transient API failures

We can add AI-assisted diagnosis later as a Tier 2.5 if needed.

---

## Risk Considerations

| Risk | Mitigation |
|------|-----------|
| **Daemon crash loop** | systemd `RestartSec=30` + `StartLimitBurst=5` in 5min → marks service failed + Telegram alert |
| **Memory files grow unbounded** | Journal rotation (keep 30 days), decisions rotation (keep 90 days) |
| **Stale context misleads agents** | Context loader only pulls recent data (24h for decisions, 2 days for journal) |
| **State corruption during crash** | Existing atomic writes (tempfile + rename) already handle this |
| **API key rotation** | Daemon reloads settings from `.env` on each cycle (no caching across cycles) |
| **Paper mode → live mode transition** | Explicit `paper_mode: false` in config + Telegram confirmation on first live trade |

---

## What This Enables

Once fully implemented, you can:

1. **`sudo systemctl start coliseum`** — Start and walk away. System runs 24/7 on your Raspberry Pi.
2. **Reboot the Pi** — Daemon auto-starts via systemd, resumes from last known state.
3. **Daemon hangs** — systemd watchdog detects the hang and restarts the service automatically.
4. **API goes down** — System retries, skips if persistent, alerts you on Telegram.
5. **Check in via Telegram** — Get periodic heartbeats showing portfolio state.
6. **Review decisions** — Read `data/memory/journal/` for a full audit trail.
7. **Tune strategy** — Edit `data/memory/learnings.md` to steer agent behavior.
8. **Check logs remotely** — `ssh pi && journalctl -u coliseum -f` for live log tailing.
9. **Monitor from dashboard** — Frontend shows daemon health, recent cycles, portfolio.
