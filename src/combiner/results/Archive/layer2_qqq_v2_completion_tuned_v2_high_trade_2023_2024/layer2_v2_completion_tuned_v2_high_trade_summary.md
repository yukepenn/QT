# Layer 2 v2 completion — tuned v2 high-trade summary (QQQ 2023–2024)

## 1. Purpose

**High-trade rerank / behavior coverage** pass after tuned v1: score and cost tables were dominated by **low-trade `cci_only`**, while **`behavior_unique` stayed 1** despite strong **~900-trade** fixed paths. Tuned v2 narrows candidate sets, raises default **`max_trades_per_day` to 2** in the base YAML, sweeps **`max_trades_per_day` ∈ {1,2,3}`**, uses **`--detail-top 60`** / **`--behavior-dedupe-top 60`**, and adds generic **`rank_high_trade_systems`** (`--min-trades-rank 400`, `--rank-high-trade-top 30`) plus **`high_trade_layer2_cost_review.py`** on `top_unique` × `cost_stress_results`.

**Non-runs:** mini-WFO v4/v5, full WFO, live/paper, strategy logic, Layer 1 grids, refined_failed_orb.

## 2. Prior tuned v1 recap

| Item | Tuned v1 |
|------|-----------|
| Reclaim in core sweep | **Removed** (diagnostic isolated) |
| Fixed high-trade leaders | **`stoch_macd_pair`**, **`completion_no_reclaim`**, **`oscillator_momentum_trend`** ~**50–52** R @ **0.01** slip, **~502** trades (with v1 base **`max_trades_per_day=1`**) |
| **Behavior-unique** | **1** (CCI path) |
| **Cost leaderboard** | **`cci_only`** dominated **`combiner_score`** |
| **`cost_robust_systems`** | **Empty** at default thresholds |
| **mini-WFO v4** | **Blocked** |

## 3. Tuned v2 config

| File | Role |
|------|------|
| `src/combiner/configs/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml` | Base (`name: layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024`) |
| `src/combiner/configs/layer2_sweep_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml` | Sweep (`name: layer2_sweep_qqq_v2_completion_tuned_v2_high_trade_2023_2024`) |

**Candidate sets (10):** `stoch_macd_pair`, `stoch_macd_pair_top_candidates`, `oscillator_momentum_trend`, `completion_no_reclaim`, `completion_no_prior_close`, `trend_only_pair`, `macd_core`, `atr_core`, `stochastic_only`, `cci_only_diagnostic`.

**Excluded:** `prior_close_reclaim`, `adx_dmi_trend_continuation`, `sma20_reclaim_reject`, `large_candle_failure`.

**Grid:** 10 × 2 × 3 × 2 × 2 × 2 = **480** combos.

## 4. Fixed runs (baseline slip 0.01 from YAML)

| candidate_set | top | trades | total_r | PF | maxDD R | Notes |
|---------------|-----|--------|---------|-----|---------|--------|
| stoch_macd_pair | 1 | 906 | **62.17** | 1.18 | -15.86 | High-trade; **>40 R**, **PF>1.10** |
| stoch_macd_pair | 2 | 963 | **62.79** | 1.16 | -16.96 | |
| oscillator_momentum_trend | 1 | 1003 | **70.27** | 1.16 | -16.15 | |
| oscillator_momentum_trend | 2 | 1003 | 58.44 | 1.10 | -16.01 | |
| completion_no_reclaim | 1 | 1003 | **70.27** | 1.16 | -16.15 | Same IDs as omni top1 |
| completion_no_reclaim | 2 | 1003 | 58.44 | 1.10 | -16.01 | |
| completion_no_prior_close | 1 | 1003 | **69.97** | 1.19 | -16.99 | |
| completion_no_prior_close | 2 | 1003 | 48.90 | 1.09 | -17.58 | |
| trend_only_pair | 1 | 913 | **39.05** | 1.12 | -22.13 | Positive |
| trend_only_pair | 2 | 951 | 18.58 | 1.04 | -18.31 | |
| macd_core | 1 | 497 | 15.76 | 1.06 | -16.72 | Positive |
| macd_core | 2 | 862 | 16.68 | 1.05 | -23.44 | |
| atr_core | 1 | 497 | **20.74** | 1.10 | -11.92 | Positive |
| atr_core | 2 | 525 | 18.72 | 1.09 | -13.54 | |
| stochastic_only | 1 | 502 | 38.05 | 1.22 | -14.51 | |
| cci_only_diagnostic | 1 | 122 | 19.34 | 1.57 | -5.88 | **Low-trade** reference |

**Sweep gate:** **Passed** (high-trade >40 R + PF>1.10; trend/macd/atr positive; no reclaim sets).

## 5. Sweep

| Metric | Value |
|--------|--------|
| Directory | `sweep_20260510_040358/` |
| Combos | **480** |
| Precompute | ~**9.4** s (**10** candidates union) |
| Sweep loop | ~**54.4** s |
| Wall time (logged) | ~**91** s |
| Final **`best_score`** | **1.6188** |
| Failures | **0** |

## 6. Top unique

- **Overall top ranks** remain **`cci_only_diagnostic`** / **`CCI_EXTREME_SNAPBACK_001`** (122 trades) — same **score-domination** pattern as v1.
- **High-trade rank** (`rank_high_trade_systems.*`, trades ≥ **400**): dominated by **`stoch_macd_pair`** / **`stoch_macd_pair_top_candidates`** at **906–963** trades, **`total_r` ~62.2–62.8** @ baseline sweep slip.

## 7. Behavior unique

| Metric | Value |
|--------|--------|
| Config rows (behavior slice) | **60** |
| Rows with `trades.csv` | **50** |
| **Behavior-unique count** | **2** |
| Missing trades rows | **10** |

**Hashes (strong):**

1. **`cci_only_diagnostic`** / CCI001 — low-trade CCI path (still behavior rank **1** by table sort).
2. **`stoch_macd_pair`** top1 / MACD001+STOCH001 — **906** trades, **~62.17** R — **high-trade path now appears as a second distinct behavior** (vs tuned v1 collapse).

**`completion_no_reclaim`:** same trade sequence as **`oscillator_momentum_trend`** top1 in this library (not a third hash).

## 8. Cost stress

- **Standard `cost_stress_summary.md`:** still driven by **top unique_rank** rows (CCI-shaped) for the first pages.
- **Operational note:** first postprocess used **`--cost-stress-top 20`**, which **did not** include high-trade `combo_id`s in `cost_stress_results.csv`. Postprocess was **re-run** with **`--cost-stress-top 60`** so **`high_trade_cost_review.*`** could join **`stoch_macd_pair`** rows. For future runs, set **`cost_stress_top ≥ dedupe_top`** (or at least cover all rows you need in `high_trade_cost_review`).
- **High-trade leader (`stoch_macd_pair`, `max_trades_per_day=2`, combo_id 9)** — from `high_trade_cost_review.csv` / `cost_stress_results.csv`:

| slip | total_r | PF | maxDD R |
|------|---------|-----|---------|
| 0.01 | **62.17** | **1.182** | -15.86 |
| **0.02** | **-24.06** | **1.017** | **-45.83** |
| 0.03 | -82.10 | 0.912 | -97.10 |

So the **primary high-trade sweep configuration does not survive 0.02 R** at this turnover level (PF stays >1 but **R-multiple collapses** and **drawdown explodes**).

- **`cost_robust_systems.csv`:** still **header-only** (default filters).

## 9. Family interpretation

| Set | Label |
|-----|--------|
| cci_only_diagnostic | **PROMISING_BUT_LOW_TRADE** (robust at 0.02 R on CCI path) |
| stochastic_only | **PROMISING_HIGH_TRADE_BUT_BEHAVIOR_DUPLICATE** vs stoch-heavy bundles |
| stoch_macd_pair | **PROMISING_HIGH_TRADE_BUT_BEHAVIOR_DUPLICATE** / **COST_SENSITIVE** @ 0.02 when `max_trades_per_day=2` |
| stoch_macd_pair_top_candidates | Same as **stoch_macd_pair** (IDs collapse to same winners) |
| oscillator_momentum_trend | **PROMISING_HIGH_TRADE**; **COST_SENSITIVE** (re-check 0.02 on selected combo rows) |
| completion_no_reclaim | **PROMISING_HIGH_TRADE**; same bundle as omni top1 here |
| completion_no_prior_close | **PROMISING_HIGH_TRADE**; multi_day adds variance top2 |
| trend_only_pair | **ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN** only at **economics** for 0.01 window in this pass — still verify 0.02 per combo |
| macd_core | **PROMISING_BUT_COST_SENSITIVE** (PF thin) |
| atr_core | **ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN** at single-strategy scale (verify 0.02 per combo) |

## 10. Decision

### **B. `TUNE_COMPLETION_GRIDS_AGAIN`**

**Rationale (exactly one):**

- **Progress:** **`behavior_unique` = 2** with a **real high-trade `stoch_macd_pair` hash** — answers the **coverage** question partially in the **affirmative**.
- **Blocker for `PROCEED_TO_MINI_WFO_V4_DESIGN`:** the **flagship high-trade `stoch_macd_pair` grid corner** (`max_trades_per_day=2`) fails **0.02 `total_r`** (**heavily negative**) with **unacceptable drawdown inflation** at **0.02/0.03** in `cost_stress` / `high_trade_cost_review`. That violates the mini-WFO v4 gate requiring **0.02 survival** on chosen systems.
- **`DEFER_COMPLETION_AND_RETURN_TO_REFINED_FAILED_CORE`** is **not** selected: behavior is **no longer collapsed to one path**, and **0.01-window economics** remain strong on fixed runs — the issue is **grid / turnover interaction**, not “no alternative.”

**Next tuning direction (research):** prioritize **`max_trades_per_day=1`** for **pair/bundle** sets before widening to 2–3; optionally **drop `max_trades_per_day=3`** for pair-heavy sets; re-stress **0.02** after any change.

## 11. Explicit non-runs

- mini-WFO **v4** — not run  
- mini-WFO **v5** — not run  
- **Full WFO** — not run  
- **Live / paper** — not run  

## 12. mini-WFO v4 design doc

**Blocked.** Decision is not `PROCEED_TO_MINI_WFO_V4_DESIGN`; `src/research/results/mini_wfo_v4_completion_design.md` is **not** authored.

## 13. Tooling notes

- **`postprocess.py`:** `--min-trades-rank` and `--rank-high-trade-top` write **`rank_high_trade_systems.csv`** / **`.md`** from **`top_unique_systems.csv`** (generic sort: `total_r`, `profit_factor_r` if present, else `profit_factor`, then `max_drawdown_r`).
- **`src/research/high_trade_layer2_cost_review.py`:** pivots **`cost_stress/cost_stress_results.csv`** by **`source_combo_id`** for rows with **`trades ≥ --min-trades`**.
