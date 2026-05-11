# Strategy Library v2 — implementation plan (completion)

**Loader count:** 25 strategies (16 legacy + 9 completion). **Constraint:** no strategy-specific code in `fast.py` / `sweep.py`; all new logic in `src/strategies/strategy/*.py` + feature modules.

## Decision table

| Strategy | Existed? | Feature support | Template | New files | Risk | Action |
|----------|----------|-----------------|----------|-----------|------|--------|
| sma20_reclaim_reject | No | SMA/EMA + ATR + VWAP | vwap_reclaim / MA | strategy + YAMLs | Grid vs line column | Implemented |
| macd_momentum_turn | No | MACD + EMA20 | intraday_ma / rsi | strategy + YAMLs | Grid pair vs tuples | Superset macd_tuples in YAML |
| stochastic_oversold_cross | No | Stochastic | rsi_failure_swing | strategy + YAMLs | Parameter alignment | Implemented |
| cci_extreme_snapback | No | CCI | rsi_failure_swing | strategy + YAMLs | Threshold sign | Implemented |
| adx_dmi_trend_continuation | No | ADX/DMI + EMA | intraday_ma | strategy + YAMLs | ADX warmup | Implemented |
| supertrend_atr_flip | No | Supertrend (new) | trend style | strategy + YAMLs | vol_window vs atr_window | vol_windows includes atr_window |
| large_candle_failure | No | bar_range + is_red | failed_orb-ish | strategy + YAMLs | State scan cost | O(n²) local scan; MVP OK |
| multi_day_level_trap | No | Multi-day lows | prior_day_level_trap | strategy + YAMLs | Overlap narrative | Document vs prior_day |
| prior_close_reclaim | No | prior_day_close | vwap_reclaim | strategy + YAMLs | Distinct from gap | Implemented |

## Files not touched

- `src/backtest/fast.py`, `src/backtest/sweep.py` (no edits)
- `data/raw/**`
- Heavy combiner/walkforward result trees

## Files patched

- `src/features/build_types.py`, `feature_key.py`, `indicators.py`, `feature_config.py`, `levels.py`
- `src/strategies/loader.py`, `metadata.yaml`
- `tests/test_indicators_features.py`
