# Trade enrichment summary

- rows_in: 1000
- rows_out: 1000
- unmatched_trades (no minute_from_open after join): 0
- timestamp_policy: `merge_asof_backward_on_entry_ts_utc_vs_feature_ts_utc`
- regime_window: 20
- output: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/trade_quality_router_v1_5/enriched_staging/indicator_completion_mtp2_enriched.csv`

## Feature columns merged

```
[
  "above_orb_high",
  "atr_like_20",
  "below_orb_low",
  "close_above_vwap",
  "close_below_vwap",
  "compression_score_20",
  "minute_from_open",
  "near_orb_high_known_atr",
  "near_orb_low_known_atr",
  "near_prior_close_atr",
  "near_prior_day_high_atr",
  "near_prior_day_low_atr",
  "near_rolling_high_20_atr",
  "near_rolling_low_20_atr",
  "near_session_open_atr",
  "near_vwap_atr",
  "near_vwap_lower_1_atr",
  "near_vwap_lower_2_atr",
  "near_vwap_upper_1_atr",
  "near_vwap_upper_2_atr",
  "orb_high_dist",
  "orb_low_dist",
  "orb_width_pct",
  "pa_always_in_side_20",
  "pa_climax_score_20",
  "pa_distance_from_vwap_atr",
  "pa_late_trend_score_20",
  "pa_limit_order_market_score_20",
  "pa_regime_label_20",
  "pa_strong_breakout_score_20",
  "pa_trade_mode_20",
  "pa_trading_range_score_20",
  "pa_trend_to_tr_transition_score_20",
  "range_efficiency_20",
  "trend_score_20",
  "vwap_cross_count_20",
  "vwap_slope_20"
]
```

## Missing optional feature columns

```
[]
```
