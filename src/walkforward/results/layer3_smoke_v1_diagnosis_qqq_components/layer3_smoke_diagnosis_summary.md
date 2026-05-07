# Layer 3 smoke — component diagnosis

**Not** full walk-forward. **Not** parameter optimization. **Not** live-ready. Explains Layer 3 smoke v1 patterns via fixed diagnostic systems.

## Component singles

            system_id  total_trades  stitched_total_r  mean_fold_pf  mean_fold_pf_r  positive_fold_count  worst_fold_r  fold_concentration  cost_0_02_survives  cost_0_03_survives
   recent_failed_only           558         32.000748      1.113842        1.071568                    1    -11.574859            0.727702                True               False
      recent_gap_only           164         15.383375      1.317442        1.161326                    2     -0.888572            0.724651                True                True
recent_prior_day_only           184          9.114162      1.083617        1.119655                    2     -7.628354            0.572488                True                True
 fullhist_failed_only           399         22.547872      1.139448        1.114065                    2     -7.838664            0.499867                True                True
    fullhist_gap_only           218         21.308008      1.452735        1.232487                    3      1.306924            0.573112                True                True

## Incremental comparisons

             base_system           variant_system                              comparison_note  delta_total_r  delta_worst_fold_r  delta_positive_fold_count  delta_fold_concentration  delta_trades                                                                                            interpretation
      recent_failed_only   recent_failed_gap_mtd1           add gap to failed ORB (pair, mtd1)       6.451052           -2.687239                        1.0                 -0.015216          53.0 stitched_total_r +6.4511; Δpositive_folds=+1; Δconcentration=-0.0152 — add gap to failed ORB (pair, mtd1)
         recent_gap_only   recent_failed_gap_mtd1           add failed ORB to gap (pair, mtd1)      23.068426          -13.373527                        0.0                 -0.012165         447.0                    stitched_total_r +23.0684; Δconcentration=-0.0122 — add failed ORB to gap (pair, mtd1)
  recent_failed_gap_mtd1    recent_trap_trio_mtd1             add PRIOR_DAY_LEVEL_TRAP to pair       8.956921            3.206251                        0.0                  0.033039          33.0                       stitched_total_r +8.9569; Δconcentration=+0.0330 — add PRIOR_DAY_LEVEL_TRAP to pair
   recent_trap_trio_mtd1    recent_trap_trio_mtd2               allow 2nd trade per day (trio)      -6.802138           -3.895359                       -1.0                 -0.037303         159.0     stitched_total_r -6.8021; Δpositive_folds=-1; Δconcentration=-0.0373 — allow 2nd trade per day (trio)
   recent_trap_trio_mtd2 recent_opening_full_mtd2 add ORB continuation + retest (full opening)      -4.754874          -10.113052                        1.0                 -0.007938         278.0               stitched_total_r -4.7549; Δpositive_folds=+1 — add ORB continuation + retest (full opening)
    fullhist_failed_only fullhist_failed_gap_mtd1            add gap to failed ORB (full-hist)      -2.796078            1.643057                        0.0                  0.072582         109.0                      stitched_total_r -2.7961; Δconcentration=+0.0726 — add gap to failed ORB (full-hist)
       fullhist_gap_only fullhist_failed_gap_mtd1            add failed ORB to gap (full-hist)      -1.556214           -7.502531                       -1.0                 -0.000663         290.0                          stitched_total_r -1.5562; Δpositive_folds=-1 — add failed ORB to gap (full-hist)
fullhist_failed_gap_mtd1 fullhist_failed_gap_mtd2             allow 2nd trade (full-hist pair)       1.939191           -0.982274                        0.0                 -0.108198          33.0                       stitched_total_r +1.9392; Δconcentration=-0.1082 — allow 2nd trade (full-hist pair)

## Max trades per day (mtd1 vs mtd2)

             mtd1_system              mtd2_system               family  delta_total_r  delta_worst_fold_r  delta_fold_concentration  delta_trades  mtd2_helps_headline_r  mtd2_increases_concentration
  recent_failed_gap_mtd1   recent_failed_gap_mtd2    failed+gap recent      -4.356362           -0.273979                  0.026974          57.0                  False                          True
   recent_trap_trio_mtd1    recent_trap_trio_mtd2     trap trio recent      -6.802138           -3.895359                 -0.037303         159.0                  False                         False
recent_opening_full_mtd1 recent_opening_full_mtd2  full opening recent      -6.597652          -18.159200                  0.136683         311.0                  False                          True
fullhist_failed_gap_mtd1 fullhist_failed_gap_mtd2 failed+gap full-hist       1.939191           -0.982274                 -0.108198          33.0                   True                         False

## Recent vs full-history candidate roots

         recent_system          fullhist_system  delta_total_r_recent_minus_full  delta_fold_concentration_recent_minus_full  delta_positive_fold_count_recent_minus_full                                        interpretation
    recent_failed_only     fullhist_failed_only                         9.452877                                    0.227836                                         -1.0    recent higher stitched R; recent more concentrated
       recent_gap_only        fullhist_gap_only                        -5.924633                                    0.151539                                         -1.0 full-hist higher stitched R; recent more concentrated
recent_failed_gap_mtd1 fullhist_failed_gap_mtd1                        18.700007                                    0.140037                                          0.0    recent higher stitched R; recent more concentrated
recent_failed_gap_mtd2 fullhist_failed_gap_mtd2                        12.404454                                    0.275209                                         -1.0    recent higher stitched R; recent more concentrated

## Fold heatmap

                     system_id  y2023_total_r  y2023_pf_r  y2024_total_r  y2024_pf_r  recent_total_r  recent_pf_r  positive_fold_count
      fullhist_failed_gap_mtd1      18.400223    1.248115      -6.195607    0.922324        7.547178     1.077334                    2
      fullhist_failed_gap_mtd2      16.734728    1.211269      -7.177881    0.914864       12.134138     1.117822                    2
          fullhist_failed_only      11.279036    1.210026      -7.838664    0.875698       19.107499     1.256471                    2
             fullhist_gap_only      12.211874    1.372701       7.789210    1.296039        1.306924     1.028720                    3
        recent_failed_gap_mtd1       4.994427    1.044534     -14.262099    0.880359       47.719472     1.341490                    2
        recent_failed_gap_mtd2      -4.012349    0.968282     -14.536077    0.889348       52.643865     1.348885                    1
            recent_failed_only      -7.559205    0.929790     -11.574859    0.894913       51.134813     1.390002                    1
               recent_gap_only       3.836553    1.148008      -0.888572    0.966200       12.435394     1.369770                    2
      recent_opening_full_mtd1      17.646506    1.134622      -6.905058    0.951543       31.707914     1.184459                    2
      recent_opening_full_mtd2       0.705398    1.003644     -25.064258    0.877501       60.210570     1.261783                    2
recent_opening_no_continuation     -12.924995    0.925005     -30.154607    0.840240       67.491244     1.344348                    1
      recent_opening_no_retest       0.831405    1.004385     -17.713452    0.910306       60.382701     1.266093                    2
         recent_prior_day_only      -7.628354    0.777977       2.790480    1.097123       13.952037     1.483865                    2
         recent_trap_trio_mtd1       6.635351    1.056099     -11.055848    0.909821       51.829218     1.363007                    2
         recent_trap_trio_mtd2     -14.951207    0.904023     -13.499487    0.911182       69.057277     1.409536                    1

## Diagnosis conclusion (heuristic, not live-ready)

This section summarizes patterns in the tables above. It does **not** justify live trading or guarantee future performance.

1. **Strongest single-component headline (stitched total R):** `recent_failed_only` (stitched_total_r≈32.0007).

2. **Largest combined 2023+2024 drag (among singles):** `recent_failed_only` (y2023_total_r + y2024_total_r ≈ -19.1341).

3. **PRIOR_DAY_LEVEL_TRAP:** Compare `recent_trap_trio_mtd1` vs `recent_failed_gap_mtd1` in **incremental_table** — positive `delta_total_r` suggests the trap adds headline R; check **fold_heatmap** `recent_total_r` vs `y2023_total_r`/`y2024_total_r` for robustness vs recent-window upside.

4. **ORB_CONTINUATION / ORB_RETEST:** Compare `recent_opening_no_retest` vs `recent_opening_no_continuation` and vs `recent_opening_full_mtd2` in **fold_heatmap** — look for improved early-fold R without exploding concentration.

5. **max_trades_per_day=2:** See **max_trades_sensitivity** — `mtd2_helps_headline_r` and `mtd2_increases_concentration`; cross-check **fold_heatmap** `recent_total_r` vs older folds for the same system family.

6. **Recent vs full-history candidates:** See **recent_vs_fullhistory** — negative `delta_fold_concentration_recent_minus_full` suggests full-hist paths are less single-fold dependent (not automatically better PnL).

### Mini-WFO readiness (decision support only)

- If **fullhist_failed_gap** pairs show more stable early folds and acceptable cost flags vs recent singles, a **narrow causal mini-WFO** could focus on **failed_orb + gap_acceptance** with **max_trades_per_day=1** first.
- If concentration remains extreme or mtd2 consistently worsens early folds, prefer **Layer 1 strategy-family work** before any mini-WFO.

