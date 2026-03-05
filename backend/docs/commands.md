# Commands

Run from `backend/` with the virtual environment activated:

```
source venv/bin/activate
```

## Individual Agents

```
python -m coliseum scout
python -m coliseum analyst --opportunity-id opp_abc12345
python -m coliseum trader --opportunity-id opp_abc12345
python -m coliseum guardian
```

## Full Pipeline

```
python -m coliseum run --once
```

**Flow:** Guardian -> Scout -> (Analyst -> Trader for each opportunity) -> Guardian
