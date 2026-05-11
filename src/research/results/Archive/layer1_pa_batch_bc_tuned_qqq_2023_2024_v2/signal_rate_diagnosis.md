# Signal-rate diagnosis — baseline vs tuned v1 vs tuned v2

Numeric highlights from formal summaries (`layer1_pa_batch_bc_summary.md`, `layer1_pa_batch_bc_tuned_v1_summary.md`) and **best PF row** per swept strategy in tuned v2 (`sweep_manifest.csv`). Older sweeps pre-date full `normalized_param_key` consistency — interpret historical magnitude only.

| Strategy | Baseline (best row) | Tuned v1 (best row) | Tuned v2 (best PF row) |
|----------|---------------------|---------------------|-------------------------|
| pa_broad_channel_zone | 0 trades | 0 trades | **skipped** (preflight 0 finals) |
| pa_generic_breakout_pullback | 0 trades | 0 trades | **skipped** |
| pa_buy_sell_close_trend | 413 / +24R / PF 1.23 | 280 / +2.7R / PF 1.03 | **461 / +41.6R / PF 1.26** |
| pa_climax_reversal | 93 / −13.7R / PF 0.88 | 26 / +8.5R / PF 2.01 | **51 / +6.2R / PF 1.37** |
| pa_second_entry_pullback | 8 / +6.6R / PF 2.39 | 2 / +1.3R / PF 2.54 | **8 / +5.3R / PF 2.08** |
| pa_wedge_reversal | 126 / −10.1R / PF 0.96 | 68 / −0.29R / PF 1.06 | **54 / −1.47R / PF 1.03** |

**Class tags (v2):** broad/generic — **STILL_ZERO_TRADE / DEFER**; close-trend — **RECOVERED_SIGNAL_RATE** + strong PF vs v1; climax — **PROMISING_LAYER1_CANDIDATE** (moderate n); second-entry — **IMPROVED_BUT_SPARSE**; wedge — **SIGNAL_RATE_OK_BUT_WEAK_EDGE**.
