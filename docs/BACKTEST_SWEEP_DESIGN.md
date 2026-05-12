# Canonical Layer 1 sweep (design)

**Status:** **Synthetic + real-symbol MVP implemented** in `src/backtest/sweep.py` (`--smoke`, `run_real_symbol_sweep`, `--validate-pipeline`, `--dry-run`). Real runs require `read_bars` partitions for the requested window. Historical Numba sweep lives under **`archive/legacy_backtest/`** (not imported by mainline).

## Canonical responsibilities

- Expand parameter grids (`expand_param_grid`).
- Load strategy + apply params (real path: future; smoke uses pre-built `sig_*` rows).
- Generate or accept signals, then **map** to canonical `sig_*` (`src/backtest/signal_adapter.py` when renames are needed).
- Call **`run_strategy_backtest`** → **`simulate_trade_path`** → **`summarize_trades`**.
- Stamp **`execution_semantics_version`**, strategy id, **`config_hash`**, data window labels, cost assumptions via policy/backtest config, `engine=canonical_reference`, `canonical_or_legacy=canonical` on saved rows.

## Canonical sweep must **not**

- Compute fill prices, exit prices, or trade R outside `src/execution`.
- Import or silently call `src.backtest.legacy.fast_legacy` for accounting.
- Present smoke outputs as performance evidence.

## Target pipeline

1. **Load bars** — `src/data/read_bars.py` (validated, sorted).
2. **Build features** — `FeatureStore` / `src/features` (no lookahead).
3. **Load strategy** — `src/strategies/loader.py`.
4. **Generate signals** — strategy-specific arrays or row-wise signals.
5. **Map to canonical contract** — columns per `docs/SIGNAL_CONTRACT.md` / `docs/FEATURES_CONTRACT.md` and `signal_adapter`.
6. **Run backtest adapter** — `run_strategy_backtest` (or batch wrapper) → `simulate_trade_path` per trade.
7. **Summarize metrics** — `src/backtest/metrics.py` only aggregates canonical columns.

## Acceleration

- **Reference engine:** `src.execution.path.simulate_trade_path`.
- **Fast engine (future):** `src.execution.fast_path` — may delegate to Numba **only** after automated parity tests on synthetic and regression bar sets agree with the reference engine within defined tolerances.
- **`src/backtest/fast.py`** exposes **only** `TM_*` integer codes for legacy signal array compatibility; it does **not** define PnL semantics.

## Legacy reference

- `src.backtest.legacy.sweep_legacy` — Numba grid; prints `engine=legacy_numba_fast`.
- Do not compare legacy R/PnL to canonical outputs without labeling and parity study.
