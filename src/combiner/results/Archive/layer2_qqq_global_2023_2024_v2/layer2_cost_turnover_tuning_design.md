# Layer 2 cost / turnover tuning — design (Global L2 v2 follow-on)

**Universe:** QQQ, equity, **2023-01-01 → 2024-12-31**, baseline slip **0.01**, commission **0**.  
**Candidate root (only):** `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates` (**66** YAMLs).  
**No** strategy edits, **no** new features, **no** signal-cache on OneDrive (prior WinError 5).

**Base config:** `src/combiner/configs/layer2_qqq_global_2023_2024_v2_cost_turnover.yaml`  
Adds buckets:

- `behavior_diverse_no_vwap` — `max_per_strategy: 1`, `exclude_strategies: [vwap_reclaim_reject, vwap_trend_pullback]`
- `non_vwap_strict_l2_core` — same excludes, `max_per_strategy: 80` (all strict l2_core except VWAP)

**Note:** There is **no** `cooldown_after_trade_minutes` in the combiner; grids use **`cooldown_after_loss_minutes`** only.

---

## Track A — `lower_turnover_vwap`

**Purpose:** See if the VWAP pair stays attractive when **max_trades_per_day = 1**, **tighter loss cooldown**, and **earlier `no_new_after_minute`** reduce churn.

**Config:** `layer2_sweep_qqq_global_2023_2024_v2_lower_turnover_vwap.yaml`

| Axis | Values |
|------|--------|
| `candidate_set` | `vwap_core`, `all_behavior_diverse`, `all_low_turnover` |
| `top_per_strategy` | `1` |
| `system.max_trades_per_day` | `1` |
| `system.daily_max_loss_r` | `-1.5`, `-2.0` |
| `system.cooldown_after_loss_minutes` | `15`, `30`, `60` |
| `conflict.priority_policy` | `metadata_priority`, `score_adjusted_priority` |
| `execution.no_new_after_minute` | `330`, `360` |

**Expected combos:** 3 × 2 × 3 × 2 × 2 = **72**

**Output root:** `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/lower_turnover_vwap/`

**Postprocess:** cost stress **0.01 / 0.02 / 0.03** (existing ladder).

---

## Track B — `family_diverse`

**Purpose:** Multi-family grids **without** VWAP in the bucket set (except what appears inside `all_*` — here we use **explicit** opening / indicator / PA / behavior-diverse-no-vwap only).

**Config:** `layer2_sweep_qqq_global_2023_2024_v2_family_diverse.yaml`

| Axis | Values |
|------|--------|
| `candidate_set` | `opening_trap_core`, `indicator_completion_core`, `pa_core`, `behavior_diverse_no_vwap` |
| `top_per_strategy` | `1` |
| `system.max_trades_per_day` | `1`, `2` |
| `system.daily_max_loss_r` | `-1.5`, `-2.0` |
| `system.cooldown_after_loss_minutes` | `15`, `30` |
| `conflict.priority_policy` | `metadata_priority`, `score_adjusted_priority` |

**Expected combos:** 4 × 2 × 2 × 2 × 2 = **64**

**Output root:** `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/family_diverse/`

---

## Track C — `cost_adjusted_objective_review`

**Purpose:** **No** change to production `combiner_score` in the sweep. Rank systems **after** the run using post-hoc objectives (see `src/combiner/analyze_layer2_cost_turnover.py`: `cost_adjusted_objective`, `layer2_cost_adjusted_ranking.csv`).

**Criteria (documentation only):** reward positive **total_r** and **PF > 1** at **0.02** slip, penalize **0.03** collapse, prefer **higher avg R/trade** and **lower** baseline **|maxDD|** where tied.

---

## Track D — `non_vwap_diagnostic`

**Purpose:** Test whether **any** non-VWAP assembly clears modest economic bars (baseline and **0.02** stress).

**Config:** `layer2_sweep_qqq_global_2023_2024_v2_non_vwap.yaml`

| Axis | Values |
|------|--------|
| `candidate_set` | `non_vwap_strict_l2_core`, `behavior_diverse_no_vwap`, `indicator_completion_core`, `opening_trap_core`, `pa_core` |
| `top_per_strategy` | `1` |
| `system.max_trades_per_day` | `1`, `2` |
| `system.daily_max_loss_r` | `-1.5`, `-2.0` |
| `system.cooldown_after_loss_minutes` | `0`, `15` |
| `conflict.priority_policy` | `metadata_priority`, `score_adjusted_priority` |

**Expected combos:** 5 × 2 × 2 × 2 × 2 = **80**

**Output root:** `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/non_vwap/`

**Pass / fail (diagnostic):** document if **no** row achieves **PF > 1.05** and **total_r > 0** at **0.02** (strict bar for “viable non-VWAP” in this note).

---

## Total diagnostic load

**72 + 64 + 80 = 216** combiner simulations (plus **detail-top** legacy reruns per sweep).

---

## Explicit non-goals

- No Layer 3 / mini-WFO  
- No SPY, no live/paper  
- No `long_short_mixed` unless strict shorts appear in YAMLs (they do not in l2_core)  
- No committing `sweep_*`, `top_runs/`, raw logs, or heavy precompute profiles
