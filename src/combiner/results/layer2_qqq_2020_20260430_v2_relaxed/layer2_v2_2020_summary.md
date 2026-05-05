# Layer 2 v2 relaxed (QQQ) — 2020-01-01 to 2026-04-30

## 1. Executive summary

- Ran Layer 2 v2 relaxed combiner on the **new 2020–2026 candidate library** (27 candidates).
- Best unique system from the sweep is a **VWAP control** pair (`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`) with **top_per_strategy=1**, **max_trades_per_day=2**, **daily_max_loss_r=-1.5**, **cooldown=30**.
- Cost robustness is **positive but sensitive**: performance degrades materially at 0.02–0.03 slippage/share.

## 2. Why 2020–2026 window

The longer window increases regime coverage and helps avoid selecting candidates that only fit the short 2025–2026 period. Results remain **in-sample** and not live-ready.

## 3. Why v2 relaxed

The v2 relaxed grid expands system-level constraints (max trades/day up to 10, daily loss down to -5, cooldown can be 0) and compares multiple candidate-set families without changing strategy logic.

## 4. Candidate universe

- **Candidate root:** `src/research/results/layer1_all10_qqq_2020_20260430_v1/selected_candidates`
- **Candidates:** 27 total (15 strict, 12 relaxed)

## 5. Diagnostics

Diagnostics root: `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/diagnostics/`

- **Total signals:** 18,265
- **Signals by strategy (top):** orb_retest_continuation (4,900), failed_orb (4,132), orb_continuation (3,078)
- **Note:** overlap/conflict reporting uses fast vectorized counts; minute-diff is reported as an **approximate** median-minute difference (no slow exact minute-diff loop).

## 6. Fixed runs

Fixed runs summary: `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/fixed_run_summary.csv`

Highlights (all 2020–2026):
- `v2_2020_fixed_trap_top1`: 1,341 trades, total_r 67.17, PF 1.140, max_dd_r -24.38
- `v2_2020_fixed_all_with_relaxed_top5`: 3,649 trades, total_r 148.83, PF 1.075, max_dd_r -37.57

## 7. Full v2 sweep

- **Sweep folder:** `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/sweep_20260505_072445_sweep_v2_relaxed_2020_20260430/`
- **Combos:** 3,360
- **Elapsed:** ~1,600s wall time (precompute ~772s, sweep loop ~791s)

## 8. Top unique systems

Top unique systems: `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/top_unique_systems.csv`

Best unique (rank 1):
- candidate_set: `vwap_control_family`
- top_per_strategy: 1
- max_trades_per_day: 2
- daily_max_loss_r: -1.5
- cooldown_after_loss_minutes: 30
- candidates: `VWAP_RECLAIM_REJECT_001`, `VWAP_TREND_PULLBACK_001`
- trades: 1,000
- total_r: 30.72
- PF: 1.021
- max_dd_r: -27.85

## 9. Cost stress

Cost stress (top 10 unique): `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/cost_stress/`

For unique_rank 1 (slippage/share):
- 0.005 → total_r 67.32, PF 1.064
- 0.010 → total_r 30.72, PF 1.021
- 0.020 → total_r -46.95, PF 0.937
- 0.030 → total_r -117.36, PF 0.850

Label: `positive_but_sensitive`

## 10. Interpretation (in-sample only)

- Relaxing system constraints can improve total_r, but the best “unique” configurations here are relatively **tight** (low max_trades/day + cooldown).
- The best system is driven by a **VWAP pair**; adding many additional families increases trade count but does not necessarily improve cost robustness.

## 11. Comparison vs old window

Not performed in this summary (requires old-window `top_unique_systems.csv` artifacts for v1/v2 relaxed).

## 12. Research conclusion

- This is **in-sample research** across 2020–2026; it is **not live-ready**.
- Recommended next step is to freeze **1–3** top unique systems and design a **Layer 3 holdout / walk-forward** rather than continuing to tune Layer 2 on the same sample.

## 13. Recommended next step

- Pick 1–3 systems from `top_unique_systems.csv`
- Design a holdout regime split / walk-forward (Layer 3)
- Re-validate on SPY only after SPY parquet coverage is complete

