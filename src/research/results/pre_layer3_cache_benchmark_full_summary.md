# Pre‑Layer‑3 cache benchmark — full comparison

Full comparison across **cache_off / cache_on_cold / cache_on_warm** was **skipped** because the local benchmark output folders under:

- `src/combiner/results/benchmarks/layer2_qqq_2025_recent_cache_benchmark/`

did not retain the curated CSV artifacts (`top_unique_systems.csv`, `behavior_unique_systems.csv`, `cost_stress_results.csv`, `cost_robust_systems.csv`) at the time of this finalization.

The benchmark gate remains **PASS** based on the already-recorded comparison artifacts:

- `pre_layer3_cache_benchmark_comparison.csv`
- `pre_layer3_cache_benchmark_summary.md`

which capture:

- wall-clock runtimes (cache_off/cold/warm),
- signal cache hit/miss behavior,
- equality of the **top_unique first row** within tolerance,
- and equality of the behavior first row.

