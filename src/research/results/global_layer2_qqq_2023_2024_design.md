# Global Layer 2 design — QQQ 2023–2024 (v1)

## Status

**Design-only** unless conditional gates in `layer1_global_qqq_2023_2024_v1/global_layer2_gate_decision.md` pass after a complete Global Layer 1 run.

## Candidate root

`src/research/results/layer1_global_qqq_2023_2024_v1/selected_candidates/`

Strict YAMLs only; **no** diagnostic relaxed candidates in **core** buckets.

## Proposed candidate buckets

1. **opening_trap_core** — `failed_orb`, `gap_acceptance_failure` (if strict-selected), `prior_day_level_trap`, `orb_retest_continuation`, `orb_continuation`
2. **vwap_core** — `vwap_reversal`, `vwap_reclaim_reject`, `vwap_trend_pullback`
3. **indicator_completion_core** — `stochastic_oversold_cross`, `cci_extreme_snapback`, `macd_momentum_turn`, `supertrend_atr_flip`, `rsi_failure_swing`, `bollinger_squeeze_breakout` (if strict + cost OK), `bollinger_band_fade_chop` only if strict/cost OK after grid repair
4. **pa_core** — PA strategies that survive strict + diversity; PA B/C “repaired” paths **diagnostic** unless Layer 1 strict ranks them highly
5. **all_strict_global** — all strict candidates
6. **all_strict_low_turnover** — strict with trades ≤ 250 on 2023–2024 window
7. **all_behavior_diverse** — one YAML per `pure_signal_hash` group per strategy/family where possible
8. **long_short_mixed** — only if short/both candidates exist from Layer 1 strict; **no** synthetic shorts

## Sweep grid v1 (336 combos)

| Axis | Values |
|------|--------|
| candidate_set | `opening_trap_core`, `vwap_core`, `indicator_completion_core`, `pa_core`, `all_strict_low_turnover`, `all_behavior_diverse`, `all_strict_global` |
| top_per_strategy | 1, 2 |
| system.max_trades_per_day | 1, 2 |
| system.daily_max_loss_r | -1.5, -2.0, -3.0 |
| system.cooldown_after_loss_minutes | 0, 15 |
| conflict.priority_policy | `metadata_priority`, `score_adjusted_priority` |

**Grid size:** 7 × 2 × 2 × 3 × 2 × 2 = **336**

## Fixed economics (baseline)

- `slippage_per_share`: **0.01**
- Cost stress in postprocess: **0.02** and **0.03**
- `max_open_positions`: **1**
- `no_new_after`: **360**
- `eod_exit`: **389**
- `min_risk_per_share`: **0.03**

## Prerun gates (before executing Layer 2)

- ≥ **3** distinct **families** with strict Layer 1 candidates
- Strict selected YAML count ≤ **80**
- Fast-context check **all ok**
- Diversity report **readable** (heuristic: duplicate group CSV row count ≤ **200** in automation)
- Top candidates not a single-strategy clone; **behavior_unique ≥ 2** strong hashes preferred
- Cost stress at **0.02**: `total_r >= 0`, PF / PF_R > **1.05** where applicable
- Max drawdown and “trade #2” sanity per combiner postprocess
- **No** diagnostic-only candidates in core system definitions

## If gates pass (configs to add)

| File | Role |
|------|------|
| `src/combiner/configs/layer2_qqq_global_2023_2024_v1.yaml` | Fixed baseline combiner config |
| `src/combiner/configs/layer2_sweep_qqq_global_2023_2024_v1.yaml` | 336-combo sweep |
| `src/combiner/results/layer2_qqq_global_2023_2024_v1/` | Results root |

**Run order (when allowed):** diagnostics-only → fixed runs by bucket → full 336 sweep → postprocess (behavior_unique + cost stress).

## Decision outcomes (post Layer 1)

One of: **PROCEED_TO_GLOBAL_MINI_WFO_DESIGN** | **TUNE_GLOBAL_LAYER1_OR_BUCKETS** | **DEFER_GLOBAL_UNTIL_MORE_STRATEGIES_READY** | **FIX_IMPLEMENTATION_FIRST**

**Note:** mini-WFO is **out of scope** for this repo phase; the first option names a **design** follow-up only.
