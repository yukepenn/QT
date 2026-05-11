# Robust l2_core v2 diagnostic v1 — summary (curated)

- discovered rows: **168**
- discovered combos: **168**

## Top 10 rows overall (by total_r)

               candidate_set       window                  grid_id   total_r  trades     pf_r   max_dd_r         priority_policy  daily_max_loss_r  max_trades_per_day
balanced_representative_core insample_ref g_m2_d-1.5_pmetadata_pri 71.964120     725 1.250785  -9.812557       metadata_priority              -1.5                   2
balanced_representative_core insample_ref g_m2_d-1.5_pscore_adjust 71.964120     725 1.250785  -9.812557 score_adjusted_priority              -1.5                   2
balanced_representative_core insample_ref g_m2_d-2.0_pmetadata_pri 71.964120     725 1.250785  -9.812557       metadata_priority              -2.0                   2
balanced_representative_core insample_ref g_m2_d-2.0_pscore_adjust 71.964120     725 1.250785  -9.812557 score_adjusted_priority              -2.0                   2
 primary_representative_core insample_ref g_m2_d-1.5_pmetadata_pri 62.695867     694 1.235399 -14.906190       metadata_priority              -1.5                   2
 primary_representative_core insample_ref g_m2_d-1.5_pscore_adjust 62.695867     694 1.235399 -14.906190 score_adjusted_priority              -1.5                   2
 primary_representative_core insample_ref g_m2_d-2.0_pmetadata_pri 62.695867     694 1.235399 -14.906190       metadata_priority              -2.0                   2
 primary_representative_core    early_oow g_m2_d-2.0_pscore_adjust 61.329231    1024 1.150824 -21.257506 score_adjusted_priority              -2.0                   2
                 pa_gap_core    early_oow g_m2_d-1.5_pmetadata_pri 60.953499     818 1.191461 -13.555458       metadata_priority              -1.5                   2
                 pa_gap_core    early_oow g_m2_d-1.5_pscore_adjust 60.953499     818 1.191461 -13.555458 score_adjusted_priority              -1.5                   2

## Notes

- This is a *small* diagnostic grid (no broad Layer2).
- Raw runs live under `local_runs/**` and are local-only.
