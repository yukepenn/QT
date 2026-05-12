# Canonical execution smoke — results

Captured locally via:

```text
python scripts/canonical_execution_smoke.py
```

Example output (synthetic data; numbers vary slightly with OHLC):

- `fixed_target` — exits at target when bars reach plan; net PnL reflects slip + commission.
- `max_hold` — exits on `MAX_HOLD` with configured bar cap.
- `runner` — may combine scale-out / trailing depending on path; leg count logged.

Re-run after code changes to confirm the script still executes.
