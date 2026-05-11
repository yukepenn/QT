# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Prior tip (pre–feature-perf work) | `6555ee8` — `Design global Layer 1 and Layer 2` |
| New commit | `51bfe17` — **Optimize feature construction performance** |
| Push status | **Pushed** to `origin/main` |
| Working tree | Clean post-commit; **`src/strategies/testing_parameters_results/**`** `sweep_*_feature_perf_smoke` remains **local-only** (do not stage) |

## B. Task scope

| | |
|--|--|
| Requested | Feature performance hardening: batch-concat refactors, benchmarks, snapshots, equivalence tests, summary + Numba design doc; **no** behavior / formula / column / `feature_key` changes |
| Completed | `volume.py`, `volatility.py`, `vwap.py`, `price_action.py`, `orb.py`, `levels.py`; `feature_build_benchmark.py`, `feature_output_snapshot.py`; `feature_build_performance_v1/{before,after}/`, `feature_output_snapshot_{before,after}/`, `feature_performance_hardening_summary.md`, `feature_numba_fastpath_design.md`; `tests/test_feature_performance_equivalence.py`; docs/indexes |
| Intentionally not done | **Global Layer 1 / Global Layer 2** rerun; **mini-WFO / full WFO / live**; deep Numba rolling kernels (design only in `feature_numba_fastpath_design.md`); `indicators` / `channels` / `regime` / `pa_swings` refactors |

## C. Files changed

| Area | Paths |
|------|-------|
| Features | `src/features/volume.py`, `volatility.py`, `vwap.py`, `price_action.py`, `orb.py`, `levels.py` |
| Research scripts | `src/research/feature_build_benchmark.py`, `feature_output_snapshot.py` |
| Tests | `tests/test_feature_performance_equivalence.py` |
| Results / docs | `src/research/results/feature_build_performance_v1/**`, `feature_output_snapshot_before/**`, `feature_output_snapshot_after/**`, `feature_numba_fastpath_design.md` |
| Root / indexes | `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`, `src/research/results/RESULTS_INDEX.md`, `tests/README.md` |

## D. Validation

| Check | Result |
|--------|--------|
| `pytest -q` | **374 passed** (363 + 11 new) |
| `compileall` | **OK** |
| `loader.py --list` | **35** strategies |
| Parity | **failed_orb**, **afternoon_continuation**, **pa_buy_sell_close_trend** tuned v3, **pa_climax_reversal** tuned v3 — `TOTAL_MISMATCH_FIELDS approx=0` |
| Sweep smoke | `afternoon_continuation` Jan 2025, `--max-combos 50`, tag `feature_perf_smoke` — `engine=numba_fast`, **no** fragmentation warnings in log; `feature_build≈0.64s` aggregate for 50 combos |
| Boundary greps | **OK** (see prior policy: `_feat_key` / `DfSignalStrategy` may appear in markdown under `src/research/results`) |
| Heavy `git ls-files` pattern | **No hits** |

## E. Performance / equality

- Benchmark CSVs: `feature_build_performance_v1/before/` vs `after/` — **fragmentation_warnings_count → 0** for configs that previously hit `volume`/`price_action` warnings; wall time improved on **`failed_orb`** / **`afternoon_continuation`** paths.
- Snapshot digests (`pa_buy_sell_close_trend`, Jan 2025 slice): **`columns_digest_sha256` identical** before vs after code change (before snapshot taken on pre-refactor `git checkout` files).

## F. Explicit non-runs

- Global Layer 1 / Global Layer 2 full reruns  
- mini-WFO, full WFO, live/paper  
- New strategies / new feature primitives  

## G. Risks / caveats

- **`orb` / `levels`**: refactors are structural (concat) only; ORB known-safe columns unchanged in logic.
- **`regime` / `indicators` / `channels` / `pa_swings`**: still potential fragmentation or cost on very wide PA configs — addressed in Numba design doc as **P2/P3**.

## H. Recommended next step

**Exactly one:** **Re-run Global Layer 1** (QQQ 2023–2024 global manifest) after this merge to measure real `feature_build` share in `sweep.py` profiles — **not** another PA B/C v4 tuning pass unless Layer 1 still disappoints.
