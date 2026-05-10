# Strategy Library v2 — completion health (Jan 2025 QQQ)

Capped sweeps: `--max-combos` 20–30, `--min-trades 1`, `--no-save`, equity **QQQ**, `2025-01-01` → `2025-01-31`.

| Strategy | Jan smoke | Notes |
|----------|-----------|--------|
| sma20_reclaim_reject | OK | Grid 64; smoke capped at 20 combos |
| macd_momentum_turn | OK | Ensure `features.indicators.macd_tuples` covers all `(macd_fast, macd_slow)` pairs from the focused grid |
| stochastic_oversold_cross | OK | |
| cci_extreme_snapback | OK | |
| adx_dmi_trend_continuation | OK | |
| supertrend_atr_flip | OK | Needs `vol_windows` including each supertrend `atr_window` |
| large_candle_failure | OK | |
| multi_day_level_trap | OK | Distinct anchors vs `prior_day_level_trap`; some conceptual overlap |
| prior_close_reclaim | OK | |

**Optional 2023–2024 capped smoke:** not run in this phase (summary scope: code + Jan wiring).

**Recommendation:** `RUN_LAYER1_V2_COMPLETION_2023_2024` when ready for economics.
