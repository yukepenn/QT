# Grid review — PA Batch B/C tuned v2

| Strategy | Raw grid | ≤1500 | Blocker addressed | Notes |
|----------|---------:|-------|---------------------|-------|
| `pa_broad_channel_zone` | 972 | yes | Zone gate (`zone_max_frac`) | First grid axis `0.5` so first-combo preflight is not stuck at 1/3 |
| `pa_generic_breakout_pullback` | 576 | yes | Geometry / followthrough | `recent_breakout_lookback` fixed at 6 to keep grid lean |
| `pa_buy_sell_close_trend` | 576 | yes | Hold / exit profile vs v1 | Longer `max_hold_minutes`; moderate filters |
| `pa_climax_reversal` | 576 | yes | Robustness vs v1 | No target_mode expansion beyond `fixed_r` |
| `pa_second_entry_pullback` | 576 | yes | Sparse second entries | Looser `context_score_min`, deeper pullback |
| `pa_wedge_reversal` | 144 | yes | Wedge quality retest | Single `atr_buffer` stop mode |

No unsupported YAML keys; no silent caps.
