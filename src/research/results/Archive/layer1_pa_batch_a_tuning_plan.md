# PA Batch A — grid/gate tuning plan (v1)

## Why `TUNE_PA_BATCH_A_GRIDS_FIRST`

Formal Layer 1 (`layer1_pa_batch_a_qqq_2023_2024`) exported **four strict YAMLs**, all **`pa_failed_range_breakout_trap`**. **`pa_trading_range_bls_hs`** had high trade counts but **negative best total R** under strict `min_total_r ≥ 0`. **`pa_tight_channel_pullback`** and **`pa_mtr_reversal`** were **too sparse** on the focused grids for meaningful economics. Reduced Layer 2 design needs **multi-family** candidates or explicit defer — tuning grids/gates first avoids premature Layer 2 work.

## Per-strategy diagnosis (from Layer 1 manifest / summaries)

| Strategy | Issue |
|----------|--------|
| pa_trading_range_bls_hs | Strong PF row still **negative total R**; needs **stricter quality** (score / range width / confirm) and **targets/stops** that fit range geometry — **not** maximizing trades. |
| pa_failed_range_breakout_trap | Best family; **maxDD ~ -47 R** near strict gate; explore **fail_window**, **require_tr_regime**, **stop/target modes** for quality vs churn. |
| pa_tight_channel_pullback | **Max ~14 trades** per combo — loosen **`tight_bull_score_min`**, **`max_pullback_depth_atr`**, **`block_climax`**, regime window. |
| pa_mtr_reversal | **Max 1 trade** — loosen **`bear_channel_score_min`**, **`require_wedge_proxy`**, **`pa_range_window`** (actual keys in code; no `test_mode` in plugin). |

## Tuning goals

1. **Failed trap:** preserve edge; seek **better DD / R** tradeoff with **≥30 trades** where possible.
2. **Trading range:** improve **total R** with **quality filters** (`trading_range_score_min`, `min_range_width_atr`, `confirm_mode`).
3. **Tight channel:** raise **signal rate** for discovery without VWAP-side lock-in (`require_vwap_side` stays false).
4. **MTR:** diagnostic loosening only — **no** forced candidate density.

## New YAMLs (do not overwrite `*_focused.yaml`)

| File | Raw grid (validator) |
|------|----------------------|
| `pa_trading_range_bls_hs_tuned_v1.yaml` | 576 |
| `pa_failed_range_breakout_trap_tuned_v1.yaml` | 576 |
| `pa_tight_channel_pullback_tuned_v1.yaml` | 768 |
| `pa_mtr_reversal_tuned_v1.yaml` | 768 |

All **≤1500** — **full grid**, **no `--max-combos` cap**.

## Unsupported user-draft keys (omitted by design)

- **Failed trap:** no `confirm_mode` / `min_break_atr` in strategy code — not swept.
- **MTR:** no `test_mode`, `confirm_mode`, `min_reversal_structure_score`, `require_trendline_break_proxy` — plugin uses **`bear_channel_score_min`**, **`require_wedge_proxy`**, **`wedge_push_min`**.

## Strict candidate thresholds (Layer 1 selection)

Same as prior formal Layer 1:

- `min_trades`: 30  
- `min_profit_factor`: 1.05  
- `min_total_r`: 0  
- `max_drawdown_r`: -50  
- `max_avg_bars_held`: 120  
- `max_eod_count`: 0  
- `max_end_of_data_count`: 0  
- `top_per_strategy`: 5  

## Explicit non-runs

- PA **Layer 2**, **mini-WFO**, **full WFO**, **live/paper** — **not** in this phase.
