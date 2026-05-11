# Tuned Layer 2 diagnostic preflight (Global L2 v2 cost/turnover)

**Date:** 2026-05-10  
**Candidate root:** `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates` — **66** YAMLs (verified by script).  
**Base config:** `src/combiner/configs/layer2_qqq_global_2023_2024_v2_cost_turnover.yaml`

## Checks

| Check | Result |
|--------|--------|
| Candidate root exists | Yes |
| YAML count | **66** |
| `long_short_mixed` / full 81 root | **Not used** |
| Candidate sets non-empty (resolved at `top_per_strategy=1`) | See JSON below |
| Expected combo counts | Track A **72**, B **64**, D **80** → **216** total |
| Output dirs (separate from full v2 sweep) | `.../layer2_qqq_global_2023_2024_v2_cost_turnover/{lower_turnover_vwap,family_diverse,non_vwap}/` |
| Signal cache | **Off** (CLI default) |

## `python -m src.combiner.analyze_layer2_cost_turnover --preflight` (excerpt)

```json
{
  "candidate_yaml_count": 66,
  "sweeps": {
    "layer2_sweep_qqq_global_2023_2024_v2_lower_turnover_vwap.yaml": {
      "combo_count": 72,
      "candidate_sets_in_grid": ["all_behavior_diverse", "all_low_turnover", "vwap_core"],
      "unknown_candidate_sets": [],
      "sample_nonempty_resolution": [
        "all_behavior_diverse@tps=1 n=17",
        "all_low_turnover@tps=1 n=11",
        "vwap_core@tps=1 n=2"
      ]
    },
    "layer2_sweep_qqq_global_2023_2024_v2_family_diverse.yaml": {
      "combo_count": 64,
      "candidate_sets_in_grid": [
        "behavior_diverse_no_vwap",
        "indicator_completion_core",
        "opening_trap_core",
        "pa_core"
      ],
      "unknown_candidate_sets": [],
      "sample_nonempty_resolution": [
        "behavior_diverse_no_vwap@tps=1 n=15",
        "indicator_completion_core@tps=1 n=5",
        "opening_trap_core@tps=1 n=3",
        "pa_core@tps=1 n=4"
      ]
    },
    "layer2_sweep_qqq_global_2023_2024_v2_non_vwap.yaml": {
      "combo_count": 80,
      "candidate_sets_in_grid": [
        "behavior_diverse_no_vwap",
        "indicator_completion_core",
        "non_vwap_strict_l2_core",
        "opening_trap_core",
        "pa_core"
      ],
      "unknown_candidate_sets": [],
      "sample_nonempty_resolution": [
        "behavior_diverse_no_vwap@tps=1 n=15",
        "indicator_completion_core@tps=1 n=5",
        "non_vwap_strict_l2_core@tps=1 n=15",
        "opening_trap_core@tps=1 n=3",
        "pa_core@tps=1 n=4"
      ]
    }
  }
}
```

**Preflight status:** **PASS** (all grid `candidate_set` keys resolve to non-empty selections).
