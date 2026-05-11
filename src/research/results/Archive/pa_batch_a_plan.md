# PA Batch A — plan (Brooks-style branch)

## Purpose

Introduce a **deterministic price-action (PA) branch**: generic PA features and coarse regime scores first, then a small set of **Batch A** strategy plugins. This avoids subjective candle-pattern shortcuts and avoids duplicating existing ORB / VWAP / gap / trap strategy logic under new names.

## No-lookahead rules

- **Current-bar** shape features (body/wick, inside/outside bar flags, etc.) are allowed; the engine enters on the **next** bar after a signal at bar close.
- **Rolling swing / range** features (`pa_prior_*`, range thirds, breakouts, failed breakouts, pullback depth, wedge proxy) must be **prior-exclusive** (rolling extrema **shifted by one** within session) — **no centered rolling pivots**, **no future bars** in swing legs.
- PA Batch A strategies must **not** list any `*_LOOKAHEAD` column in `required_features`.

## Why PA must not duplicate ORB / VWAP / gap / trap

- **ORB**, **VWAP**, **gap**, and **trap** families already have dedicated plugins and curated grids; PA Batch A targets **generic rolling-range** and **coarse regime** behavior (trading-range scalp, failed range breakout, tight-channel pullback, major-trend-reversal proxy) using **`pa_*`** columns, not re-labeled ORB/VWAP/gap rules.

## Feature files (this phase)

- `src/features/price_action.py` — bar microstructure (ATR-free ratios, streaks, overlap/tail).
- `src/features/pa_swings.py` — prior-exclusive range / breakout / failed-break / leg / pullback / wedge proxy.
- `src/features/regime.py` — coarse `pa_*_score_*` and follow-through helpers (consumes `pa_swings` + existing regime inputs).
- `src/features/levels.py` — optional `near_*_atr` proximity (where ATR + anchors exist).
- `src/features/build_types.py`, `feature_config.py`, `feature_key.py`, `build_features.py` — `PaFeatureConfig`, registry, key materialization, pipeline order (**channels → pa_swings → pa_proximity → regime**).

## Batch A strategies (four only)

1. `pa_trading_range_bls_hs` — trading-range buy-low / sell-high long MVP.
2. `pa_failed_range_breakout_trap` — failed **rolling-range** breakdown trap (not ORB).
3. `pa_tight_channel_pullback` — tight **bull** channel pullback long MVP.
4. `pa_mtr_reversal` — coarse major-trend-reversal long MVP.

## Explicit non-runs (this phase)

- No formal **Layer 1** 2023–2024 PA sweep unless explicitly approved after review.
- No **Layer 2**, **mini-WFO**, **full WFO**, **live/paper**.
- No **SPY**, no **IBKR pull** in scope.
- No PA Batch B/C; no deletion of tests, `selected_candidates/*.yaml`, or curated summaries.

## Validation plan

- Unit: `tests/test_pa_features_no_lookahead.py`, registration + per-strategy signal tests.
- Parity: `check_strategy_fast_parity.py` on QQQ Jan 2025 with each `*_focused.yaml` (small `--max-combos`).
- Smoke: `build_features_from_config` on QQQ Jan 2025 with PA default YAML; `sweep.py` Jan 2025 capped combos (`--tag pa_batch_a_jan2025_smoke`).
- Regression: `failed_orb` parity unchanged; `loader.py --list` count **29**.
