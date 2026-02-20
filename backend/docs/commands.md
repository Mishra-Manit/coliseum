# Test Pipeline Commands

Run from `backend/` with the virtual environment activated:

```
source venv/bin/activate
```

Individual agents:

```
python -m coliseum.test_pipeline scout
python -m coliseum.test_pipeline scout --dry-run
python -m coliseum.test_pipeline analyst --opportunity-id opp_abc12345
python -m coliseum.test_pipeline trader --opportunity-file KXBTCD-26JAN2317-T89999.99.md
python -m coliseum.test_pipeline trader --verbose --opportunity-file KXBTCD-26JAN2317-T89999.99.md
python -m coliseum.test_pipeline guardian
```

## Trader
python -m coliseum.test_pipeline trader \
  --opportunity-file KXNBAMENTION-26FEB21LACLAL-INJU.md \
  --live


Pipeline + cleanup:

```
python -m coliseum.test_pipeline run --full
python -m coliseum.test_pipeline clean
```

## Full Sequential Pipeline

python -m coliseum.test_pipeline run --full

**Flow:**
1. Scout scans Kalshi markets → finds N opportunities (configured in `test_data/config.yaml`)
2. For opportunity 1: Analyst researches → Trader decides
3. For opportunity 2: Analyst researches → Trader decides

