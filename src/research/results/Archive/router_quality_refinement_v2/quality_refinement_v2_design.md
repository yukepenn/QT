# quality_refinement_v2_design

## Principles

- v1 **A-only** buckets were too sparse; fixed cutoffs (e.g. 75) are not stable across profiles without calibration.
- v2 tests **multiple score variants** and **threshold schemes**, including **percentile** and **bottom-cut** filters.
- Any percentile/bottom-cut threshold computed on the **same panel** used for evaluation is explicitly flagged **`IN_SAMPLE_DIAGNOSTIC`** in `quality_v2_refined/quality_variant_results.csv`.

## Score variants

1. `original_v2_score` — same composite as v1 diagnostics.
2. `no_signal_strength_fallback` — removes signal-strength weight; redistributes to regime/level.
3. `regime_level_cost_only` — regime + level + cost only.
4. `freshness_penalty_light` — lighter penalty after prior loss.
5. `repeat_after_loss_penalty_only` — freshness channel only (ranking diagnostic).
6. `context_fit_plus_cost` — regime fit + cost safety.
7. `profile_percentile_score` — percentile rank of `original_v2_score` within `profile_id` (0..100).

## Threshold schemes

- **fixed_AB:** A ≥ 75, B ∈ [55, 75)  ⟹ effectively keep scores ≥ 55 (C removed)
- **relaxed_AB:** A ≥ 65, B ∈ [45, 65) ⟹ effectively keep scores ≥ 45
- **percentile_profile_top{80,70,50}:** per `profile_id` keep top N% by score
- **percentile_profile_window_top{80,70}:** per (`profile_id`, `window`)
- **bottom_cut_{10,20,30}:** per `profile_id` remove bottom {10,20,30}% by score

## CSV mirror

- Detailed rows: `quality_refinement_v2_design.csv`
