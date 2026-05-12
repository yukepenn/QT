# Canonical real-symbol sweep — plan

**Date:** 2026-05-11

## Objective

Wire **one strategy**, **one symbol**, **one NY date window**, optional **YAML/JSON grid**, through:

`read_bars` → `build_features_from_config` → `generate_signals` → `prepare_canonical_signals` → `run_strategy_backtest` → `summarize_trades`.

## Implementation status

| Area | Status |
|------|--------|
| Bridge module `src/backtest/strategy_runner.py` | Done |
| CLI `--validate-pipeline`, `--dry-run`, real sweep args | Done |
| `run_canonical_real_symbol_sweep` | Done |
| Artifacts (`canonical_sweep_results.csv`, `run_manifest.json`, `canonical_sweep_summary.md`) | Done when `--output-root` without `--no-save` |
| Multi-symbol / multi-asset batching | Out of scope (MVP) |
| Performance / broad sweeps | Explicitly out of scope |

## MVP constraints

- Reference execution only; no legacy Numba in this path.
- No Layer2 / Layer3 orchestration.
- No performance claims from default outputs.

## Next extensions

- Optional feature-column subset builds when strategies declare minimal primitives.
- Cache `FeatureStore` reuse across combos sharing the same feature key.
