# Strategy Library v2 — feature audit (completion)

## Reused columns

- **MACD / stoch / CCI / ADX:** existing `indicators.py` pipelines.
- **EMA/SMA slopes:** existing.
- **ATR-like:** `volatility.atr_like_{w}`.
- **VWAP / price action / ORB:** unchanged.
- **Prior close / session open:** `levels.py` (`prior_day_close`, `session_open`, gaps).

## Added columns

| Column | Module | Rule |
|--------|--------|------|
| `supertrend_line_{atr}_{mult_z}`, `supertrend_dir_{atr}_{mult_z}` | indicators | Session-scoped SuperTrend; uses `atr_like_{atr}`; mult_z = round(mult*100). |
| `prior_3day_low`, `prior_5day_low`, `previous_week_low` | levels | Min completed-session lows over prior 3/5 sessions; prior ISO week min low. |

## Strategy-specific thresholds

Oscillator oversold levels, MACD trigger interpretation, and reclaim buffers remain **signal config**, not extra feature columns.

## Tests

- `tests/test_strategy_library_v2_completion_features.py` — multi-day columns + supertrend feature key.
- `tests/test_levels_multiday_no_lookahead.py` — prior 3-day low matches manual expectation on synthetic sessions.
