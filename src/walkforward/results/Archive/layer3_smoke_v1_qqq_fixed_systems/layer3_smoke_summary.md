# Layer 3 Smoke v1 — QQQ Fixed Systems

## 1. Purpose

Fixed-system **temporal-stability smoke** over calendar segments. **Not** full walk-forward. **Not** a profitability claim. **Not** live-ready.

## 2. Systems tested

- `trap_recent_top1` (frozen: `qqq_trap_family_recent_top1`)
- `opening_recent_top1` (frozen: `qqq_opening_family_recent_top1`)
- `full_history_opening_pair` (frozen: `qqq_full_history_opening_pair`)

## 3. Fold definitions

- **y2023**: 2023-01-01 → 2023-12-31 (calendar_2023)
- **y2024**: 2024-01-01 → 2024-12-31 (calendar_2024)
- **recent_2025_202604**: 2025-01-01 → 2026-04-30 (recent_2025_202604)

## 4. Validation status

- Runner tag: `layer3_smoke_v1_qqq_fixed_systems`
- Signal cache: **on** (root chosen at run time; default `.cache/qt/candidate_signals` or CLI `--signal-cache-root`).

## 5. System-level results

                system_id  fold_count  positive_fold_count  total_trades  stitched_total_r  stitched_pf  stitched_pf_r  median_fold_r  worst_fold_r  best_fold_r  positive_fold_rate  fold_concentration  slip_0_02_total_r_mean  slip_0_02_pf_mean  slip_0_03_total_r_mean  slip_0_03_pf_mean  stitched_max_drawdown_r  positive_total_r  pf_above_1  pf_r_above_1  cost_0_02_survives  cost_0_03_survives  drawdown_exceeds_insample  single_fold_dependency  trade_2_positive
full_history_opening_pair           3                    2           508         19.751794     1.210453       1.082591       7.547178     -6.195607    18.400223            0.666667            0.572449                2.237485           1.164780               -0.580719           1.130594               -18.994331              True        True          True                True               False                      False                   False             False
      opening_recent_top1           3                    2          1081         35.851710     1.099783       1.047643       0.705398    -25.064258    60.210570            0.666667            0.700284                0.819535           1.054151              -12.772878           1.004091               -33.511436              True        True          True                True               False                      False                    True             False
         trap_recent_top1           3                    1           803         40.606584     1.130084       1.074914     -13.499487    -14.951207    69.057277            0.333333            0.708222                4.496445           1.083857               -4.198471           1.041417               -36.621979              True        True          True                True               False                      False                    True             False

## 6. Fold-level results

                system_id               frozen_system_id            fold_id         fold_label test_start   test_end  trades    total_r  profit_factor  profit_factor_r  max_drawdown_r  avg_cost_r  median_cost_r  trade_1_total_r  trade_2_total_r  slip_0_02_total_r  slip_0_02_pf  slip_0_03_total_r  slip_0_03_pf  trade_2_positive  positive_total_r  pf_above_1  pf_r_above_1  cost_0_02_survives  cost_0_03_survives  drawdown_exceeds_insample                                                                                                         output_dir
         trap_recent_top1    qqq_trap_family_recent_top1              y2023      calendar_2023 2023-01-01 2023-12-31     243 -14.951207       0.973103         0.904023      -36.621979    0.044575       0.035714         6.635351       -21.586558         -28.426731      0.896725         -43.024386      0.823732             False             False       False         False               False               False                      False                       src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_trap_recent_top1/fold_y2023
         trap_recent_top1    qqq_trap_family_recent_top1              y2024      calendar_2024 2024-01-01 2024-12-31     237 -13.499487       0.900844         0.911182      -24.645760    0.036201       0.029851       -11.055848        -2.443639         -19.309201      0.872565         -26.462007      0.842749             False             False       False         False               False               False                      False                       src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_trap_recent_top1/fold_y2024
         trap_recent_top1    qqq_trap_family_recent_top1 recent_2025_202604 recent_2025_202604 2025-01-01 2026-04-30     323  69.057277       1.516306         1.409536      -12.082487    0.027123       0.021053        51.829218        17.228060          61.225265      1.482280          56.890979      1.457771              True              True        True          True                True                True                      False          src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_trap_recent_top1/fold_recent_2025_202604
      opening_recent_top1 qqq_opening_family_recent_top1              y2023      calendar_2023 2023-01-01 2023-12-31     327   0.705398       1.033118         1.003644      -16.665281    0.040685       0.034188        17.646506       -16.941108         -15.174356      0.956000         -40.682399      0.857041             False              True        True          True               False               False                      False                    src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_opening_recent_top1/fold_y2023
      opening_recent_top1 qqq_opening_family_recent_top1              y2024      calendar_2024 2024-01-01 2024-12-31     326 -25.064258       0.913366         0.877501      -33.511436    0.035465       0.030303        -6.905058       -18.159200         -31.290289      0.889707         -39.821260      0.860435             False             False       False         False               False               False                      False                    src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_opening_recent_top1/fold_y2024
      opening_recent_top1 qqq_opening_family_recent_top1 recent_2025_202604 recent_2025_202604 2025-01-01 2026-04-30     428  60.210570       1.352865         1.261783      -17.443168    0.025943       0.021053        31.707914        28.502656          48.923252      1.316746          42.185026      1.294797              True              True        True          True                True                True                      False       src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_opening_recent_top1/fold_recent_2025_202604
full_history_opening_pair  qqq_full_history_opening_pair              y2023      calendar_2023 2023-01-01 2023-12-31     158  18.400223       1.326262         1.248115       -7.402050    0.027829       0.024541        18.400223              NaN          12.453295      1.257921           9.149181      1.213356             False              True        True          True                True                True                      False              src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_full_history_opening_pair/fold_y2023
full_history_opening_pair  qqq_full_history_opening_pair              y2024      calendar_2024 2024-01-01 2024-12-31     146  -6.195607       1.159394         0.922324      -18.994331    0.024967       0.022989        -6.195607              NaN         -10.561012      1.113598         -12.810168      1.082585             False             False        True         False               False               False                      False              src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_full_history_opening_pair/fold_y2024
full_history_opening_pair  qqq_full_history_opening_pair recent_2025_202604 recent_2025_202604 2025-01-01 2026-04-30     204   7.547178       1.145703         1.077334      -18.888195    0.017283       0.015326         7.547178              NaN           4.820172      1.122821           1.918831      1.095841             False              True        True          True                True                True                      False src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/system_full_history_opening_pair/fold_recent_2025_202604

## 7. Cost stress (0.02 / 0.03 slippage per share)

Stress rows use the same frozen candidates and combiner rules as the base run; only `slippage_per_share` changes. See per-fold `cost_stress.csv` and rollup `cost_stress_by_fold.csv`.

                system_id  slip_0_02_total_r_mean  slip_0_02_pf_mean  slip_0_03_total_r_mean  slip_0_03_pf_mean  cost_0_02_survives  cost_0_03_survives
full_history_opening_pair                2.237485           1.164780               -0.580719           1.130594                True               False
      opening_recent_top1                0.819535           1.054151              -12.772878           1.004091                True               False
         trap_recent_top1                4.496445           1.083857               -4.198471           1.041417                True               False

**Read:** At the stitched level, `cost_0_03_survives` is **False** for every system in this run — treat 0.03/share as a harsh lens, not an automatic veto on further research.

## 8. Monthly / quarterly concentration

Detailed cadence is in `monthly_breakdown_all.csv` (concatenated per-fold monthly breakdowns). Use it to see whether positive stitched R is concentrated in a small number of months.

## 9. Daily trade number profile (trade #1 vs trade #2)

Where `max_trades_per_day` allows a second trade, fold-level columns `trade_1_total_r` and `trade_2_total_r` split contribution. See `daily_trade_number_by_fold.csv` and each fold’s `daily_trade_number_breakdown.csv`.

          system_id            fold_id  trade_1_total_r  trade_2_total_r  trade_2_positive
   trap_recent_top1              y2023         6.635351       -21.586558             False
   trap_recent_top1              y2024       -11.055848        -2.443639             False
   trap_recent_top1 recent_2025_202604        51.829218        17.228060              True
opening_recent_top1              y2023        17.646506       -16.941108             False
opening_recent_top1              y2024        -6.905058       -18.159200             False
opening_recent_top1 recent_2025_202604        31.707914        28.502656              True

**Read:** **trap_recent_top1** / **y2023** shows trade #2 total R (-21.5866) far below trade #1 (6.6354) — the second intraday slot can dominate negatively in hostile regimes. **full_history_opening_pair** uses `max_trades_per_day: 1` only — no trade #2 bucket.

## 10. Interpretation flags (system rollup)

                system_id  positive_total_r  pf_above_1  pf_r_above_1  cost_0_02_survives  cost_0_03_survives  drawdown_exceeds_insample  single_fold_dependency  trade_2_positive  positive_fold_rate  fold_concentration
full_history_opening_pair              True        True          True                True               False                      False                   False             False            0.666667            0.572449
      opening_recent_top1              True        True          True                True               False                      False                    True             False            0.666667            0.700284
         trap_recent_top1              True        True          True                True               False                      False                    True             False            0.333333            0.708222

## 11. Decision gate (smoke only)

**Overall:** Caution — at least one system is **Fail**-tier on this smoke heuristic (often single-fold reliance).

- `full_history_opening_pair`: **Pass**
- `opening_recent_top1`: **Caution**
- `trap_recent_top1`: **Fail**

**Heuristic (not a trading signal):** **Fail**-like behavior includes mostly negative folds plus clear reliance on one segment. **Caution** covers mixed years, single-fold dominance (`single_fold_dependency`), or failure of stitched 0.03 stress (`cost_0_03_survives`). **Pass** would require most folds positive or near-flat, `pf_r_above_1`, 0.02 survival, and no extreme concentration — rarely met on first smoke.

## 12. Recommended next step

- **Do not** jump to a full rolling walk-forward or broaden grids based on this smoke alone.
- Prefer **strategy-family diagnosis** (why 2023/2024 differ from the recent segment) unless you explicitly approve a narrow **causal mini-WFO** (e.g. train 2023-01-01→2024-12-31, test 2025-01-01→2026-04-30) as a separate, labeled experiment.

