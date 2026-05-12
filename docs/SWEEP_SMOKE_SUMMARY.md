# Canonical sweep — synthetic smoke

**Date:** 2026-05-11

## What runs

`python -m src.backtest.sweep --smoke` (or `run_synthetic_canonical_smoke()`):

1. Builds a 12-row OHLCV frame with UTC + NY timestamps and session metadata.
2. Seeds **one** valid long signal at row index `SYNTHETIC_SIGNAL_ROW` (3): `fixed_r` target, stop 99, `sig_risk_per_share` 1.0.
3. Sweeps grid `{"sig_target_r": [1.0, 2.0]}` → **two** combos.
4. Each combo: `assert_canonical_signal_frame` → `run_strategy_backtest` → `summarize_trades`.
5. Prints `engine=canonical_reference`, `canonical_or_legacy=canonical`, and the results table.

## Outputs

- In-memory: two-row `DataFrame` with schema in `docs/CANONICAL_SWEEP_RESULT_SCHEMA.md`.
- Optional: `--output-root` without `--no-save` writes `canonical_sweep_smoke.csv` and `canonical_sweep_meta.json` (tiny only).

## Guarantees

- No parquet, no QQQ, no external files.
- Deterministic given fixed seeds/constants.
- Not a performance benchmark; do not cite smoke rows as live edge.
