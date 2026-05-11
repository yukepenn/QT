## Hardening Commit B Plan — Feature no-lookahead + feature_key

- **Repo**: `QT/`
- **Branch**: `main`
- **Current HEAD (expected)**: `c48112a` (Docs(research): checkpoint before commit B)
- **Scope**: Commit B only (no Layer 3, no full Layer 1/2 reruns, no IBKR pull, no `data/raw` changes).

### Files inspected (current state)

#### Features

- `src/features/levels.py`
- `src/features/orb.py`
- `src/features/utils.py`
- `src/features/build_features.py`
- `src/features/feature_config.py`
- `src/features/time_features.py`
- `src/features/price_action.py`
- `src/features/volume.py`
- `src/features/vwap.py`
- `src/features/volatility.py`

#### Feature usage / caching call sites (to update)

- `src/backtest/engine.py`
- `src/backtest/sweep.py` (has local `_feat_key`)
- `src/combiner/candidate.py` (has local `_feat_key`)
- `src/research/run_layer1_focused.py`
- `src/research/check_strategy_fast_parity.py`

#### Strategy anchor helper (to extend)

- `src/strategies/strategy/fast_utils.py` (has `first_value_when_minute_ge`)
- `src/strategies/strategy/afternoon_continuation.py` (uses morning anchor)

### Confirmed lookahead / footguns

- **`src/features/levels.py`** currently emits:
  - `session_high`, `session_low`, `session_close` as **full-session aggregates** broadcast intraday (unsafe lookahead).
  - `session_open` is safe.
- **`src/features/orb.py`** broadcasts ORB levels to full session; safe only if gated by `after_orb`.

### Feature-key call sites found

- `src/backtest/sweep.py:_feat_key` (currently only `(orb_open_minutes, vwap_bands, vol_windows)`).
- `src/combiner/candidate.py:_feat_key` (same limitation).

### Proposed edits (Commit B)

#### B1 — Levels (no-lookahead)

- Rename unsafe full-session columns:
  - `session_high` → `full_session_high_LOOKAHEAD`
  - `session_low` → `full_session_low_LOOKAHEAD`
  - `session_close` → `full_session_close_LOOKAHEAD`
- Keep `session_open` as-is.
- Add safe intraday columns:
  - `intraday_high_so_far` = cummax of `high` by `session_date`
  - `intraday_low_so_far` = cummin of `low` by `session_date`
- Keep prior-day columns unchanged and computed from the (renamed) full-session aggregates.
- Update `src/features/feature_config.py` registry + descriptions accordingly.

#### B2 — ORB known columns

- Add `*_known` variants that are NaN/False before ORB completion (`after_orb == False`) and equal to broadcast values once ORB is known:
  - `orb_high_known`, `orb_low_known`, `orb_mid_known`, `orb_width_pct_known`
  - `above_orb_high_known`, `below_orb_low_known`
- Keep existing ORB columns unchanged for compatibility.
- Update `src/features/feature_config.py` registry + descriptions.

#### B3 — Anchor known helper

- Add a new helper alongside `first_value_when_minute_ge` that provides both:
  - `anchor_value` (broadcast)
  - `anchor_known` (False before target minute, True at/after once available)
- Keep the old helper for backward compatibility.
- Ensure any strategy that uses a broadcast anchor can gate on `anchor_known` (should be behavior-neutral when entry windows are already after the anchor minute).

#### B4/B5 — Centralized FeatureBuildConfig + feature key

- Add `src/features/feature_key.py`:
  - `FeatureBuildConfig`
  - `feature_config_from_strategy_config(cfg)`
  - `feature_key_from_config(cfg)` (hashable, stable, includes all knobs used by `build_basic_features`)
  - `build_features_from_config(raw_df, cfg)` (calls `build_basic_features` with config-derived knobs)
- Update all caching / feature-build call sites to use the shared key and builder:
  - remove or delegate local `_feat_key` implementations
  - ensure cache key includes `price_action_windows` and `volume_windows`

#### B6 — Prevent strategies from requiring LOOKAHEAD columns

- Add a validator that rejects required feature names containing `LOOKAHEAD` / `_LOOKAHEAD`.
- Call it during strategy loading / research preflight and in tests.

### Tests to add (Commit B)

- `tests/test_feature_no_lookahead.py`
- `tests/test_feature_key.py`

### Light smoke checks (post-change only)

- `python -m pytest ...`
- `python -m compileall -q src`
- `python src/strategies/loader.py --list`
- Small `read_bars` + `build_features` smoke on QQQ
- Parity smoke (small combos)
- Small combiner run with `--no-save` when available

