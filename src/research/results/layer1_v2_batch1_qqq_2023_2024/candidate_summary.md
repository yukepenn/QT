# Layer 1 v2 Batch 1 — candidate summary (partial)

**Scope:** QQQ, **2023-01-01 → 2024-12-31**, capped sweep `rsi_failure_swing` (`sweep_20260509_213539_layer1_v2_batch1_qqq_2023_2024`), then `select_candidates` (conservative thresholds).

**Exported:** 5 YAMLs in `selected_candidates/` (IDs `RSI_FAILURE_SWING_001` … `_005`).

**Top row (rank 1, `RSI_FAILURE_SWING_001`):** 68 trades, profit factor ≈ **1.82**, total R ≈ **8.53**, max drawdown R ≈ **-6.21**. Trigger: `price_break_3bar_high_after_oversold`, VWAP filter on, `swing_low` stop, RSI window 14, swing lookback 12.

Other Batch 1 strategies were not swept in this commit; see `strategy_library_v2_batch1_summary.md`.
