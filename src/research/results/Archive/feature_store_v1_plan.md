# FeatureStore v1 — plan (pre–Layer 3)

## 1. Current feature flow

- Raw bars loaded via `src/data/read_bars.py:read_bars`.
- Feature columns built via `src/features/feature_key.py:build_features_from_config` which calls `src/features/build_features.py:build_basic_features`.
- Feature output is sorted `ts_utc` (callers typically do `.sort_values("ts_utc", ignore_index=True)`).

## 2. Existing `feature_key` behavior

- `feature_key_from_config(cfg)` returns a **hashable tuple** derived from `cfg["features"]` knobs:
  - `orb_open_minutes`, `vwap_bands`, `vol_windows`, `price_action_windows`, `volume_windows`.
- This key is intended to uniquely identify the feature DataFrame schema + values.

## 3. Where Layer 1 uses feature cache today

- `src/backtest/sweep.py`:
  - loads `raw = read_bars(...)` per symbol
  - caches feature DataFrames in `feat_cache[fk]`
  - caches prepared arrays in `array_cache[fk]`
  - caches contexts in `context_cache[(fk, strat.context_key(cfg))]`

## 4. Where Layer 2 uses feature cache today

- `src/combiner/precompute.py`:
  - loads `raw = read_bars(...)` once per run
  - previously cached features in a local dict; now also has a persistent **signal cache**
  - still needs feature DataFrames for cold runs and for some bootstrap cases when signal-cache hits occur

## 5. What FeatureStore will centralize

- A reusable per-window object that:
  - lazily loads raw bars (or accepts a provided `raw_df`)
  - caches feature DataFrames keyed by `feature_key_from_config(cfg)` (with optional key normalization)
  - tracks hit/miss/request stats and writes a small `feature_store_stats.json` beside profiles/results

## 6. What will NOT change

- Feature formulas, columns, and values produced by `build_basic_features`.
- Strategy logic, Layer 1 grids, Layer 2 grids, and Layer 2 signal cache semantics.
- Layer 3 remains out of scope.

## 7. Tests and smokes

- Unit tests for FeatureStore:
  - key normalization + caching stats
  - equality vs `build_features_from_config(raw, cfg)` on a small real window (QQQ Jan 2025)
- Integration tests:
  - Layer 2 precompute still produces identical matrices and writes stats JSON.
- Smokes / equivalence:
  - Layer 2 diagnostics smoke (QQQ Jan 2025, `trap_family` top1)
  - Fixed trap top1 full-window equivalence vs reference metrics
  - Small Layer 1 sweep smoke for `failed_orb` (no behavior comparison required)

