# Feature performance hardening (v1)

## Scope

- **Code:** batch `pd.concat` for new columns in `volume.py`, `volatility.py`, `vwap.py`, `price_action.py`, `levels.py` (`add_prior_day_levels` post-merge block), `orb.py` (post-merge ORB fields).
- **Formulas:** intentionally unchanged (same groupby / rolling / shift semantics; VWAP still uses typical price \((H+L+C)/3\)).
- **Parity / Layer 1:** not rerun globally in this phase; local benchmark + parity scripts only.

## Before / after (QQQ 2025-01-01 → 2025-01-31, `build_features_from_config`, repeat=3)

| Config | Before mean (s) | After mean (s) | Before frag warns | After frag warns |
|--------|-----------------|----------------|---------------------|------------------|
| failed_orb | 0.59 | 0.45 | 2 | **0** |
| pa_buy_sell_close_trend | 0.39 | 0.38 | 0 | 0 |
| pa_climax_reversal | 0.38 | 0.39 | 0 | 0 |
| afternoon_continuation | 0.38 | 0.37 | 2 | **0** |

Source CSVs: `feature_build_performance_v1/before/feature_build_benchmark.csv`, `.../after/feature_build_benchmark.csv`.

## Snapshot equality (PA buy/sell close trend, 2025-01-01 → 2025-01-10)

- `feature_output_snapshot_before/` vs `feature_output_snapshot_after/`: **`columns_digest_sha256` identical** — no numeric drift in the digested column stats for this window.

## Fragmentation warnings

- **Before:** `PerformanceWarning: DataFrame is highly fragmented` from **`volume.py`** (and **`price_action.py`** rolling loop in heavier configs) observed in pytest / benchmark logs.
- **After:** benchmark **`fragmentation_warnings_count = 0`** for all four configs; targeted test `test_no_fragmentation_warning_optimized_modules` passes.

## Remaining bottlenecks

- **`regime.py`**, **`indicators.py`**, **`channels.py`**, **`pa_swings.py`**: not refactored in this pass; still dominate on very wide PA configs.
- **`groupby(...).transform(lambda ... rolling ...)`** remains Python-level; future **Numba** session kernels (see `feature_numba_fastpath_design.md`) would be the next step if wall time must drop further.

## Tests

- `tests/test_feature_performance_equivalence.py` — session boundaries, no duplicate columns, no LOOKAHEAD in PA required features, optimized-module fragmentation guard, `feature_key` stability.

## Sweep smoke (afternoon_continuation, Jan 2025, 50 combos)

- Tag `feature_perf_smoke`: `engine=numba_fast`, `feature_build≈0.64s` aggregate for 50 combos, **no** fragmentation warnings in console output.

