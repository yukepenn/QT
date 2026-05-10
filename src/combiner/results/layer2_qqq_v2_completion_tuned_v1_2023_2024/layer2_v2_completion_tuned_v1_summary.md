# Layer 2 v2 completion — tuned v1 summary (QQQ 2023–2024)

## 1. Purpose

Focused **Layer 2 combiner** pass after `layer2_qqq_v2_completion_2023_2024` produced a **promising** `max_trades_per_day=1` corner but **behavior-unique = 1** and a **`prior_close_reclaim` / `multi_day_level_trap` catastrophic interaction** (~**-219** R in `level_reclaim_family`). This tuned run **removes reclaim and ADX from core grids**, tightens the default base to **`max_trades_per_day=1`**, and tests oscillator / MACD / Supertrend **singles and pairs** plus **`completion_no_prior_close`** / **`completion_no_reclaim`**.

**Not run:** mini-WFO v4/v5, full WFO, live/paper, Layer 1 grid changes, strategy signal logic changes, refined_failed_orb integration.

## 2. Prior result recap

| Item | Prior (`layer2_qqq_v2_completion_2023_2024`) |
|------|-----------------------------------------------|
| Best config-unique corner | `strict_completion_core`, `top_per_strategy=1`, `max_trades_per_day=1`, `daily_max_loss_r=-1.5` |
| Baseline @ 0.01 slip | ~**54.3** `total_r`, PF ~**1.26**, maxDD ~**-13.1** R |
| @ 0.02 slip | ~**13.5** `total_r`, PF ~**1.10** |
| @ 0.03 slip | Negative `total_r` |
| **Behavior-unique** | **1** |
| Toxic path | **`prior_close_reclaim`** ~**-218** R in `level_reclaim_family`; **`multi_day_level_trap`** near flat |
| Supertrend in best strict row | **0** executed trades (crowded by stoch/MACD/reclaim at `max_trades_per_day=1`) |
| **Why mini-WFO v4 stayed blocked** | Single behavior path + reclaim toxicity + cost tail at 0.03 |

## 3. Tuned config

| File | Role |
|------|------|
| `src/combiner/configs/layer2_qqq_v2_completion_tuned_v1_2023_2024.yaml` | Base (`name: layer2_qqq_v2_completion_tuned_v1_2023_2024`) |
| `src/combiner/configs/layer2_sweep_qqq_v2_completion_tuned_v1_2023_2024.yaml` | Sweep (`name: layer2_sweep_qqq_v2_completion_tuned_v1_2023_2024`) |

**Candidate sets (13 in sweep):** `oscillator_core`, `stochastic_only`, `cci_only`, `macd_core`, `atr_core`, `momentum_trend_core`, `stoch_macd_pair`, `stoch_supertrend_pair`, `macd_supertrend_pair`, `oscillator_momentum_trend`, `multi_day_only`, `completion_no_prior_close`, `completion_no_reclaim`.

**Diagnostic only (fixed run, not in sweep):** `prior_close_diagnostic` (`prior_close_reclaim` only).

**Excluded from core / sweep:** `prior_close_reclaim` (except diagnostic), `adx_dmi_trend_continuation`, `sma20_reclaim_reject`, `large_candle_failure`.

**Grid:** 13 × 2 × 2 × 2 × 2 × 2 = **416** combos.

## 4. Diagnostics

| Snapshot | Path | Candidates | Total signals | Notes |
|----------|------|------------|---------------|-------|
| `completion_no_prior_close` top5 | `diagnostics_completion_no_prior_close/` | 23 | 7641 | No reclaim; includes `multi_day_level_trap` |
| `oscillator_momentum_trend` top5 | `diagnostics_oscillator_momentum_trend/` | 18 | 7401 | No reclaim, no multi_day |
| Latest (post second run) | `diagnostics/` | 18 | 7401 | Same as oscillator_momentum snapshot |

**Prior close isolation:** reclaim **not** present in sweep candidate sets; **`prior_close_diagnostic`** fixed run confirms standalone toxicity (**~ -234** `total_r` on `PRIOR_CLOSE_RECLAIM_001` alone under tuned base).

## 5. Fixed runs

Base: `max_trades_per_day=1`, `daily_max_loss_r=-1.5`, `cooldown_after_loss_minutes=0`, `metadata_priority` (unless noted). QQQ **2023-01-01 → 2024-12-31**.

| # | candidate_set | top | trades | total_r | PF | maxDD R | Notes |
|---|---------------|-----|--------|---------|-----|---------|--------|
| 1 | stochastic_only | 1 | 502 | 38.05 | 1.22 | -14.51 | Strong |
| 2 | stochastic_only | 2 | 502 | 38.05 | 1.22 | -14.51 | Second YAML never wins (all conflicts) |
| 3 | cci_only | 1 | 122 | 19.34 | 1.57 | -5.88 | High PF, fewer trades |
| 4 | oscillator_core | 1 | 502 | 37.78 | 1.21 | -14.51 | Stoch dominates |
| 5 | oscillator_core | 2 | 502 | 37.78 | 1.21 | -14.51 | Same as top1 outcome |
| 6 | macd_core | 1 | 497 | 15.76 | 1.06 | -16.72 | Positive |
| 7 | macd_core | 2 | 502 | 25.09 | 1.05 | -13.84 | Positive |
| 8 | atr_core | 1 | 497 | 20.74 | 1.10 | -11.92 | Positive |
| 9 | atr_core | 2 | 497 | 18.86 | 1.08 | -12.29 | Positive |
| 10 | momentum_trend_core | 1 | 502 | 17.38 | 1.04 | -15.54 | Both legs get trades (97 ST) |
| 11 | momentum_trend_core | 2 | 502 | 18.65 | **0.97** | -13.52 | PF dips below 1.0 |
| 12 | stoch_macd_pair | 1 | 502 | **52.08** | 1.21 | -14.45 | **Best combined** |
| 13 | stoch_macd_pair | 2 | 502 | 26.36 | 1.09 | -21.17 | Weaker |
| 14 | stoch_supertrend_pair | 1 | 502 | 38.05 | 1.22 | -14.51 | Stoch only (1 supertrend bar lost) |
| 15 | stoch_supertrend_pair | 2 | 502 | 38.05 | 1.22 | -14.51 | Same |
| 16 | macd_supertrend_pair | 1 | 502 | 17.38 | 1.04 | -15.54 | Same as momentum top1 |
| 17 | oscillator_momentum_trend | 1 | 502 | **51.82** | 1.21 | -14.45 | Strong; supertrend contributes |
| 18 | oscillator_momentum_trend | 2 | 502 | 26.11 | 1.09 | -21.17 | Weaker |
| 19 | multi_day_only | 1 | 48 | 4.55 | 1.42 | -6.27 | Small N |
| 20 | completion_no_prior_close | 1 | 502 | **50.49** | 1.23 | -14.46 | **No reclaim**; multi_day in set |
| 21 | completion_no_prior_close | 2 | 502 | 24.76 | 1.11 | -21.16 | |
| 22 | completion_no_reclaim | 1 | 502 | **51.82** | 1.21 | -14.45 | Same IDs as row 17 |
| 23 | completion_no_reclaim | 2 | 502 | 26.11 | 1.09 | -21.17 | |
| 24 | prior_close_diagnostic | 1 | 150 | **-234.37** | 0.11 | -234.55 | **Do not merge** |
| 25 | macd_supertrend_pair | 2 | 502 | 18.65 | 0.97 | -13.52 | (run after collect; included in summary) |

**Sweep gate:** **Passed** — oscillator + MACD + ATR singles positive; **`stoch_macd_pair` top1** and **`completion_no_reclaim` / `oscillator_momentum_trend` top1** strongly positive; **`prior_close_diagnostic`** isolated and negative.

## 6. Sweep

| Metric | Value |
|--------|--------|
| Folder | `sweep_20260510_033030/` |
| Combos | **416** |
| Precompute | ~**9.9** s (**10** candidates in union) |
| Sweep loop | ~**46** s |
| Total | ~**58.6** s |
| Best `combiner_score` | **1.6188** |
| Failures | **0** |

## 7. Top unique systems (sample top 10)

Sweep dedupe ranks **`cci_only` / `CCI_EXTREME_SNAPBACK_001`** highest (122 trades, **~19.3** R @ 0.01 slip) across many parameter duplicates — **high PF, low trade count**.

**Higher-trade leaders** (examples from `top_unique_systems.csv`):

| candidate_set | top | max_trades | trades | total_r | PF | maxDD | trades_by_strategy (abbrev) |
|---------------|-----|------------|--------|---------|-----|-------|-------------------------------|
| cci_only | 1 | 1 | 122 | 19.34 | 1.57 | -5.88 | cci 122 |
| stoch_macd_pair | 1 | 2 | 906 | **62.17** | 1.18 | -15.86 | macd 427, stoch 479 |
| stoch_macd_pair | 2 | 2 | 963 | **62.79** | 1.16 | -16.96 | macd 497, stoch 466 |

Full table: `top_unique_systems.csv` / `.md`.

## 8. Behavior unique

| Metric | Value |
|--------|--------|
| Config rows (behavior pass) | 30 |
| Rows with `trades.csv` | 20 |
| **Behavior-unique count** | **1** |
| Missing trades rows | 10 |

**Interpretation:** Trade-sequence dedupe still collapses to **one** hash. Top hash corresponds to **`cci_only`** / `CCI_EXTREME_SNAPBACK_001` path — **does not** meet the “≥2 behavior-distinct systems” bar for mini-WFO v4. Multi-strategy rows (e.g. `stoch_macd_pair` at **906** trades) **did not** produce a second surviving behavior hash in the `detail_top` slice (see `behavior_unique_systems.md`).

## 9. Cost stress

Leaderboard **`unique_rank=1`** (`cci_only`, 122 trades) — from `cost_stress/cost_stress_summary.md`:

| slip | total_r | PF | maxDD R |
|------|---------|-----|---------|
| 0.005 | 23.60 | 1.723 | -5.68 |
| 0.010 | 19.34 | 1.571 | -5.88 |
| **0.020** | **9.10** | **1.329** | -6.24 |
| 0.030 | -1.53 | 1.128 | -7.76 |

**`cost_robust_systems.csv`:** **empty** (header only) — default postprocess thresholds / min-trades filter left **no** rows; interpret cost robustness from **`cost_stress_results.csv`** and fixed runs for high-trade systems (e.g. **`stoch_macd_pair` top1** fixed: **52** R @ 0.01 baseline — re-stress that path in a future pass if needed).

## 10. Family interpretation

| Set | Label | Notes |
|-----|-------|-------|
| stochastic_only | PROMISING_BUT_BEHAVIOR_DUPLICATE | top2 adds no diversity |
| cci_only | PROMISING_BUT_COST_SENSITIVE | Great PF; low **n**; drives dedupe |
| oscillator_core | PROMISING_BUT_BEHAVIOR_DUPLICATE | Same as stoch-heavy |
| macd_core | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (single-family) | Positive top1/top2 |
| atr_core | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (single-family) | Positive |
| momentum_trend_core | PROMISING_BUT_COST_SENSITIVE | top2 PF<1 |
| stoch_macd_pair | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (pair) | **Best fixed combined** |
| stoch_supertrend_pair | PROMISING_BUT_BEHAVIOR_DUPLICATE | Stoch wins all bars |
| macd_supertrend_pair | PROMISING_BUT_COST_SENSITIVE | top2 weak PF |
| oscillator_momentum_trend | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (bundle) | **~51.8** R top1 |
| multi_day_only | WEAK_SINGLE_FAMILY | Low **n** |
| completion_no_prior_close | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (bundle) | **~50.5** R top1 |
| completion_no_reclaim | ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN (bundle) | Same as omni w/o multi_day top1 |
| prior_close_diagnostic | DEFER | **Toxic** standalone |

## 11. Decision

### **B. `TUNE_COMPLETION_GRIDS_AGAIN`**

**Rationale (exactly one):**

- **Reclaim toxicity** is **solved** in core sets (no `prior_close` in sweep; diagnostic confirms isolation).
- **Economics improved materially** for **`stoch_macd_pair`**, **`oscillator_momentum_trend`**, **`completion_no_prior_close` / `completion_no_reclaim`** fixed runs (**50–52** R @ 0.01 slip, **502** trades).
- **However:** **behavior-unique count remains 1** — the mini-WFO v4 gate (“≥2 behavior-distinct systems”) is **not** met.
- **Cost leaderboard** is dominated by **low-trade `cci_only`**, and **`cost_robust_systems`** is empty under default filters — another tuning pass should re-rank **high-trade** configs explicitly and/or relax cost-robust min-trades for this research track.

**Not chosen:** `PROCEED_TO_MINI_WFO_V4_DESIGN` (behavior + cost-robust table). **Not chosen:** `DEFER_COMPLETION_AND_RETURN_TO_REFINED_FAILED_CORE` (clear improvement vs reclaim-collapse).

## 12. Explicit non-runs

- **mini-WFO v4** — not run  
- **mini-WFO v5** — not run  
- **Full WFO** — not run  
- **Live / paper** — not run  

## 13. mini-WFO v4 design doc

**Blocked.** Decision is not `PROCEED_TO_MINI_WFO_V4_DESIGN`; no `mini_wfo_v4_completion_design.md` authored.
