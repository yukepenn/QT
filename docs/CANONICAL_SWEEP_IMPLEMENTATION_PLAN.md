# Canonical sweep — implementation plan

**Date:** 2026-05-11  
**Scope:** Layer 1 reference-engine sweep (`src/backtest/sweep.py`), explicit legacy boundary, synthetic smoke only in CI.

## Done (this milestone)

- Public API: `expand_param_grid`, `config_hash`, `run_canonical_sweep`, `run_single_canonical_combo`, `run_synthetic_canonical_smoke`, `canonical_sweep_main`, `main`.
- Dataclasses: `SweepCombo` (flattened combo id + params via `run_canonical_sweep` rows), `SweepResult`, `CanonicalSweepConfig`.
- CLI: `--smoke`, `--canonical-help`, reserved `--config` / `--grid` / `--data-root`; default exit ≠ 0 without actionable args; **`--legacy` must be argv[0]** → `sweep_legacy.main(argv[1:])`.
- `src/backtest/signal_adapter.py`: rename map, validate valid rows, assert helper.
- Tests: grid/hash/smoke/schema/legacy boundary / execution path (patched `engine.simulate_trade_path`).
- Docs: design updates, result schema, smoke summary, strategy integration plan, inventory CSV.

## Next (not in this milestone)

- Wire `read_bars` + `FeatureStore` + strategy `generate_signals` into `run_canonical_sweep` for real symbols (no CI dependency on QQQ parquet).
- Parse `--grid` / `--config` YAML into `expand_param_grid` input + strategy params (`_finalize_combo_config` patterns from legacy, without calling legacy accounting).
- Optional: emit `SweepCombo` objects from runner for richer provenance.

## Non-goals

- Numba acceleration, WFO, combiner accounting, Champion YAML edits, performance claims from smoke.
