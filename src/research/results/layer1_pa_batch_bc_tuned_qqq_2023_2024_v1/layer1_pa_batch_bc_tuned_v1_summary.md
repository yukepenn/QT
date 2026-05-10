# PA Batch B/C — tuned Layer 1 v1 summary (QQQ 2023–2024)

Tag: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`  
Curated root: `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`

## 1. Purpose

Grid/gate tuning pass after baseline PA Batch B/C Layer 1 (`layer1_pa_batch_bc_qqq_2023_2024/`) produced strict candidates from **only one family** (`pa_buy_sell_close_trend`). Goal: determine whether **another** PA Batch B/C family can produce strict candidates, without running Layer 2 / WFO.

## 2. Baseline recap (why tuning)

Baseline key outcomes:

- `pa_broad_channel_zone`: zero-trade
- `pa_generic_breakout_pullback`: zero-trade
- `pa_second_entry_pullback`: tiny-n (max 8 trades) but high-PF corner
- `pa_climax_reversal`, `pa_wedge_reversal`: high activity but PF < 1.0
- Strict candidates: **5** YAMLs, all `pa_buy_sell_close_trend` → decision **`TUNE_PA_BATCH_BC_GRIDS_FIRST`**

## 3. Tuning diagnosis inputs

- Baseline row/axis hints: `prior_row_diagnosis.{csv,md}`
- Tuned grids: `src/strategies/testing_parameters/*_tuned_v1.yaml` (sizes in `grid_review.*`)

## 4. Tuned YAMLs

| strategy | tuned grid | raw_grid_size | intent |
|----------|------------|--------------:|--------|
| pa_broad_channel_zone | `pa_broad_channel_zone_tuned_v1.yaml` | 864 | attempt to recover signal rate |
| pa_climax_reversal | `pa_climax_reversal_tuned_v1.yaml` | 1296 | tighten quality (drop vwap target; stronger context) |
| pa_second_entry_pullback | `pa_second_entry_pullback_tuned_v1.yaml` | 1152 | increase trade counts (looser gates) |
| pa_wedge_reversal | `pa_wedge_reversal_tuned_v1.yaml` | 432 | tighten wedge proxy (fixed-r only) |
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_tuned_v1.yaml` | 324 | shorten holds + stronger body/trend filters |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_tuned_v1.yaml` | 1024 | attempt to recover signal rate (loosen followthrough, overlap) |

## 5. Sweep results

See `sweep_manifest.*`. Highlights (best PF row per strategy):

| strategy | status | result_rows | best_trades | best_total_r | best_PF | best_maxDD_R | best_avg_bars_held |
|----------|--------|------------:|------------:|-------------:|--------:|-------------:|-------------------:|
| pa_broad_channel_zone | ok_zero_trade | 0 | 0 | 0.0 | 0.000 | 0.0 | 0.0 |
| pa_climax_reversal | ok | 216 | 26 | +8.474 | 2.007 | -3.110 | 7.12 |
| pa_second_entry_pullback | ok | 192 | 2 | +1.281 | 2.539 | -1.130 | 1.00 |
| pa_wedge_reversal | ok | 72 | 68 | -0.290 | 1.055 | -7.197 | 7.51 |
| pa_buy_sell_close_trend | ok | 54 | 280 | +2.732 | 1.031 | -7.054 | 27.52 |
| pa_generic_breakout_pullback | ok_zero_trade | 0 | 0 | 0.0 | 0.000 | 0.0 | 0.0 |

## 6. Signal-rate comparison

See `signal_rate_diagnosis.*`. Key deltas vs baseline:

- **`pa_climax_reversal` improved**: now has PF>1 corners and strict passes.
- **`pa_second_entry_pullback` improved activity** (max trades increased materially vs baseline max=8), but best PF rows remain tiny-n and strict still fails.
- **`pa_buy_sell_close_trend` regressed** relative to baseline strict PF≥1.05: shortened hold-time reduced PF below strict.
- Two strategies remain **still_zero_trade** (`pa_broad_channel_zone`, `pa_generic_breakout_pullback`).

## 7. Candidate selection

- **Strict thresholds:** same as baseline (`min_trades=30`, PF≥1.05, total_r≥0, etc.). Command: `candidate_selection_config.md`.
- **Strict exports:** **5 YAMLs**, all `pa_climax_reversal` (`selected_candidates/`).
- **No strict candidates:** `no_candidate_strategies.txt`.
- **Diagnostic relaxed:** recorded under `diagnostic_relaxed_selection/` (**DIAGNOSTIC ONLY**). YAML exports are deleted intentionally.

## 8. Candidate sanity

Fast-context check (2023‑01‑03 → 2023‑01‑31): **all strict YAMLs ok** (`candidate_fast_context_check.*`).

## 9. Interpretation

- `pa_climax_reversal`: **PROMISING_LAYER1_CANDIDATE** (strict passes; still research-only)
- `pa_second_entry_pullback`: **IMPROVED_BUT_SPARSE**
- `pa_wedge_reversal`: **SIGNAL_RATE_OK_BUT_WEAK_EDGE** (PF barely >1, total_r negative)
- `pa_buy_sell_close_trend`: **PROMISING_BUT_COST_SENSITIVE** (trade rate ok; PF below strict under hold-time cuts)
- `pa_broad_channel_zone`, `pa_generic_breakout_pullback`: **TOO_SPARSE_NEEDS_GRID_TUNE** / still-zero-trade

## 10. Decision

**TUNE_PA_BATCH_BC_GRIDS_AGAIN**

Rationale: tuned v1 moved strict candidates from `pa_buy_sell_close_trend` to `pa_climax_reversal`, but still yields **only one family** under strict gates. Two strategies remain zero-trade; `pa_buy_sell_close_trend` needs a less-destructive hold/cost tweak to keep PF ≥ 1.05.

## 11. Explicit non-runs

- PA Batch B/C **Layer 2** not run  
- **mini-WFO** not run  
- **Full WFO** not run  
- **Live / paper** not run  

No reduced Layer 2 design doc in this phase (decision is not **PROCEED**).

