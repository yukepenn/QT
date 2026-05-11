# Pre-sweep gate decision — tuned v2

**Rule:** Strategies with **preflight `final_valid_signals == 0`** are **DEFER** for full Layer 1 sweep (no proof-only burn unless explicitly requested).

| Strategy | Preflight finals | Decision |
|----------|------------------:|----------|
| `pa_broad_channel_zone` | 0 | **skipped_zero_signal_preflight** — zone widened (`zone_max_frac`) surfaces structural tension vs pullback/reversal chain; defer sweep until further implementation review or smaller proof grid. |
| `pa_generic_breakout_pullback` | 0 | **skipped_zero_signal_preflight** |
| `pa_buy_sell_close_trend` | 434 | **sweep** |
| `pa_climax_reversal` | 90 | **sweep** |
| `pa_second_entry_pullback` | 26 | **sweep** |
| `pa_wedge_reversal` | 91 | **sweep** |
