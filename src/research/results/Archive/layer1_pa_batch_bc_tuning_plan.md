# PA Batch B/C — Layer 1 grid/gate tuning plan (v1)

Date: 2026-05-10  
Baseline root: `src/research/results/layer1_pa_batch_bc_qqq_2023_2024/`  
Tuned root (this phase): `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`  
Tag: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`

## Purpose

Baseline formal Layer 1 for PA Batch B/C on QQQ 2023–2024 produced **strict candidates from only one family** (`pa_buy_sell_close_trend` / `pa_close_trend_continuation`). Several strategies were **zero-trade** or **high-activity but weak edge**. This phase performs a **grid/gate tuning pass** to determine whether:

- Zero-trade strategies can be made to trade (or are structurally impossible under current logic).
- Sparse-but-promising strategies can reach a usable trade count without destroying economics.
- High-activity strategies can be tightened into PF ≥ 1.05 candidates.
- `pa_buy_sell_close_trend` can reduce hold-time/cost fragility while preserving edge.

## Decision basis (why `TUNE_PA_BATCH_BC_GRIDS_FIRST`)

From baseline `layer1_pa_batch_bc_summary.md`:

- `pa_broad_channel_zone`: **ok_zero_trade** (all rows 0 trades)
- `pa_generic_breakout_pullback`: **ok_zero_trade** (all rows 0 trades)
- `pa_second_entry_pullback`: **tiny-n** (max 8 trades) despite strong PF corner
- `pa_climax_reversal`, `pa_wedge_reversal`: **high activity, weak edge** (PF < 1.0 at scale)
- Strict selected candidates: **5 YAMLs**, all `pa_buy_sell_close_trend`

That does **not** justify reduced Layer 2 design yet; we need at least a second family showing strict (or near-strict) viability.

## Scope

- **Asset/symbol/window:** equity / QQQ / 2023-01-01 → 2024-12-31
- **Strategies (6):**
  - Batch B: `pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`
  - Batch C: `pa_buy_sell_close_trend`, `pa_generic_breakout_pullback`
- **Grid artifacts:** create **new** tuned grids only (`*_tuned_v1.yaml`), do not overwrite focused YAMLs.

## Per-strategy tuning intent

### 1) `pa_broad_channel_zone` — **grid-tune + gate diagnose**

- **Problem:** all-zero trades on QQQ 2023–2024.
- **Hypothesis:** either (a) confirmation / context gates too strict, or (b) signal definition is too rare given feature scales.
- **Action:** widen entry window, lower score thresholds, loosen pullback depth constraints, and try alternative stop/target combos that do not require rare structure.
- **Success criteria:** any sustained nonzero trade count on tuned grid; then evaluate PF/total_r under strict filters.

### 2) `pa_generic_breakout_pullback` — **grid-tune + gate diagnose**

- **Problem:** all-zero trades on QQQ 2023–2024.
- **Action:** loosen followthrough requirement, loosen breakout overlap constraints, allow deeper pullbacks, expand entry window, and validate stop/target modes are reachable.
- **Success criteria:** nonzero trades for a meaningful portion of the grid; then strict PF/total_r viability.

### 3) `pa_second_entry_pullback` — **grid-tune (increase trade count)**

- **Problem:** best corner has PF>2 but max trades=8 → cannot meet `min_trades=30`.
- **Action:** widen entry window, loosen context score thresholds and/or trend-context requirement (if supported), allow larger max_hold where needed.
- **Success criteria:** increase max/median trades materially (target: max trades ≳ 30) while keeping PF ≥ 1.05 on at least some rows.

### 4) `pa_climax_reversal` — **quality tightening**

- **Problem:** high trade counts but negative edge.
- **Action:** isolate which axis choices contribute most to losses (target/stop modes, vwap distance, bar-range expansion gates, entry window).
- **Success criteria:** find rows with PF ≥ 1.05 and nontrivial trades (≥30).

### 5) `pa_wedge_reversal` — **quality tightening**

- **Problem:** high activity, PF < 1.0.
- **Action:** tighten wedge proxy and/or context gates, reduce noisy windows, reduce poor stop/target combos.
- **Success criteria:** PF ≥ 1.05 with ≥30 trades.

### 6) `pa_buy_sell_close_trend` — **hold-time / cost sensitivity reduction**

- **Problem:** viable strict candidates exist but are **slow** (avg bars held ~55–61) and `cost_sensitivity: high`.
- **Action:** test shorter `backtest.max_hold_minutes`, explore slightly stronger entry gates (body_pct/trend_score), and keep target mode fixed-r only.
- **Success criteria:** preserve PF/total_r while reducing avg_bars_held and/or improving robustness across grid rows.

## Grid rules for tuned v1 YAMLs

- **Raw grid size:** ≤ 1500 per strategy (prefer 300–900)
- **No silent caps:** if raw grid >1500, reduce axes before running
- **Only supported keys:** must pass `strategy.validate_config` (unsupported suggestions omitted and documented)
- **Avoid duplicate-heavy axes:** baseline dedup was significant; tuned grids should not amplify duplication unnecessarily

## Candidate selection thresholds (strict)

Same as baseline strict selection:

- `min_trades=30`
- `min_profit_factor=1.05`
- `min_total_r=0`
- `max_drawdown_r=-50`
- `max_avg_bars_held=120`
- `max_eod_count=0`
- `max_end_of_data_count=0`
- `top_per_strategy=5`

## Explicit non-runs

- **No** Layer 2 run or design doc unless tuned Layer 1 produces strict candidates from ≥2 families
- **No** mini-WFO / full WFO
- **No** live/paper
- **No** new strategies
- **No** feature formula changes unless a clear bug is proven
- **No** strategy logic changes unless a clear bug is proven

