# PA Batch B/C tuned v3 — grid review

Both strategies use **full grids** (no silent cap) with **raw size 1152** each (≤ 1500).

| strategy | raw_grid_size | intent |
|----------|---------------|--------|
| `pa_buy_sell_close_trend` | 1152 | Wider entry grid + **`max_hold_minutes`** vs **`target_r`** trade-off; optional **`require_vwap_side`** for quality without exploding axis count. |
| `pa_climax_reversal` | 1152 | **Signal-first** axes (climax / bear / VWAP distance / entry window / bar-range expansion) with **`stop_mode`** and modest **`target_r` / `max_hold`** secondary axes. |

Validation: `validate_testing_grid_for_strategy` + `grid_size()` from `src.strategies.loader` on commit.
