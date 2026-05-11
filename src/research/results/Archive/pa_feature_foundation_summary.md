# PA feature foundation — summary

## Smoke (QQQ 2025-01-01 → 2025-01-31)

Built features with **`pa_trading_range_bls_hs`** default parameter YAML via `build_features_from_config(read_bars(...), cfg)`:

- **Rows:** 7800 (RTH 1m bars in window).
- **`pa_*` column count:** 92 (all swing windows 10/20/30/60 plus regime windows 20/30/60 scores).
- **LOOKAHEAD in `pa_*` columns:** none (`lookahead_pa []`).

`src/features/build_features.py` CLI still uses **`build_basic_features`** only (no full strategy `features:` merge); full PA columns are validated through **`build_features_from_config`** as used by sweeps and tests.

## New / grouped PA columns (high level)

- **Bar shape (`price_action`):** `body_pct`, wick ratios, bull/bear/doji/inside/outside, `close_near_high` / `close_near_low`, reversal flags, consecutive bar counts, `overlap_bar`, `tail_bar`, etc.
- **Swings (`pa_swings`):** `pa_prior_high_N`, `pa_prior_low_N`, range mid/thirds/width/width ATR, `pa_breakout_*`, `pa_close_back_inside_*`, `pa_failed_breakout_*`, `pa_leg_direction_*`, `pa_pullback_depth_atr_*`, `pa_wedge_push_count_*`.
- **Regime (`regime`):** `pa_trading_range_score_*`, `pa_tight_bull_channel_score_*`, `pa_tight_bear_channel_score_*`, `pa_climax_score_*`, `pa_overlap_score_*`, `pa_strong_breakout_score_*`, `pa_followthrough_up_*` / `down_*`, etc.
- **Proximity (`levels`):** `near_prior_day_high_atr`, `near_vwap_atr`, `near_rolling_high_20_atr`, … (ATR-normalized distances where inputs exist).

## No-lookahead design

- Prior rolling highs/lows use **groupby(session_date)** + **`rolling(...).max/min.shift(1)`** so the current bar is excluded from the “prior” window.
- Failed / close-back-inside flags use **lagged** outside-range state where needed.
- No **centered** pivot windows; **delayed-confirmed** advanced pivots deferred.

## Known limitations

- PA regime scores are **coarse** and not heavily tuned.
- **Long-only MVP** for Batch A plugins.
- **Jan 2025 sweep:** `pa_tight_channel_pullback` and `pa_mtr_reversal` produced **0 trades** across evaluated combos (strict gates / window); not treated as a parity bug — see `pa_batch_a_jan2025_smoke.md`.

## Deferred

- Centered rolling pivots (explicitly out of scope).
- Richer delayed-confirmed swing labels.
