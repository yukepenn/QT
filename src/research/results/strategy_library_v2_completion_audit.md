# Strategy Library v2 — architecture audit (completion)

| Strategy | File | Fast | Tier | Context | norm_key | Numba | LOOKAHEAD in required_features |
|----------|------|------|------|---------|----------|-------|--------------------------------|
| sma20_reclaim_reject | sma20_reclaim_reject.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| macd_momentum_turn | macd_momentum_turn.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| stochastic_oversold_cross | stochastic_oversold_cross.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| cci_extreme_snapback | cci_extreme_snapback.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| adx_dmi_trend_continuation | adx_dmi_trend_continuation.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| supertrend_atr_flip | supertrend_atr_flip.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| large_candle_failure | large_candle_failure.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| multi_day_level_trap | multi_day_level_trap.py | yes | A_true_context_fast_core | yes | yes | yes | no |
| prior_close_reclaim | prior_close_reclaim.py | yes | A_true_context_fast_core | yes | yes | yes | no |

**Repo checks:** No edits to `fast.py` / `sweep.py` for strategy branching. Single `feature_key_from_config` path. Jan 2025 smokes: wiring OK (see health pack).
