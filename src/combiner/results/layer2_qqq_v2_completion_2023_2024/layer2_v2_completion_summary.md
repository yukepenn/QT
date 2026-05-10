# Layer 2 v2 Completion — QQQ 2023–2024

## 1. Purpose

Reduced Layer 2 combiner exercise for **Strategy Library v2 completion** candidates selected in Layer 1 (`30` YAMLs, QQQ **2023-01-01 → 2024-12-31**). This document records diagnostics, fixed runs, a **756-combo** sweep, postprocess (dedupe, behavior, cost stress), and a **single explicit decision** for the next research phase.

**Not in scope:** mini-WFO v4/v5, full WFO, live/paper trading, SPY, IBKR pulls, new strategy logic.

## 2. Inputs

| Item | Value |
|------|--------|
| **Candidate root** | `src/research/results/layer1_v2_completion_qqq_2023_2024/selected_candidates` |
| **YAML count** | **30** (all fast-context checks passed in Layer 1) |
| **Strict vs relaxed** | Layer 1 manifest: **28** strict, **2** relaxed (`adx_dmi_trend_continuation` only) |
| **Excluded strategies** | `sma20_reclaim_reject`, `large_candle_failure` — **no** YAMLs (zero Layer 1 selections) |
| **ADX** | Diagnostic / relaxed-only; combiner sets: `adx_diagnostic`; included in `all_with_relaxed_completion` only |

**Counts by strategy (from diagnostics `candidate_signal_summary`):**  
`stochastic_oversold_cross` 2510, `supertrend_atr_flip` 2494, `macd_momentum_turn` 1499, `cci_extreme_snapback` 898, `adx_dmi_trend_continuation` 872, `prior_close_reclaim` 759, `multi_day_level_trap` 240 — **9272** total selected bar-rows across candidates (pre-conflict universe).

## 3. Configs

| File | Role |
|------|------|
| `src/combiner/configs/layer2_qqq_v2_completion_2023_2024.yaml` | Base combiner config (`name: layer2_qqq_v2_completion_2023_2024`) |
| `src/combiner/configs/layer2_sweep_qqq_v2_completion_2023_2024.yaml` | Sweep grid (`name: layer2_sweep_qqq_v2_completion_2023_2024`) |

**Candidate sets (families):** `macd_momentum_family`, `oscillator_reversal_family`, `atr_trend_family`, `level_reclaim_family`, `strict_completion_core`, `all_strict_completion`, `all_with_relaxed_completion`, `adx_diagnostic`.

**Grid size:** `7 × 3 × 3 × 3 × 2 × 2 = **756**` combos (`candidate_set` × `top_per_strategy` × `max_trades_per_day` × `daily_max_loss_r` × `cooldown_after_loss_minutes` × `priority_policy`).

**System constraints (base):** `max_open_positions: 1`, `max_trades_per_day: 2`, `daily_max_loss_r: -2.0`, `cooldown_after_loss_minutes: 15`, `cooldown_scope: session`, execution block per YAML (commission `0`, slip `0.01`, EOD exit minute `389`, no new after `360`, `recompute_target_from_entry: true`, `min_risk_per_share: 0.03`).

## 4. Diagnostics

| Metric | Value |
|--------|--------|
| Candidates in diagnostics run | **30** |
| Total signals (diagnostics footer) | **9272** |
| Signals by strategy | See §2 table |
| **Overlap / conflicts** | High same-bar contention when many strategies run together; `lower_priority_conflict` and `existing_position` dominate in multi-strategy fixed runs |
| **Near-duplicate candidates** | Several strategies export **top-5** variants with similar parameter corners (MACD, Stoch, Supertrend, prior close) — combiner sees redundant competition |
| **Relaxed ADX** | Adds volume without fixing portfolio-level drag when paired with reclaim strategies |

Artifacts: `diagnostics/candidate_signal_summary.csv`, `candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`, `diagnostics_summary.md`, `candidate_precompute_profile*.csv` (also copied to result root as `candidate_precompute_profile_summary.{csv,md}`).

**Broken candidates:** **None** observed (all precomputes completed; fast-context was already 30/30 in Layer 1).

## 5. Fixed runs

Base combiner settings except per-run `--candidate-set` / `--top-per-strategy` / `--tag`. Signal cache: `%LOCALAPPDATA%\QT\candidate_signals`.

| candidate_set | top | trades | total_r | profit_factor | max_drawdown_r | Notes |
|---------------|-----|--------|---------|---------------|----------------|--------|
| macd_momentum_family | 1 | 497 | 15.76 | 1.06 | -16.72 | Strong single-strategy |
| macd_momentum_family | 3 | 831 | 26.18 | 1.07 | -20.65 | Good; conflicts moderate |
| oscillator_reversal_family | 1 | 609 | 56.60 | 1.27 | -15.83 | Best PF among families |
| oscillator_reversal_family | 3 | 766 | 62.02 | 1.26 | -17.40 | Best total_r among fixed |
| atr_trend_family | 1 | 497 | 20.74 | 1.10 | -11.92 | Solid |
| atr_trend_family | 3 | 518 | 17.17 | 1.08 | -12.29 | Slight dilution vs top1 |
| level_reclaim_family | 1 | 186 | **-218.74** | 0.25 | **-219.72** | **prior_close_reclaim** dominates negative R in portfolio |
| level_reclaim_family | 3 | 187 | **-219.75** | 0.24 | **-220.73** | Same failure mode |
| strict_completion_core | 1 | 977 | -44.83 | 0.95 | -81.91 | Reclaim + crowded book |
| strict_completion_core | 3 | 981 | -58.33 | 0.88 | -84.98 | Worse with more candidates |
| all_strict_completion | 1/3 | (same as strict_core for top1/top3) | — | — | — | Same six #1 YAMLs |
| all_with_relaxed_completion | 1 | 980 | -27.27 | 0.99 | -80.07 | ADX does not rescue |
| all_with_relaxed_completion | 3 | 983 | -60.87 | 0.88 | -102.24 | Heavy overlap |
| adx_diagnostic | 2 | 588 | -12.93 | 1.00 | -31.29 | Weak diagnostic |

**Best fixed run (economics):** `oscillator_reversal_family` **top3** — **62.02** total_r, PF **1.26**, **766** trades.  
**Weakest / actionable:** `level_reclaim_family` — catastrophic combiner portfolio R driven by **`prior_close_reclaim`** selection vs **`multi_day_level_trap`** under current conflict + risk rules.

## 6. Sweep

| Metric | Value |
|--------|--------|
| **Sweep folder** | `sweep_20260510_025424/` |
| **Combo count** | **756** (`results.csv` rows) |
| **Precompute wall time** | ~**10.1** s (20 candidates in union after grid filter) |
| **Sweep loop wall time** | ~**111** s (progress logs at 100-combo steps) |
| **Total sweep wall time** | ~**119.5** s (tool-reported `[Layer2 sweep] total_elapsed_s`) |
| **Host elapsed (PowerShell stopwatch)** | ~**131** s |
| **Best combiner_score** | **1.6132** (first crossed ~combo 100; best **1.6132** by combo 500+) |
| **Cache** | Signal cache **hits** on all 20 precompute rows after warm diagnostics/fixed runs |
| **Failures** | **0** (sweep completed) |

## 7. Top unique systems

Config dedupe (`dedupe_top=50`) collapses many parameter duplicates. **Dominant winning corner:** `strict_completion_core` / `all_strict_completion` with **`max_trades_per_day=1`**, **`top_per_strategy=1`**, **`daily_max_loss_r=-1.5`**, **`cooldown_after_loss_minutes`** in `{0,15}`, both priority policies — same six candidate IDs.

**Representative top row (unique_rank 1, baseline slip 0.01):**

| Field | Value |
|-------|--------|
| candidate_set | `strict_completion_core` |
| top_per_strategy | 1 |
| max_trades_per_day | 1 |
| daily_max_loss_r | -1.5 |
| cooldown_after_loss_minutes | 0 |
| priority_policy | `metadata_priority` |
| trades | **502** |
| total_r | **54.32** |
| profit_factor | **1.257** |
| max_drawdown_r | **-13.08** |
| Family composition (trades_by_strategy) | `stochastic_oversold_cross` **373**, `macd_momentum_turn` **103**, `prior_close_reclaim` **17**, `multi_day_level_trap` **7**, `cci_extreme_snapback` **2**; `supertrend_atr_flip` **0** fills (listed but starved at `max_trades_per_day=1`) |

Full table: `top_unique_systems.csv` / `top_unique_systems.md` (top **50** config-unique rows).

## 8. Behavior unique

| Metric | Value |
|--------|--------|
| Config rows considered | **30** |
| Rows with `trades.csv` | **15** |
| **Behavior-unique systems** | **1** |
| Weak hash rows | **0** |
| Missing trades (no `top_runs` match) | **15** |

**Interpretation:** Trade-sequence dedupe **collapses** to a **single** behavior hash among detailed reruns — same structural path dominates `detail_top` configs. **Does not** meet a “≥2 behavior-distinct survivors” bar for mini-WFO v4 design.

## 9. Cost stress

Leaderboard system: **unique_rank 1** (`strict_completion_core`, `top_per_strategy=1`, `max_trades_per_day=1`, `daily_max_loss_r=-1.5`, cooldown `0`, `metadata_priority`).

| slippage_per_share | total_r | profit_factor | max_drawdown_r | combiner_score |
|--------------------|---------|---------------|----------------|----------------|
| 0.005 | 67.33 | 1.300 | -12.35 | 1.87 |
| **0.01** | **54.32** | **1.257** | **-13.08** | **1.61** |
| **0.02** | **13.52** | **1.100** | **-16.37** | **0.75** |
| 0.03 | -19.60 | 0.989 | -40.42 | -0.64 |

**cost_robustness_label (engine):** `robust_positive_at_0_02` for the stressed leaderboard rows.

**cost_robust_systems.csv:** **10** rows at **0.02** slip (deduped policy variants of the same winning corner) — all show **positive** total_r at 0.02 with PF **> 1.05**. **At 0.03**, the same path is **negative** on total_r (cost tail risk).

## 10. Family interpretation

| Family / set | Classification | Notes |
|----------------|------------------|-------|
| macd_momentum_family | **PROMISING_BUT_COST_SENSITIVE** | Good alone; crowded when stacked |
| oscillator_reversal_family | **ROBUST_CANDIDATE_FOR_MINIWFO_V4_DESIGN** (isolated) | Best fixed runs; watch multi-candidate conflicts |
| atr_trend_family | **PROMISING_BUT_COST_SENSITIVE** | Strong alone; mild dilution top3 |
| level_reclaim_family | **DEFER** (combiner portfolio) | **Do not** merge reclaim `#001` with trap `#001` under defaults without redesign |
| all_strict_completion | **BEHAVIOR_DUPLICATE_ONLY** at sweep scale | Top ranks duplicate same six-ID corner |
| all_with_relaxed_completion | **WEAK_DIAGNOSTIC** | Relaxed ADX + reclaim hurts |
| adx_diagnostic | **WEAK_DIAGNOSTIC** | Negative R, ~PF 1.0 |

## 11. Decision

### **B. `TUNE_COMPLETION_GRIDS_FIRST`**

**Rationale (exactly one):**

- Sweep finds a **credible** `max_trades_per_day=1` corner (**54** R @ 0.01 slip, **13.5** R @ **0.02**, PF still **> 1.05**), so results are **not** a blanket failure.
- **`prior_close_reclaim`** selections **destroy** portfolio R in **`level_reclaim_family`** and **`strict_completion_core`** at **`max_trades_per_day=2`** defaults — candidate / conflict / priority tuning (or excluding specific reclaim YAMLs from multi-strategy sets) is required **before** treating completion as a merged library.
- **Behavior dedupe** reports **1** unique trade path among detailed top rows — **fails** a prudent “≥2 behavior-distinct systems” gate for **`PROCEED_TO_MINI_WFO_V4_DESIGN`**.
- Therefore: **retune completion combiner grids / candidate sets** (and reclaim–trap interaction), **not** mini-WFO v4 integration yet.

## 12. Explicit non-runs

- **mini-WFO v4** — **not run**
- **mini-WFO v5** — **not run**
- **Full WFO** — **not run**
- **Live / paper trading** — **not run**

---

*Sweep tag:* `layer2_v2_completion_2023_2024` · *Diagnostics candidate set:* `all_with_relaxed_completion`, `top_per_strategy=5`.
