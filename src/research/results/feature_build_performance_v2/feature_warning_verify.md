# Feature warning verification (post 51bfe17)

## Summary

- `python src/research/feature_build_benchmark.py` was run for Jan 2025 QQQ with four representative configs under `src/research/results/feature_build_performance_v2/verify_after/`.
- **fragmentation_warnings_count** is **0** for all configs (see `feature_build_benchmark.csv`).
- The historical `PerformanceWarning: DataFrame is highly fragmented` from `src/features/volume.py` (pre-hardening) is **not reproduced** on this path.

## Benchmark snapshot (repeat=3)

| config | wall_sec_mean | fragmentation_warnings_count |
|--------|---------------|-------------------------------|
| failed_orb | 0.47 | 0 |
| afternoon_continuation | 0.39 | 0 |
| pa_buy_sell_close_trend | 0.39 | 0 |
| pa_climax_reversal | 0.41 | 0 |

## Notes

- Global Layer 1 v2 was started only after this check (per research workflow).
- A separate sweep smoke (`--tag feature_perf_verify`) should be consulted in `src/strategies/testing_parameters_results/` (not committed) for console-level confirmation.
