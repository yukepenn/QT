# Layer 2 relaxed — QQQ 2020–2026 post-hardening v1

In-sample; **not live-ready.**

## 1. Executive summary

Relaxed grid (**3360** combos) precomputes **all 27** candidates. Deduped leaders favor **`vwap_control_family`** (`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`) with **`combiner_score≈-0.96`** — better than strict-only grids on that objective, but **cost stress** is **`positive_but_sensitive`** (**fails** at **0.02** slip on stress replay). **`cost_robust_systems.csv`** is **empty** at the configured robust filter.

## 2. Candidate universe

Full **27** YAMLs (includes **relaxed_filter** warning rows).

## 3. Diagnostics

- Folder: `diagnostics/`
- **18,271** total candidate signals across strategies (see CLI log).

## 4. Fixed runs

See `fixed_run_summary.csv`. Highlights:

- **Trap top1 (relaxed):** **1341** trades, **`total_r=67.17`** (relaxed execution defaults: higher `max_trades_per_day`, looser daily loss).
- **All-with-relaxed top5:** **3642** trades, **`total_r=147.94`** — high trade count, **negative combiner_score**.

## 5. Full sweep

- **Folder:** `sweep_20260506_010141_sweep_relaxed_2020_posthardening/`
- **Combos:** 3360
- **Precompute:** ~**58.7 s**
- **Sweep loop:** ~**453 s** (total ~**474 s** logged)

## 6. Top config-unique systems

`top_unique_systems.csv`: rank **1** = **`vwap_control_family`**, **`top_per_strategy=1`**, **`max_trades_per_day=2`**, **`daily_max_loss_r=-1.5`**, **`cooldown_after_loss_minutes=30`**, **1000** trades, **`total_r=30.72`**, **`profit_factor=1.021`**.

## 7. Top behavior-unique systems

`behavior_unique_systems.csv`: **1** behavior hash in top-100 scan — same VWAP pair as config-unique rank 1.

## 8. Cost stress

`cost_stress/cost_stress_summary.md`: **`total_r`** **67.3 → 30.7 → -46.9 → -117.4** at slip **0.005 / 0.01 / 0.02 / 0.03**.

## 9. Cost-robust systems

`cost_robust_systems.csv` is **empty** (no rows) under **`cost-robust-min-trades 300`**, **0.02** slip, and related floors.

## 10. Fixed vs sweep comparison

See `fixed_vs_sweep_comparison.csv` — relaxed sweep leaders **do not** match trap-only fixed runs on composition (VWAP control vs opening).

## 11. Period breakdown observations

Under `fixed_runs/` (git-ignored detail folders).

## 12. Research conclusion

Relaxed YAMLs improve **combiner_score** for **VWAP** stacks but **fragile** under **cost stress** — consistent with 2023 relaxed narrative.

## 13. Layer 3 smoke

**Defer.** VWAP-forward leaders **fail** **0.02** cost stress; all-with-relaxed shows very high trade churn. No Layer 3 build or commands.
