# Commands

Run from `backend/` with the virtual environment activated:

```
source venv/bin/activate
```

## Production

```
python -m coliseum daemon
```

Starts the trading daemon (heartbeat loop) and the dashboard API server together on port 9000. This is the only command needed for normal operation.

## One-shot pipeline (testing/debug)

```
python -m coliseum pipeline
```

Runs the full pipeline once (Guardian → Scout → Analyst → Trader) then exits. Use this to validate changes without running the daemon.

## Dashboard API only

```
python -m coliseum api
```

Starts the FastAPI dashboard server on port 9000 with no trading daemon. Use this when testing the frontend against a live backend without triggering trades.

## Individual Agents

```
python -m coliseum scout
python -m coliseum analyst --id opp_abc12345
python -m coliseum trader --id opp_abc12345
python -m coliseum guardian
```

Run a single agent in isolation. Useful for debugging a specific stage of the pipeline.

## Health Check

```
GET /health
```

Returns server liveness and uptime. Does not require authentication, touch the database, or depend on the daemon. Use this for Kubernetes liveness probes, AWS ALB health checks, or any infrastructure monitoring.

Example response:

```json
{"status": "ok", "uptime_seconds": 3672}
```

- `status` is always `"ok"` when the server is responding.
- `uptime_seconds` is the integer number of seconds since server startup (0 if the lifespan has not run yet).

Available on both `app` (API-only) and `daemon_app` (daemon + API) instances on port 9000.

## Setup and Inspection

```
python -m coliseum init      # Create data/ directory structure and config templates
python -m coliseum status    # Print portfolio value and open positions
python -m coliseum config    # Print merged configuration and API key status
```
