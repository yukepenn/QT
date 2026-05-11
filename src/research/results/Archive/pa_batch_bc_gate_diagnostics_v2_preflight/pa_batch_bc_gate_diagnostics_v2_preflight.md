# PA Batch B/C — gate diagnostics v2 preflight

**Window:** QQQ 2023-01-01 → 2024-12-31. **First combo** from each tuned v2 YAML.

| Strategy | final_valid_signals | Preflight note |
|----------|--------------------:|----------------|
| `pa_broad_channel_zone` | 0 | First combo uses `zone_max_frac=2/3`, `broad_bull_score_min=0.16`; zone gate passes **1** bar but pullback/reversal chain stays **0**. |
| `pa_generic_breakout_pullback` | 0 | Still zero finals on first combo → **DEFER** full sweep. |
| `pa_buy_sell_close_trend` | 434 | Proceed to sweep. |
| `pa_climax_reversal` | 90 | Proceed to sweep. |
| `pa_second_entry_pullback` | 26 | Proceed to sweep (sparse but nonzero). |
| `pa_wedge_reversal` | 91 | Proceed to sweep. |

See `pa_batch_bc_gate_diagnostics_v2_preflight.csv` (copy of `pa_gate_rows.csv`).
