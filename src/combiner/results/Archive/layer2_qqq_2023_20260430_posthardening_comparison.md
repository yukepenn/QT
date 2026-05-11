# Strict vs relaxed — QQQ post-hardening Layer 2 (2023-01-01 → 2026-04-30)

Sources: `layer2_qqq_2023_20260430_posthardening_strict_v1/*.csv`, `layer2_qqq_2023_20260430_posthardening_relaxed_v1/*.csv`, sweep `results.csv`, `cost_stress/cost_stress_summary.md`, `fixed_vs_sweep_comparison.md`.

## Config-unique (dedupe top 100 by parameters + candidate list)

| Mode | Best `combiner_score` row (representative) | `candidate_set` | `trades` | `total_r` | `profit_factor` | `max_drawdown_r` | `combiner_score` |
|------|---------------------------------------------|-----------------|----------|-----------|-----------------|------------------|------------------|
| **Strict** | `unique_rank` 1 (`combo_id` 1) | `trap_family`, `top_per_strategy=1`, `max_trades_per_day=1`, … | 523 | 30.181 | 1.180 | −17.218 | −1.385 |
| **Relaxed** | `unique_rank` 1 (`combo_id` 2307) | `vwap_control_family`, `top_per_strategy=5`, `max_trades_per_day=2`, cooldown 15 | 740 | 47.479 | 1.052 | −19.609 | −0.331 |

Strict sweep optimization landed on a **minimal trap trio** (failed_orb + gap_acceptance_failure + prior_day_level_trap top-1 each). Relaxed sweep’s score leader is **VWAP-only family** (reclaim_reject + trend_pullback), reflecting the relaxed candidate library and grid.

## Behavior-unique

| Mode | Count | Top behavior row |
|------|-------|-------------------|
| Strict | **1** strong hash | Same economics as config rank 1: trap_family, 523 trades, total_r 30.181, avg_cost_r ~0.024, daily_trade_number **1 only** (523 trades). |
| Relaxed | **2** strong hashes | (1) Full 5+5 VWAP bundle, 740 trades, total_r 47.479; (2) 3 reclaim + 3 pullback bundle, 733 trades, total_r 45.237. Second trade-of-day bucket contributes disproportionate R (see `r_by_daily_trade_number_json` in CSV). |

Postprocess noted **85 / 100** strict config-unique rows lacked detailed trades for behavior hashing (grid duplication / overlap).

## Cost stress (top 10 unique, base YAML)

| Mode | Label @ 0.01 slip (baseline) | At 0.02 slip (`total_r`) | At 0.03 slip (`total_r`) |
|------|------------------------------|---------------------------|----------------------------|
| Strict | `robust_positive_at_0_03` | 16.654 | 2.505 |
| Relaxed | `positive_but_sensitive` | −10.533 | −61.848 |

Strict top configs remain **positive through 0.03** slip on the stress ladder in `cost_stress_summary.md`. Relaxed leaders **flip negative by 0.02** share slip — consistent with higher **avg_cost_r / median_cost_r** (~0.075 vs ~0.024 on behavior row).

## Cost-robust filter (min_trades 200, slip 0.02, thresholds as postprocess run)

| Mode | Rows in `cost_robust_systems.csv` |
|------|-----------------------------------|
| Strict | **10** (first row: trap_family rank 1 → total_r **16.654** at 0.02 slip, PF 1.129, max_dd_r −20.376) |
| Relaxed | **0** (empty file — no sweep row satisfied all filters at once) |

## Rank leaders (full sweep `results.csv`)

- **`rank_by_total_r.csv` rank 1 — Strict:** `all_strict`, `top_per_strategy=2`, `max_trades_per_day=3`, combo **1273** — **total_r 74.813**, PF 1.154, max_dd_r −22.891, **1427 trades** (much larger portfolio than dedupe winner).
- **`rank_by_total_r.csv` rank 1 — Relaxed:** `all_with_relaxed`, `max_trades_per_day=10`, combo **3115** — **total_r 112.787**, PF 1.127, max_dd_r −36.176, **2119 trades**.

Highest **profit_factor_r** in both sweeps: **`opening_family`** subset (e.g. strict combo **314** — PF_r ~1.131, total_r ~58.8, 858 trades).

## Fixed runs vs sweep

- **Strict:** Broad fixed `all_strict` top5 reached **total_r 36.912** / 1409 trades vs sweep dedupe winner **30.181** / 523 trades — same comparison table pattern as `fixed_vs_sweep_comparison.md` (broad baskets ≠ score-optimal sparse configs).
- **Relaxed:** Fixed `all_with_relaxed` hit **102.587** / 2210 trades vs sweep score leader **47.479** / 740 — adding everything raises R in-sample but not combiner_score.

## Relaxed candidates: help or hurt?

- **Help combiner_score** when isolated in **`vwap_control_family`** (best −0.331 vs strict trap −1.385).
- **Hurt cost robustness** vs strict trap path (stress labels; empty relaxed cost_robust table).
- **`all_with_relaxed`** reaches highest raw **total_r** in relaxed sweep but with **more trades**, worse drawdown (−36.2 vs −19.6 on VWAP leader), and heavy **2nd/3rd trade-of-day** participation (`trades_by_daily_trade_number_json` on rank 1).

## Families dominating dedupe top 100

- **Strict:** Almost entirely **`trap_family`** variants at the top (same three candidates; grid duplicates).
- **Relaxed:** **`vwap_control_family`** dominates dedupe top ranks.

## Daily trade number

- Strict behavior-unique winner: **100%** of trades are daily trade #**1** (single slot under `max_trades_per_day=1`).
- Relaxed `all_with_relaxed` sweep winner: trades spread across **1–6** daily slots; rank-1 row shows substantial R on trades **2** (e.g. ~53.9 R on trade #2 vs ~28.6 on #1 in snippet).

## Monthly / quarterly consistency

Period breakdown CSVs live under each sweep’s `top_runs/run_*` and under `fixed_runs/run_*` per postprocess. This comparison does not aggregate quarters here; open those folders for regime splits.

## Suggested conclusion category

| Aspect | Label |
|--------|--------|
| Strict pipeline + trap_family | **positive_but_cost_sensitive** at pile-on leverage; **robust_candidate_found** under postprocess stress labels for top trap configs |
| Relaxed VWAP-heavy | **positive_but_cost_sensitive** (explicit in cost_stress); not cost-robust at requested filter |
| Overall | Not **no_clear_system** — there is a coherent strict trap edge on this window — but **not** live-ready; **Layer 3 still unjustified** without longer history and execution realism |
