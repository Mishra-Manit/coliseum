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

## Setup and Inspection

```
python -m coliseum init      # Create data/ directory structure and config templates
python -m coliseum status    # Print portfolio value and open positions
python -m coliseum config    # Print merged configuration and API key status
```
