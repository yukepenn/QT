# Canonical Layer 1 sweep (design)

**Status:** Not implemented. Mainline CLI: `python -m src.backtest.sweep` (use `--legacy` for Numba reference grid).

## Target pipeline

1. **Load bars** — `src/data/read_bars.py` (validated, sorted).
2. **Build features** — `FeatureStore` / `src/features` (no lookahead).
3. **Load strategy** — `src/strategies/loader.py`.
4. **Generate signals** — strategy-specific arrays or row-wise signals.
5. **Map to canonical contract** — columns per `docs/SIGNAL_CONTRACT.md` / `docs/FEATURES_CONTRACT.md`.
6. **Run backtest adapter** — `run_strategy_backtest` (or batch wrapper) → `simulate_trade_path` per trade.
7. **Summarize metrics** — `src/backtest/metrics.py` only aggregates canonical columns.

## Acceleration

- **Reference engine:** `src.execution.path.simulate_trade_path`.
- **Fast engine (future):** `src.execution.fast_path` — may delegate to Numba **only** after automated parity tests on synthetic and regression bar sets agree with the reference engine within defined tolerances.
- **`src/backtest/fast.py`** exposes **only** `TM_*` integer codes for legacy signal array compatibility; it does **not** define PnL semantics.

## Legacy reference

- `src.backtest.legacy.sweep_legacy` — Numba grid; prints `engine=legacy_numba_fast`.
- Do not compare legacy R/PnL to canonical outputs without labeling and parity study.
