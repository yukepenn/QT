# Layer 2 relaxed — QQQ post-hardening (2023-01-01 → 2026-04-30)

Result root: `src/combiner/results/layer2_qqq_2023_20260430_posthardening_relaxed_v1/`  
Config: `src/combiner/configs/layer2_qqq_2023_20260430_posthardening_relaxed.yaml`  
Sweep: `sweep_20260505_234057_sweep_relaxed_2023_posthardening/` (tag `sweep_relaxed_2023_posthardening`)

## 1. Executive summary

Relaxed pipeline completed: diagnostics (`all_with_relaxed`), eight fixed runs, **3360**-combo sweep (~**393 s** wall; precompute ~**326 s**, sweep ~**378 s**), postprocess dedupe 100, cost stress 10, behavior-unique **2** strong hashes. **Combiner_score** leader is **`vwap_control_family`** (10 VWAP candidates). **Cost stress** labels top rows **`positive_but_sensitive`**; **`cost_robust_systems.csv` is empty** under the same thresholds used for strict — relaxed leaders fail combined cost/shape filters. Not live-ready.

## 2. Candidate universe

**39** YAMLs including relaxed-filter **vwap_reclaim_reject** and **vwap_trend_pullback** candidates.

## 3. Diagnostics

Relaxed diagnostics: **39** candidates, **14 398** signals (`all_with_relaxed`, top 5 per strategy).

## 4. Fixed runs

Eight tags (includes **`vwap_control_family`** and **`all_with_relaxed`**).

| Tag | Trades | total_r | PF |
|-----|--------|---------|-----|
| relaxed_2023_fixed_all_with_relaxed_top5 | 2210 | 102.587 | 1.121 |
| relaxed_2023_fixed_vwap_control_top5 | 813 | 38.561 | 1.031 |

## 5. Full sweep

- **Combos:** 3360.
- **Precompute:** ~326 s; **sweep:** ~378 s.

## 6. Top config-unique systems

Rank **1** (`combo_id` **2307**): **`vwap_control_family`**, `top_per_strategy=5`, `max_trades_per_day=2`, `daily_max_loss_r=-1.5`, cooldown **15** → **740 trades**, **total_r 47.479**, **PF 1.052**, **max_dd_r −19.609**, **combiner_score −0.331**.

Raw **max total_r** in sweep: `rank_by_total_r.csv` combo **3115** — **`all_with_relaxed`**, **2119 trades**, **total_r 112.787**, **max_dd_r −36.176**.

## 7. Top behavior-unique systems

**2** rows — both VWAP-control bundles (full 5+5 vs 3+3 subsets). Trade **2** of day contributes large share of R (see CSV JSON columns).

## 8. Cost stress

`positive_but_sensitive`: at **0.005** slip, total_r ~**76.5**; at **0.010** ~**47.5**; at **0.020** ~**−10.5**; at **0.030** ~**−61.8** (top rank block in `cost_stress_summary.md`).

## 9. Cost-robust systems

**`cost_robust_systems.csv`** — **no rows** (empty apart from header) at min_trades **200**, slip **0.02**, and companion thresholds.

## 10. Fixed vs sweep comparison

See **`fixed_vs_sweep_comparison.md`**. Broad **`all_with_relaxed`** fixed run dominates raw **total_r** vs score-ranked VWAP sweep row.

## 11. Period breakdown observations

See `fixed_runs/run_*` and sweep `top_runs/` for monthly/quarterly exports.

## 12. Research conclusion

Relaxed grid **elevates VWAP strategies** in combiner_score and raw R but **does not pass** the same **cost-robust** screen as strict trap systems. Treat as **positive_but_cost_sensitive** / **high_R_but_drawdown_heavy** for all-book configs (`all_with_relaxed`).

## 13. Further testing?

Use relaxed results to **stress-test VWAP plumbing**, not as primary production candidates until cost labels improve or execution assumptions change. **Defer Layer 3** pending long-window strict confirmation.
