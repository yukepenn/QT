# Layer 2 strict — QQQ 2020–2026 post-hardening v1

In-sample; **not live-ready.**

## 1. Executive summary

Strict Layer 2 on **27** Layer 1 YAMLs resolves to **15** warning-free candidates for sweep precompute. The **1440-combo** sweep favors **`opening_family`** with **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`** (`top_per_strategy=1`). Cost stress: **`robust_positive_at_0_02`** on rank-1; **not** robust at **0.03**.

## 2. Candidate universe

- Library: `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates/`
- **Sweep precompute:** **15** candidates (strict sets exclude warning-tagged ORB/VWAP exports).

## 3. Diagnostics

- Folder: `diagnostics/`
- **`candidate_precompute_profile.csv`:** per-candidate timings (diagnostics run).
- Signal summary + overlap/conflict CSVs for the **15** active strict candidates.

## 4. Fixed runs

Tags in `fixed_run_summary.csv` / `fixed_run_summary.md`:

| Tag | Family | n_cand | Trades | total_r | PF |
|-----|--------|--------|--------|---------|-----|
| strict_2020_fixed_trap_top1 | trap_family | 3 | 1285 | 40.89 | 1.114 |
| strict_2020_fixed_trap_top5 | trap_family | 15 | 1294 | 36.17 | 1.107 |
| strict_2020_fixed_opening_top5 | opening_family | 10 | 1019 | 41.73 | 1.123 |
| strict_2020_fixed_core5_no_vwap_top5 | core5_no_vwap | 15 | 1294 | 36.17 | 1.107 |
| strict_2020_fixed_strict_core_top5 | strict_core | 15 | 1294 | 36.17 | 1.107 |
| strict_2020_fixed_all_strict_top5 | all_strict | 15 | 1294 | 36.17 | 1.107 |

(`strict_core` equals trap+gap+prior here because warning candidates are excluded.)

## 5. Full sweep

- **Folder:** `sweep_20260506_005804_sweep_strict_2020_posthardening/`
- **Combos:** 1440
- **Precompute:** ~**30.8 s** (15 candidates)
- **Sweep loop:** ~**166.6 s**

## 6. Top config-unique systems

See `top_unique_systems.csv` / `.md`. Rank **1**: **`opening_family`**, **`top_per_strategy=1`**, **`max_trades_per_day=1`**, **`daily_max_loss_r=-1.5`**, pair **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`**, **986** trades, **`combiner_score≈-3.50`**, **`total_r=42.32`**.

## 7. Top behavior-unique systems

`behavior_unique_systems.csv`: **1** unique behavior in the top-100 config scan — same **`opening_family`** pair as rank-1 config unique.

## 8. Cost stress

`cost_stress/cost_stress_summary.md` for top unique ranks: **`total_r`** **54.3 → 42.3 → 20.4 → -6.2** across slip **0.005 / 0.01 / 0.02 / 0.03**.

## 9. Cost-robust systems

`cost_robust_systems.csv` lists systems passing the **0.02** slip replay and trade-count floor (see file for full rows).

## 10. Fixed vs sweep comparison

`sweep` **opening_family top1** edges **fixed opening top5** on **`total_r`** (42.32 vs 41.73) with fewer trades — see `fixed_vs_sweep_comparison.csv`.

## 11. Period breakdown observations

Generated under `fixed_runs/*/period_breakdown*.csv` (large; git-ignored paths) — inspect locally.

## 12. Research conclusion

Opening **failed_orb + gap** pair is the stable strict narrative; combiner **score remains negative** (research-only objective). Cost stress shows **limited** headroom past **0.02** slip.

## 13. Layer 3 smoke

**Defer.** Baseline combiner score is negative; cost stress turns negative by **0.03**. No Layer 3 commands were run.
