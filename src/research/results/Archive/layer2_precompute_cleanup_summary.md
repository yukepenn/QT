# Layer 2 precompute cleanup — summary

## 1. Purpose

Improve Layer 2 precompute **correctness** (context cache semantics), **performance** (strategy instance reuse, better context reuse), **observability** (profile + grouped summary), and **module boundaries** — without changing strategy signals, Layer 1 grids, or Layer 2 sweep grids. Layer 3 remains out of scope.

## 2. Files changed

| Area | Files |
|------|--------|
| New | `src/combiner/precompute.py`, `src/combiner/diagnostics.py` |
| Split / slim | `src/combiner/candidate.py` |
| Imports | `src/combiner/run.py`, `src/combiner/sweep.py`, `src/combiner/postprocess.py` |
| Tests | `tests/test_combiner_precompute_cache_key.py`, `tests/test_combiner_precompute_profile.py`, `tests/test_combiner_module_boundaries.py` |
| Docs | `README.md`, `PROGRESS.md`, `CHANGES.md`, `layer2_precompute_cleanup_plan.md` (this folder) |

## 3. Behavior-preserving changes

- Signal generation paths unchanged: same `prepare_signal_context` → `generate_signal_arrays_from_context` flow.
- **Equivalence check** (QQQ, `trap_family`, top 1 per strategy, 2025-01-01 → 2026-04-30): **329** trades, **total_r ≈ 66.329**, **profit_factor ≈ 1.479**, **max_drawdown_r ≈ -14.103** — matches the recent-check reference run within floating noise.

## 4. Context cache key fix

- **Before:** `(feature_key, str(params_hash))` — treated distinct candidates with identical signal context as different buckets; inconsistent with Layer 1’s use of `strategy.context_key(cfg)`.
- **After:** `build_context_cache_key(strategy, feature_key_from_config(cfg), strat.context_key(cfg))` — hashable tuple with nested structures normalized; **strategy** prefix prevents cross-strategy collisions in multi-strategy precompute.
- **Profile:** `params_hash_short` retained per row for traceability; `feature_key_short` and `strategy_context_key_short` are short SHA256 digests of the respective key material.

## 5. Module split

- **`candidate.py`:** `Candidate`, YAML load/select/universe/metadata/rules/filtering only; lazy `__getattr__` re-exports for backward-compatible `from src.combiner.candidate import precompute_candidate_signal_matrices` etc.
- **`precompute.py`:** `CandidateSignalMatrix`, caches, `precompute_candidate_signal_matrices`, `build_candidate_signal_arrays`, profile CSV + `write_precompute_profile_summary`.
- **`diagnostics.py`:** `write_candidate_diagnostics` (overlap / conflict / signal summary CSVs).

## 6. Precompute profile summary

- **Outputs:** beside `candidate_precompute_profile.csv`: `candidate_precompute_profile_summary.csv` and `candidate_precompute_profile_summary.md`.
- **Group by:** `strategy`, `feature_key_short`, `strategy_context_key_short`.
- **Metrics:** candidate count, feature/context hit & miss counts, `sum`/`mean`/`max` of `total_sec`, optional sums for feature/context/signal seconds (blank when no data), total signal counts.

## 7. Tests run

- `python -m pytest -q` — **78** passed (includes new combiner tests).
- Targeted: `test_combiner_precompute_cache_key.py`, `test_combiner_precompute_profile.py`, `test_combiner_module_boundaries.py`.

## 8. Smoke results

- `read_bars` QQQ Jan 2025 — OK.
- `check_strategy_fast_parity.py` failed_orb — **0** meaningful mismatches.
- `run.py --diagnostics-only` (trap_family, Jan 2025) — exit 0; profile + summary + diagnostics CSVs written (smoke output dir removed after validation).
- `run.py --no-save` same window — exit 0.
- **Limited sweep:** `sweep.py` has no `--max-combos`; full recent-check grid is **2688** combos — **not** run in this phase; precompute path validated via diagnostics + equivalence run.

## 9. Known follow-ups

1. Persistent candidate signal cache (disk).
2. FeatureStore / shared feature artifacts.
3. Active vs archive cleanup for configs/results.
4. Layer 3 smoke only after the above and user approval.
