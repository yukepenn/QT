# Strategy Library v2 Batch 1 — health (Jan 2025 smoke)

Command: `sweep.py` QQQ 2025-01-01→2025-01-31, `--max-combos 50`, `--min-trades 1`, `--no-save`, `--profile`.

| strategy | exit | sec | combos | trades | total_r | PF | maxDD_r | warning |
|---|--:|---:|---:|---:|---:|---:|---:|---|
| intraday_ma_crossover | 0 | 1.303 | 50 | 18 | -0.654264 | 0.760925 | -3.102652 | negative_jan_smoke |
| rsi_failure_swing | 0 | 1.347 | 50 | 7 | 0.618422 | 3.832692 | -1.153907 | ok_for_layer1 |
| bollinger_squeeze_breakout | 0 | 1.565 | 50 | 20 | -1.662697 | 0.776503 | -5.594643 | negative_jan_smoke |
| bollinger_band_fade_chop | 0 | 1.625 | 50 | 19 | -3.876959 | 0.805917 | -8.256751 | negative_jan_smoke |
| donchian_channel_breakout | 0 | 1.304 | 50 | 20 | -5.947401 | 0.650238 | -8.238166 | negative_jan_smoke |
| consecutive_bar_exhaustion | 0 | 1.318 | 50 | 4 | 0.374799 | 0.586634 | -1.026316 | ok_for_layer1 |

