# Global Layer 1 summary (QQQ, in-sample)

- window: `2023-01-01` → `2024-12-31`
- tag: `layer1_global_qqq_2023_2024_v2`
- manifest_rows: **30**
- strict_selected_yaml: **81**

Interpretation: in-sample sweep rankings; not live-ready.

## Manifest overview

| strategy | family | status | raw_grid_size | result_rows | best_total_r | best_profit_factor | best_max_drawdown_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| adx_dmi_trend_continuation | trend_strength_continuation | ok | 32 | 32 | -46.679191410842925 | 1.0440646025854992 | -69.09039290866416 |
| cci_extreme_snapback | oscillator_reversal | ok | 32 | 32 | 0.4368487050840561 | 1.9451754385964903 | -2.0403603603603235 |
| large_candle_failure | price_action_failure | ok | 32 | 32 | -19.081422245580416 | 0.9890318203334268 | -46.31019654299072 |
| macd_momentum_turn | macd_momentum_shift | ok | 32 | 32 | 11.698983494032298 | 1.090355037410327 | -16.9189125746812 |
| multi_day_level_trap | multi_day_level_trap | ok | 32 | 32 | 4.5487671547494095 | 1.4199218750000608 | -6.265579726514017 |
| prior_close_reclaim | value_reclaim | ok | 32 | 32 | 7.60407941310537 | 1.629032373574469 | -7.949179415074949 |
| stochastic_oversold_cross | oscillator_reversal | ok | 32 | 32 | 38.05416199327347 | 1.2154160046857063 | -14.508229608959262 |
| supertrend_atr_flip | atr_trend_following | ok | 32 | 32 | 19.992991064042485 | 1.1205485790154186 | -19.675038945204943 |
| sma20_reclaim_reject | moving_average_reclaim | ok | 64 | 64 | -1.415905515637168 | 0.9702985101900804 | -25.058500471547102 |
| pa_wedge_reversal | pa_wedge_reversal | ok | 144 | 144 | -1.4662761713651682 | 1.0266687340104277 | -11.040696739722325 |
| gap_acceptance_failure | gap_behavior | ok | 192 | 192 | 20.00108438327635 | 1.577570480928719 | -6.023748222814444 |
| afternoon_continuation | afternoon_trend | ok | 256 | 256 | 10.417147784806946 | 1.2851432880845386 | -5.006677691074555 |
| orb_retest_continuation | opening_momentum | ok | 256 | 256 | -1.8004709980606783 | 1.018090632276578 | -27.735820981926963 |
| vwap_reversal | mean_reversion | ok | 480 | 480 | -70.7337461449601 | 1.1873619138326246 | -72.85884499213734 |
| orb_continuation | opening_momentum | ok | 512 | 512 | 5.399337685516121 | 1.0639438000326902 | -23.188338875048775 |
| prior_day_level_trap | key_level_trap | ok | 512 | 512 | 10.837863477853546 | 1.0392674766684609 | -13.417503221133606 |
| vwap_reclaim_reject | vwap_reclaim | ok | 512 | 512 | 28.38448860569918 | 1.2222127804215297 | -7.374574138597863 |
| vwap_trend_pullback | vwap_trend | ok | 512 | 512 | 8.899917093091727 | 1.210980876002508 | -17.377517111655813 |
| bollinger_squeeze_breakout | volatility_expansion | ok | 576 | 72 | 6.823118116136275 | 1.04829675045989 | -21.413602703141866 |
| pa_failed_range_breakout_trap | pa_range_breakout_failure | ok | 576 | 576 | 34.88500285947301 | 1.329076539833796 | -43.20632030970974 |
| pa_generic_breakout_pullback | pa_breakout_pullback | ok | 576 | 576 | 0.0 | 0.0 | 0.0 |
| pa_second_entry_pullback | pa_second_entry | ok | 576 | 576 | 1.444444444444655 | inf | 0.0 |
| pa_trading_range_bls_hs | pa_trading_range | ok | 576 | 288 | 25.57343522621101 | 1.469831727562135 | -22.172181130782096 |
| failed_orb | opening_reversal | ok | 768 | 768 | 3.8738176791134906 | 1.2030111968692587 | -15.798669579456956 |
| pa_mtr_reversal | pa_major_trend_reversal | ok | 768 | 768 | 3.7464716448556095 | inf | 0.0 |
| pa_tight_channel_pullback | pa_channel_pullback | ok | 768 | 768 | 0.8710509348807959 | inf | 0.0 |
| rsi_failure_swing | oscillator_reversal | ok | 768 | 128 | 4.80386363694312 | 1.525360824742347 | -8.281018809208064 |
| pa_broad_channel_zone | pa_broad_channel | ok | 972 | 972 | 0.0 | 0.0 | 0.0 |
| pa_buy_sell_close_trend | pa_close_trend_continuation | ok | 1152 | 1152 | 41.56264706078157 | 1.260109394287692 | -13.77849607688373 |
| pa_climax_reversal | pa_climax_reversal | ok | 1152 | 1152 | 5.910439715605149 | 1.3580040526850088 | -6.290149133855962 |

## Gate snapshot

See `global_layer2_gate_decision.md`.
