# Signal / trade-rate diagnosis — PA Batch B/C tuned v1 (QQQ 2023–2024)

Baseline comparison root: `src/research/results/layer1_pa_batch_bc_qqq_2023_2024/`.

This file summarizes tuned sweep activity; full details are in `signal_rate_diagnosis.csv`.

| strategy | max_trades | median_trades_nonzero | best_pf | best_total_r | classification |
|----------|-----------:|----------------------:|--------:|-------------:|----------------|
| pa_broad_channel_zone | 0 |  | 0.0000 | 0.0000 | still_zero_trade |
| pa_climax_reversal | 79 | 43.0 | 2.0067 | 8.4740 | improved |
| pa_second_entry_pullback | 52 | 10.5 | 2.5387 | 1.2814 | improved (but still sparse vs strict) |
| pa_wedge_reversal | 107 | 87.5 | 1.0553 | -0.2902 | no_change / weak edge |
| pa_buy_sell_close_trend | 401 | 355.0 | 1.0306 | 2.7316 | no_change (PF below strict) |
| pa_generic_breakout_pullback | 0 |  | 0.0000 | 0.0000 | still_zero_trade |

