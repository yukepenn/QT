# Layer 2 precompute cleanup — internal plan

## 1. Current `candidate.py` responsibilities (before split)

- Candidate YAML loading, `Candidate` dataclass, `merged_strategy_config`
- Candidate-set selection (`select_candidate_set`, `resolve_candidate_universe_for_grid`)
- Metadata encoding for Numba (`encode_candidate_metadata`), `build_enabled_mask`, `write_candidates_used`
- **Signal precompute**: `precompute_candidate_signal_matrices`, `CandidateSignalMatrix`, `build_candidate_signal_arrays`
- Feature cache keyed by `feature_key_from_config`; **context cache** was `(fk, params_hash)` — **replaced** by `(strategy, fk, normalized context_key(cfg))` in `precompute.py`
- **Diagnostics**: overlap/conflict CSVs (`write_candidate_diagnostics`, `_min_abs_diff_two_sorted_minutes`)
- Combiner rule helpers: `apply_combiner_rules`, `filter_candidates`

## 2. Keep in `candidate.py`

- `Candidate` / `CandidateSpec`, `load_candidate_yaml`, `load_candidates`
- `merged_strategy_config`, `_finalize_entry_start`, `_rank_from_candidate_id`
- `select_candidate_set`, `resolve_candidate_universe_for_grid`
- `build_enabled_mask`, `write_candidates_used`, `encode_candidate_metadata`
- `apply_combiner_rules`, `filter_candidates`
- Re-exports of moved public API for backward compatibility

## 3. Move to `precompute.py`

- `CandidateSignalMatrix`
- `normalize_for_context_cache_key`, `build_context_cache_key`
- `precompute_candidate_signal_matrices` (strategy instance cache, fixed context key, profile rows)
- `write_precompute_profile_summary` → `candidate_precompute_profile_summary.csv` / `.md`
- `build_candidate_signal_arrays`

## 4. Move to `diagnostics.py`

- `_min_abs_diff_two_sorted_minutes`
- `write_candidate_diagnostics`

## 5. Import compatibility

- `run.py`, `sweep.py`, `postprocess.py`: import `precompute_candidate_signal_matrices` from `src.combiner.precompute`; `write_candidate_diagnostics` from `src.combiner.diagnostics`
- `candidate.py`: lazy `__getattr__` re-exports (no import-time cycle with `precompute`)

## 6. Tests to add

- `test_combiner_precompute_cache_key.py` — hashable key, strategy isolation, risk-only vs context-driving params
- `test_combiner_precompute_profile.py` — summary aggregation, missing optional columns
- `test_combiner_module_boundaries.py` — imports / re-exports

## 7. Smoke commands

- `pytest -q`
- `run.py --diagnostics-only` on `trap_family` Jan 2025 → `_smoke_layer2_precompute_cleanup`
- `run.py --detailed` trap_family top=1 full 2025 window → equivalence vs prior metrics; delete output dirs
- `read_bars` + `check_strategy_fast_parity` (failed_orb)
