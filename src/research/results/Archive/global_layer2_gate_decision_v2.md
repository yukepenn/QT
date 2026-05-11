# Global Layer 2 gate decision (v2)

## A. Full strict Layer 1 export (`layer1_global_qqq_2023_2024_v2/selected_candidates`)

| Check | Value |
|-------|-------|
| strict_candidate_yaml_count | **81** |
| distinct_families_in_strict_selected | **15** |
| duplicate_signal_group_rows | **22** |
| fast_context_exit_code | **0** |
| diversity_exit_code | **0** |

**Historical prerun rule:** strict YAML count must be ≤ **80** for the *legacy* automated gate used inside `run_global_layer1.py`.

**Result:** **NO** — 81 > 80 (same situation as v1; economics unchanged in expectation).

## B. Layer-2-ready core (`selected_candidates_l2_core`)

| Check | Value |
|-------|-------|
| rows in `selected_candidates.csv` | **66** (≤ 80) |
| distinct families | **15** (≥ 3) |
| distinct strategies | **17** |
| non-PA strategies present | **yes** (e.g. MACD, stochastic, VWAP reclaim) |
| strict short / both fingerprint (`n_short_signals` > 0) | **0** |
| fast-context (Jan 2023 smoke window) | **0** (all `ok`) |
| diversity script on l2_core | **0** |

**Manual Layer 2 input gate (l2_core):** **YES** — use this root for combiner configs in `layer2_qqq_global_2023_2024_v2.yaml`.

## C. Recommended action

- **Do not** block on the full-root 81-YAML automated flag when l2_core is available.
- **Proceed** with Layer 2 sweep using **l2_core** + emitted YAML; optional: raise or remove the 80-cap in code only after policy discussion.
