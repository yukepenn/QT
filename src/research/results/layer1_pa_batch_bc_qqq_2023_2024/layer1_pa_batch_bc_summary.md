# PA Batch B/C — formal Layer 1 summary (QQQ 2023–2024)

Tag: `layer1_pa_batch_bc_qqq_2023_2024`  
Curated root: `src/research/results/layer1_pa_batch_bc_qqq_2023_2024/`

## 1. Purpose

Formal **Layer 1** sweeps for **PA Batch B** (four strategies) and **PA Batch C** (two strategies) after engineering implementation, on **QQQ** only, **2023-01-01 → 2024-12-31**, to see whether enough **strict** candidates appear to justify a later **reduced Layer 2** design.

## 2. Inputs

- **Strategies:** `pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`, `pa_buy_sell_close_trend`, `pa_generic_breakout_pullback`.
- **Window:** QQQ 2023–2024 (inclusive).
- **Configs:** `*_focused.yaml` per strategy; orchestrated via `run_layer1_focused.py`.
- **Not in scope:** SPY, IBKR pull, Batch A / refined_failed_orb mixing, Layer 2 execution, WFO, live/paper.

## 3. Preflight / grid review

- All six: `supports_fast=True`, default + focused YAML validation OK, metadata present, no `LOOKAHEAD` in required features (see plan + `preflight_check.*`).
- **Raw grids:** 288 (Batch B + `pa_buy_sell_close_trend` / `pa_generic_breakout_pullback` split: 288 vs 432 — see `grid_review.*`): all **≤ 1500** → **full grid**, **capped = false**, no silent `max_combos`.

## 4. Sweep results

| strategy | status | result_rows | best_trades | best_total_r | best_PF | best_maxDD_R | best_avg_bars_held | notes |
|----------|--------|-------------|-------------|--------------|---------|--------------|-------------------|-------|
| pa_broad_channel_zone | ok_zero_trade | 72 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | all combos zero-trade |
| pa_climax_reversal | ok | 72 | 93 | −13.71 | 0.879 | −17.90 | 7.37 | high activity, negative edge |
| pa_second_entry_pullback | ok | 72 | 8 | +6.58 | 2.387 | −1.07 | 4.5 | strong PF, tiny n |
| pa_wedge_reversal | ok | 72 | 126 | −10.09 | 0.964 | −24.77 | 10.06 | high activity, weak edge |
| pa_buy_sell_close_trend | ok | 108 | 413 | +24.07 | 1.230 | −10.86 | 59.34 | 36 rows pass strict filters |
| pa_generic_breakout_pullback | ok_zero_trade | 108 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | all combos zero-trade |

Detailed trade-count distributions: `signal_rate_diagnosis.*`. Sweep artifacts live under `src/strategies/testing_parameters_results/**` (not committed).

## 5. Signal / trade-rate diagnosis

| Strategy | Assessment | Jan 2025 smoke note |
|----------|------------|---------------------|
| pa_broad_channel_zone | **Too sparse** — zero trades | 0 trades — consistent |
| pa_climax_reversal | **High activity, weak edge** | Few trades in Jan; full window busy |
| pa_second_entry_pullback | **Too sparse** for strict gates (max 8 trades) | 0 in Jan; slightly nonzero in window |
| pa_wedge_reversal | **High activity, weak edge** | Few in Jan; full window busy |
| pa_buy_sell_close_trend | **Viable rate**; **cost / hold-time sensitive** | Active in Jan; full window strong count |
| pa_generic_breakout_pullback | **Too sparse** — zero trades | 0 trades — consistent |

## 6. Candidate selection

- **Strict thresholds:** `min_trades=30`, `min_profit_factor=1.05`, `min_total_r=0`, `max_drawdown_r=-50`, `max_avg_bars_held=120`, `max_eod_count=0`, `max_end_of_data_count=0`, `top_per_strategy=5`.
- **Strict YAML count:** **5**, all **`pa_buy_sell_close_trend`**.
- **Metadata families with strict candidates:** **one** — `pa_close_trend_continuation` (Batch C only). No Batch B family passes strict gates.
- **No strict candidates:** `pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`, `pa_generic_breakout_pullback` (`no_candidate_strategies.txt`).
- **Diagnostic relaxed:** run recorded under `diagnostic_relaxed_selection/` (**DIAGNOSTIC ONLY**); only `pa_buy_sell_close_trend` produced rows at relaxed thresholds; duplicate YAMLs omitted on purpose.

## 7. Candidate sanity

- **Fast context:** `check_selected_candidates_fast_context.py` on **2023-01-03 → 2023-01-31**, all **5** strict YAMLs → **ok** (`candidate_fast_context_check.*`).
- **LOOKAHEAD:** preflight + repo boundary checks — no lookahead tokens in required feature sets for these strategies.

## 8. Interpretation (per strategy)

| Strategy | Classification |
|----------|----------------|
| pa_broad_channel_zone | **TOO_SPARSE_NEEDS_GRID_TUNE** |
| pa_climax_reversal | **SIGNAL_RATE_OK_BUT_WEAK_EDGE** |
| pa_second_entry_pullback | **TOO_SPARSE_NEEDS_GRID_TUNE** |
| pa_wedge_reversal | **SIGNAL_RATE_OK_BUT_WEAK_EDGE** |
| pa_buy_sell_close_trend | **PROMISING_LAYER1_CANDIDATE** + **COST_SENSITIVE_NEEDS_LAYER2_CHECK** |
| pa_generic_breakout_pullback | **TOO_SPARSE_NEEDS_GRID_TUNE** |

## 9. Decision

**TUNE_PA_BATCH_BC_GRIDS_FIRST**

**Rationale:** Only **one** strategy family (**Batch C** close-trend) yields strict Layer 1 candidates; **Batch B** contributes **no** strict passes (zero-trade or negative edge at scale). That does **not** meet the bar for a cross-batch **reduced Layer 2** design spanning B+C. The path forward is to **widen or re-axis focused grids** (especially for zero-trade and tiny-n strategies) and re-run Layer 1 before committing combiner work.

## 10. Explicit non-runs

- PA Batch B/C **Layer 2** not run  
- **mini-WFO** not run  
- **Full WFO** not run  
- **Live / paper** not run  

No `reduced_layer2_pa_batch_bc_design.md` (decision is not **PROCEED**).
