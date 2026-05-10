# Grid review — PA Batch A tuned v1

| strategy | tuned_yaml | raw_grid_size | capped | max_combos | notes |
|----------|------------|---------------|--------|------------|--------|
| pa_trading_range_bls_hs | pa_trading_range_bls_hs_tuned_v1.yaml | 576 | false | — | Dropped `upper_third` target_mode vs draft to save axis budget; stricter score/range width |
| pa_failed_range_breakout_trap | pa_failed_range_breakout_trap_tuned_v1.yaml | 576 | false | — | No `confirm_mode` in strategy; swept `fail_window_bars`, `require_tr_regime`, holds |
| pa_tight_channel_pullback | pa_tight_channel_pullback_tuned_v1.yaml | 768 | false | — | Single `pa_regime_window` (30); loosened scores / pullback depth |
| pa_mtr_reversal | pa_mtr_reversal_tuned_v1.yaml | 768 | false | — | Uses `bear_channel_score_min` / `require_wedge_proxy` (code keys); two target_r levels |

All raw grids **≤1500** — run **full** sweeps (no silent cap).

Dedupe: expect fewer **unique** rows than raw grid if `normalized_param_key` collapses some axes (same as prior Layer 1).
