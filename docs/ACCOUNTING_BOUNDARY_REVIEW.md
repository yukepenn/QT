# Accounting boundary review

**Date:** 2026-05-11  
**Purpose:** Map which layers may compute fills, exits, and PnL vs canonical `src.execution`, and flag legacy paths.

## Summary

- **Canonical execution** (`src/execution/path.py`, `materialize.py`, `fill.py`, `exits.py`, `pnl.py`) owns entry fill, initial risk, fixed-R / fixed-price / none targets, intrabar exit ordering, partial legs, gross vs net PnL/R, and commission allocation (one charge per trade).
- **Backtest adapter** (`src/backtest/engine.py`) maps `sig_*` columns to raw `TradeIntent` and calls `simulate_trade_path`; it does not compute entry fill, risk, or targets.
- **Metrics** (`src/backtest/metrics.py`) aggregates `r_multiple`, `net_pnl`, optional `gross_r_multiple`; it does not re-derive per-trade R from prices.
- **Legacy:** `src/backtest/sweep.py`, `src/backtest/legacy/*`, Numba fast path — pre-reset accounting, not interchangeable with canonical execution without parity tests.

Machine-readable rows: `docs/ACCOUNTING_BOUNDARY_REVIEW.csv`.
