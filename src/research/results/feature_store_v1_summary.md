# FeatureStore v1 — summary

## 1. Purpose

Add a generic **in-memory** `FeatureStore` to reuse raw bars and feature DataFrames across:

- Layer 1 sweeps (`src/backtest/sweep.py`)
- Layer 2 precompute (`src/combiner/precompute.py`)

This reduces repeated `build_features_from_config` work in cold runs and sets up clean boundaries before Layer 3. **Feature formulas are unchanged.**

## 2. Files changed

- New: `src/features/feature_store.py`
- Wired: `src/combiner/precompute.py`, `src/backtest/sweep.py`
- Docs: `src/research/results/feature_store_v1_plan.md`, this file
- Tests: `tests/test_feature_store.py`, `tests/test_combiner_precompute_feature_store.py`

## 3. FeatureStore API (v1)

- `FeatureStore(..., raw_df=None)` lazy-loads raw bars using `read_bars` on first feature request.
- `FeatureStore(..., raw_df=raw)` uses provided bars and never calls `read_bars`.
- `get_features(cfg)` / `get_features_by_key(feature_key, cfg)` returns features built via:
  - `feature_key_from_config(cfg)`
  - `build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)`
- `FeatureStoreStats`: raw load count, feature requests, cache hits/misses, raw row count.
- `write_stats(path)` writes a small JSON stats artifact.

## 4. Integration points

### Layer 2 precompute

- `precompute_candidate_signal_matrices` creates a `FeatureStore(raw_df=raw)` and uses it instead of a local feature dict cache.
- Writes `feature_store_stats.json` beside `candidate_precompute_profile.csv` when profile output is enabled.
- Signal cache hit behavior is preserved:
  - if signal cache hits, FeatureStore is skipped unless a one-time bootstrap is needed to build `backtest_arrays` / `meta_arrays`.

### Layer 1 sweep

- Replaces the per-symbol `feat_cache` dict with `FeatureStore(raw_df=raw)`.
- Keeps `array_cache` and `context_cache` unchanged.
- When saving results, writes `feature_store_stats.json` (list of stats by symbol) into the sweep folder.

## 5. Behavior preservation

Layer 2 `trap_family` top-1 fixed run equivalence (QQQ 2025-01-01 → 2026-04-30):

- trades: **329**
- total_r: **66.3293679139934**
- profit_factor: **1.479397596602119**
- max_drawdown_r: **-14.102637612790438**

## 6. Tests

- `python -m pytest -q` passes (includes FeatureStore tests).
- `test_feature_store.py`: cache hit/miss stats and equality vs direct feature build on a tiny raw DF.
- `test_combiner_precompute_feature_store.py`: precompute writes `feature_store_stats.json` and records requests.

## 7. Smoke results

- Layer 2 diagnostics smoke (QQQ Jan 2025, `trap_family` top-1): exit 0; signal counts unchanged (15 / 4 / 3).
- Layer 1 sweep smoke (`failed_orb`, QQQ Jan 2025, 10 combos, `--no-save`): exit 0.

## 8. Interaction with signal cache

- Signal cache is persistent disk cache under `.cache/qt/candidate_signals` (gitignored).
- FeatureStore is **in-memory only** per process/run.
- Warm signal-cache runs may skip both feature building and context generation per candidate; FeatureStore remains useful for cold starts and for bootstrap needs.

