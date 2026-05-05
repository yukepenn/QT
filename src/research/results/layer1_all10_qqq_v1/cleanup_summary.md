# Clean reset (Layer 1 all-10 v1)

## Removed

- `src/combiner/results/run_*` (old combiner comparison runs)
- `src/research/results/layer1_orb_vwap_qqq/`
- `src/research/results/layer1_ready9_qqq_v1/`
- `src/research/results/strategy_library_v1_health.csv`
- `src/research/results/strategy_library_v1_audit_report.md`
- `src/research/results/strategy_fast_core_migration_v1_before.csv`
- `src/research/results/strategy_fast_core_migration_v1_after.csv`
- `src/strategies/testing_parameters/orb_continuation.yaml` and `vwap_reversal.yaml` (legacy broad grids; default testing config now falls back to `*_focused.yaml` via `load_testing_config`)
- All `src/strategies/testing_parameters_results/*/sweep_*` folders
- `src/strategies/strategy/df_signal_strategy.py` (no remaining strategy imports)
- `__pycache__`, `*.pyc`, `*.nbc`, `*.nbi` under the repo (safe generated junk)

## Preserved

- `data/raw/ibkr/**` (parquet)
- All `src/strategies/**` code and `*_focused.yaml` grids
- `src/research/check_strategy_fast_parity.py`, `select_candidates.py`, `scoring.py`

## Loader default grids

After cleanup, `load_testing_config(<strategy>)` resolves `testing_parameters/<strategy>_focused.yaml` when `<strategy>.yaml` is absent.
