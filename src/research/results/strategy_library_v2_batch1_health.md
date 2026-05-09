# Strategy Library v2 Batch 1 — health (smoke)

QQQ **2025-01-01 → 2025-01-31**, `--max-combos 24`, `--min-trades 1`, `--no-save`, `--profile`. Engine: **numba_fast** for all six.

| strategy | exit | runtime_sec | combos | best_trades | best_total_r | best_pf | warnings |
|----------|-----:|------------:|-------:|------------:|-------------:|--------:|----------|
| intraday_ma_crossover | 0 | 0.538 | 24 | 18 | -0.654 | 0.761 | — |
| rsi_failure_swing | 0 | 0.555 | 24 | 7 | 0.618 | 3.833 | — |
| bollinger_squeeze_breakout | 0 | 0.807 | 24 | 20 | -1.678 | 0.692 | channels `PerformanceWarning` (fragmented frame) |
| bollinger_band_fade_chop | 0 | 0.854 | 24 | 19 | -3.877 | 0.806 | channels + regime `PerformanceWarning` |
| donchian_channel_breakout | 0 | 0.549 | 24 | 1 | -1.038 | 0.0 | only 6 post-filter rows had trades; very sparse |
| consecutive_bar_exhaustion | 0 | 0.528 | 24 | 19 | -6.123 | 0.579 | — |

**Layer 1 spot-check (partial):** `rsi_failure_swing` on **2023-01-01 → 2024-12-31** (capped sweep + `select_candidates`) → `src/research/results/layer1_v2_batch1_qqq_2023_2024/`.
