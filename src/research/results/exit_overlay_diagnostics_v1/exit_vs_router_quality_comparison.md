# Exit overlay vs router / quality v2

Headline rows are programmatic picks from:
- `router_v2/router_v2_results.csv` (best `ROUTER_V2_PROMISING` by `delta_pf_vs_baseline`)
- `quality_v2_refined/quality_variant_results.csv` (best `QUALITY_V2_PROMISING` with `in_sample_diagnostic=True`)
- `combined_light_guards/combined_guard_results.csv` (max `total_r` row — illustrative)
- Exit overlay: best `PF_R_overlay - PF_R_original` among non-baseline overlays, excluding `full_available` window slice.

| path | variant | profile_id | total_r | PF_R | maxDD_proxy | retention_pct | implementation_complexity | overfit_risk | data_quality_risk | next_step_priority | window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| router_v2_best_promising | late_climax_guard | pa_only_mtp1_meta | 221.1704074187924 | 1.2756139288321082 | -36.602263017684606 | 0.8208846990572879 | medium | high_without_oos | low | diagnostic_only | nan |
| quality_v2_best_in_sample_promising | context_fit_plus_cost|bottom_cut_30 | primary_mtp2_meta | 243.5104570727936 | 1.194595334481768 | -49.54885079838528 | 0.6988117001828154 | medium | high_in_sample | low | diagnostic_only | nan |
| combined_light_guard_top_row | best_router_v2 + bottom_20_quality_cut | pa_gap_mtp2_meta | 252.40456703535887 | 1.259761065775962 | -33.27865667085399 | 0.7012020606754437 | high_combo | medium_high | low | diagnostic_only | nan |
| exit_overlay_best_non_full_available_delta_pf | runner_after_1R_trail_vwap | pa_only_mtp1_meta | 86.06248284146508 | 1.4794788134701893 | -12.209681526443347 | 1.0 | medium_exit_engine | medium_path_sim | ambiguous_intrabar | see_decision_doc | insample_ref |

## Interpretation

Router/quality masks **drop or reweight trades**; exit overlays **keep the same entries** and only change exit paths.
They answer different questions — compare **implementation risk** (router metadata + retention) vs **path simulation risk** (intrabar ambiguity, bar coverage).
