# Pre‑Layer‑3 cache benchmark plan (Layer 2 recent)

## Purpose

Benchmark **signal cache** (disk) + **FeatureStore** (in‑memory) before Layer 3, and confirm they **do not change results**.

This benchmark uses the **recent** Layer 2 sweep config (manageable and already validated for equivalence on trap_family top‑1).

## Inputs

- **candidate_root:** `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/selected_candidates`
- **sweep config:** `src/combiner/configs/layer2_sweep_qqq_2025_20260430_recent_check_v1.yaml`
- **base config (for postprocess):** `src/combiner/configs/layer2_qqq_2025_20260430_recent_check_v1.yaml`
- **window:** QQQ 2025‑01‑01 → 2026‑04‑30

## Modes

1. **cache_off**: no signal cache flags
2. **cache_on_cold**: `--use-signal-cache --signal-cache-root ... --refresh-signal-cache`
3. **cache_on_warm**: `--use-signal-cache --signal-cache-root ...` (no refresh)

## Outputs (local only)

Combiner benchmark output roots live under:

`src/combiner/results/benchmarks/layer2_qqq_2025_recent_cache_benchmark/{cache_off,cache_on_cold,cache_on_warm}/`

These are **not** intended to be committed. Only curated comparison + summary under `src/research/results/` should be committed.

## Comparisons

Compare across the three modes:

- `top_unique_systems.csv` (top row equality + tolerance)
- `behavior_unique_systems.csv` (top row equality + tolerance, if present)
- `cost_stress/cost_stress_results.csv` (rows by slip)
- precompute profile summary: cache hits/misses and precompute time deltas
- FeatureStore stats: requests/hits/misses

## Pass criteria

- Key outputs match within small numeric tolerance (\(\le 10^{-6}\) for floats).
- Warm run shows high signal-cache hit rate and reduced precompute time relative to cold/off.

