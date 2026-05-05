# Layer 2 strict — QQQ post-hardening (2023-01-01 → 2026-04-30)

Result root: `src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/`  
Config: `src/combiner/configs/layer2_qqq_2023_20260430_posthardening_strict.yaml`  
Sweep: `sweep_20260505_232959_sweep_strict_2023_posthardening/` (tag `sweep_strict_2023_posthardening`)

## 1. Executive summary

Full strict pipeline completed: diagnostics, six fixed detailed runs, **1440**-combo sweep (~**328 s** total including ~**299 s** candidate precompute + ~**310 s** Numba sweep), postprocess dedupe (100), cost stress (10), behavior-unique (1 strong), rank CSVs, fixed-vs-sweep comparison. **Combiner_score** favors a sparse **`trap_family`** basket (three candidates, top-1 each). **Cost stress** keeps top configs positive through **0.03** $/share slip. This remains **in-sample research on 2023–2026 QQQ only** — not live-ready.

## 2. Candidate universe

From Layer 1: **39** YAMLs under `layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates/` (29 strict-eligible without relaxed warnings for non-VWAP strategies; diagnostics reported **29** candidates in strict `all_strict` diagnostics mode).

## 3. Diagnostics

`diagnostics/` — strict `all_strict`, top 5 per strategy: **29** candidates, **11 017** raw signals (see console summary). Postprocessed `diagnostics_summary.md` present.

## 4. Fixed runs

Six tags under `fixed_runs/`; aggregated **`fixed_run_summary.csv`** / **`.md`**.

| Tag | Candidate set | Trades | total_r | PF |
|-----|---------------|--------|---------|-----|
| strict_2023_fixed_trap_top1 | trap_family | 613 | 30.943 | 1.180 |
| strict_2023_fixed_all_strict_top5 | all_strict | 1409 | 36.912 | 1.110 |

## 5. Full sweep

- **Combos:** 1440 (grid as specified).
- **Precompute:** 39 candidates, ~299 s.
- **Sweep phase:** ~310 s (`total_elapsed_s=327.6` logged).

## 6. Top config-unique systems

See **`top_unique_systems.csv`** / **`top_unique_systems.md`**.

Representative rank **1:** `trap_family`, `top_per_strategy=1`, `max_trades_per_day=1`, `daily_max_loss_r=-1.5`, `cooldown=0`, `metadata_priority`, candidates `FAILED_ORB_001`, `GAP_ACCEPTANCE_FAILURE_001`, `PRIOR_DAY_LEVEL_TRAP_001` → **523 trades**, **total_r 30.181**, **PF 1.180**, **max_dd_r −17.218**, **combiner_score −1.385**.

Full sweep **max total_r** (not same as dedupe score): `rank_by_total_r.csv` combo **1273** — **total_r 74.813**, **1427 trades**, `all_strict`, `top_per_strategy=2`, `max_trades_per_day=3`.

## 7. Top behavior-unique systems

**`behavior_unique_systems.csv`:** **1** row (strong hash). Same economics as config rank 1; **all trades** daily slot **1**. Dedupe stats: 15 / 100 rows had trades for hashing; 85 missing detailed paths.

## 8. Cost stress

`cost_stress/cost_stress_summary.md` — top unique ranks carry **`robust_positive_at_0_03`**: at **0.010** slip baseline total_r **30.181**; at **0.020** → **16.654**; at **0.030** → **2.505** (still positive).

## 9. Cost-robust systems

**`cost_robust_systems.csv`:** **10** rows (filter: min_trades **200**, slip **0.02**, min_total_r **0**, min_pf **1.0**, max_dd **−80**, max_median_cost_r **0.50**). First row aligns with trap_family rank 1 at stressed slip.

## 10. Fixed vs sweep comparison

See **`fixed_vs_sweep_comparison.md`**. Illustrative: fixed **all_strict** shows higher trade count than sparse sweep winner; sweep aligns **combiner_score** with trap_family top dedupe row.

## 11. Period breakdown observations

Monthly/quarterly CSVs written under `fixed_runs/run_*` and sweep `top_runs/` where detailed folders exist — use for regime review.

## 12. Research conclusion

On this window, **strict Layer 2** surfaces a **stable, sparse trap basket** with **favorable cost-stress labels**. Expanding to **all_strict** increases **total_r** but not **combiner_score** (different objective).

## 13. Further testing?

**Worth** a later **2020–2026** rerun and optional **Layer 3 smoke** only after long-window confirmation — **not** automatic from this shorter window alone.
