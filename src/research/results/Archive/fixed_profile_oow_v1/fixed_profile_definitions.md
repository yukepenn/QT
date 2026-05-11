# Fixed profile definitions (OOW v1)

All profiles use:

- `candidate_root`: `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- `commission_per_trade`: 0.0  
- `slippage_per_share`: 0.01  
- `max_open_positions`: 1  
- `eod_exit_minute`: 389  
- `no_new_after_minute`: 360  
- `recompute_target_from_entry`: true  
- `min_risk_per_share`: 0.03  
- `cooldown_scope`: session  
- `priority_policy`: metadata_priority  

Machine-readable table: `fixed_profile_definitions.csv`.

Expected **2023–2024** economics in `fixed_profile_definitions.csv`: VWAP rows match Global L2–style references; **indicator** rows are **anchored to this combiner replay** (Numba path, `top_per_strategy=3`) — legacy v1.5 headline R figures are **not** reproduced at the same total R (trade counts align); see `insample_sanity/insample_sanity_failure.md`.
