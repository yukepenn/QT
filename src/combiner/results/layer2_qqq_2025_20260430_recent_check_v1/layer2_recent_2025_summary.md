# Layer 2 — QQQ recent-window check v1

In-sample research only (2025-01-01 → 2026-04-30 on QQQ RTH). Not live-ready. No Layer 3.

## 1. Purpose

Recent-window Layer 2 check after strong Layer 1 2025–2026 results, with a wider risk envelope:

- `max_open_positions=1`
- `max_trades_per_day` up to **5**
- `daily_max_loss_r` down to **-5.0**

## 2. Window and candidate universe

- **Symbol:** QQQ
- **Start / end:** 2025-01-01 → 2026-04-30
- **Candidate root:** `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/selected_candidates`
- **Candidates:** 40 total (30 strict + 10 relaxed warnings from Layer 1)

Candidate sets used in the sweep config:

- `trap_family`: failed_orb + gap_acceptance_failure + prior_day_level_trap
- `opening_family`: failed_orb + gap_acceptance_failure + orb_continuation + orb_retest_continuation
- `core5_no_vwap`: opening + prior_day_level_trap
- `strict_core`: core + vwap_reclaim_reject
- `vwap_control_family`: vwap_reclaim_reject + vwap_trend_pullback (warnings allowed)
- `all_strict`: all non-warning candidates (max 5 per strategy)
- `all_with_relaxed`: includes warning candidates (max 5 per strategy)

## 3. Diagnostics (all_with_relaxed, top_per_strategy=5)

From `diagnostics/`:

- **candidates=40**
- **total_signals=6327**
- **by_strategy**:
  - failed_orb: 1173
  - orb_continuation: 1136
  - vwap_reclaim_reject: 994
  - orb_retest_continuation: 990
  - vwap_trend_pullback: 674
  - afternoon_continuation: 640
  - gap_acceptance_failure: 365
  - prior_day_level_trap: 355

## 4. Fixed runs (detailed)

From `fixed_run_summary.csv`:

- **best fixed (strict_core / all_strict, top=5)**:
  - trades=787
  - total_r=89.79
  - profit_factor=1.3336
  - max_drawdown_r=-21.19
  - selection_rate=0.157
  - key rejections: existing_position=1878, lower_priority_conflict=2335

- **trap_family top=1**:
  - trades=329
  - total_r=66.33
  - profit_factor=1.4794
  - max_drawdown_r=-14.10
  - selection_rate=0.873

- **vwap_control_family top=5**:
  - trades=531
  - total_r=38.14
  - profit_factor=1.0842
  - max_drawdown_r=-20.61

## 5. Full sweep

Sweep folder:
`sweep_20260506_031937_sweep_recent_2025_layer2_check/`

- **grid rows:** 2688
- **precompute:** ~26.2s (40 candidates)
- **sweep loop:** ~348.0s
- **best combiner_score observed during sweep:** 1.4086

## 6. Best config-unique systems (top unique)

From `top_unique_systems.csv`:

The top config-unique systems are dominated by **`trap_family` top_per_strategy=1** (3 candidates) with `max_trades_per_day=2` and `cooldown_after_loss_minutes=0`:

- unique_rank=1: candidate_set=trap_family, top_per_strategy=1, max_trades_per_day=2, daily_max_loss_r=-1.5, cooldown=0
  - trades=323, total_r=69.06, profit_factor=1.5163, max_drawdown_r=-12.08, avg_bars_held=21.13, combiner_score=1.4086

## 7. Best behavior-unique systems

From `behavior_unique_systems.csv` (behavior-unique among the top unique configs):

- **behavior_rank=1 (strong hash)**: trap_family top=1 (3 candidates)
  - trades=323, total_r=69.06, profit_factor=1.5163
  - profit_factor_r=1.4095
  - max_drawdown_r=-12.08
  - avg_cost_r=0.0271, median_cost_r=0.0211
  - daily trade-number split: trade #1 total_r=51.83 vs trade #2 total_r=17.23

## 8. Cost stress

From `cost_stress/cost_stress_summary.md`:

- The top unique system (trap_family top=1) stays **positive through 0.03** slippage:
  - 0.01: total_r=69.06, PF=1.5163
  - 0.02: total_r=61.23, PF=1.4823
  - 0.03: total_r=56.89, PF=1.4578
  - label: `robust_positive_at_0_03`

## 9. Cost-robust systems

From `cost_robust_systems.csv` (filters include `slip=0.02`, `min_trades=100`, `min_total_r=0`, `min_pf=1.0`, `max_dd_r=-60`):

- Multiple systems qualify, including:
  - `trap_family` top=1 (robust_positive_at_0_03 at 0.02)
  - `core5_no_vwap` top=1 (robust_positive_at_0_03 at 0.02)

## 10. Main takeaways (recent-window only)

- In this window, the best Layer 2 systems are **opening/trap families** with **small candidate sets** and `top_per_strategy=1`, consistent with 1-position routing.
- Allowing `daily_max_loss_r=-5.0` and `max_trades_per_day=5` is supported in the sweep grid, but the current top unique winners do **not** require the most permissive settings to rank well.
- VWAP-only control remains materially weaker than the top opening/trap systems in this recent window.

