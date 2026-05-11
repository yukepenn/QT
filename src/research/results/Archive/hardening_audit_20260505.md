## Research Platform Hardening Audit (Pre–Layer 3)

- **Repo**: `QT/`
- **Phase**: Research Platform Hardening Before Layer 3
- **Do not**: build Layer 3, add strategies, rerun full Layer 1/2 until hardening + tests are complete
- **Main branch commit inspected**: `3c38c1b` (Feat(research): finish QQQ 2020 layer2 v2)

### Scope inspected (Phase 0)

- **Backtest / execution**: `src/backtest/metrics.py`, `src/backtest/fast.py`, `src/backtest/engine.py`, `src/backtest/sweep.py`
- **Combiner**: `src/combiner/simulator.py`, `src/combiner/metrics.py`, `src/combiner/run.py`, `src/combiner/sweep.py`, `src/combiner/postprocess.py`, `src/combiner/candidate.py`
- **Features**: `src/features/*` (time/vwap/orb/levels/price_action/volume/volatility, build orchestration, registry)
- **Strategies**: `src/strategies/strategy/base.py`, `src/strategies/strategy/fast_utils.py`, 10 strategy plugin files, `src/strategies/metadata.yaml`
- **Strategy configs**: `src/strategies/parameters/*.yaml`, `src/strategies/testing_parameters/*_focused.yaml`
- **Research orchestration**: `src/research/scoring.py`, `src/research/select_candidates.py`, `src/research/run_layer1_focused.py`, `src/research/check_strategy_fast_parity.py`
- **Artifact policy**: `.gitignore`

---

## Executive summary

The platform is **functionally working** (Layer 1 candidate library + Layer 2 combiner run/sweep/postprocess), but several **correctness / validation / no-lookahead** issues exist and will make Layer 1/2 rankings **stale or misleading** once fixed. The hardening work should be done in ordered commit groups with tests, avoiding any heavy re-runs until correctness is enforced.

---

## Findings by priority (what is present right now)

### P0 — Execution correctness / validation

#### P0.1 Max drawdown starts from first cumulative value (present)

- **Present in**:
  - `src/backtest/metrics.py:max_drawdown` initializes `peak = x[0]`.
  - `src/backtest/fast.py:_max_dd_numba` initializes `peak = cum[0]`.
- **Impact**: If the **first trade is a loss**, drawdown is understated because the drawdown baseline implicitly becomes the first cumulative value instead of 0.
- **Required fix**: Initialize `peak = 0.0`, and compute drawdown vs that peak (same for numba).

#### P0.2 Risk computed with `abs(entry-stop)` hides wrong-side stops (present)

- **Present in**:
  - Readable engine: `src/backtest/engine.py` uses `actual_risk = abs(entry_price - stop_px)`.
  - Fast engine: `src/backtest/fast.py` uses `act_risk = abs(ent_price - stop_px)`.
  - Combiner fast: `src/combiner/simulator.py` uses `act_risk = abs(ent_price - stop_px)`.
  - Combiner detailed: `simulate_combiner_legacy_logs` also uses `abs(...)`.
- **Impact**: Wrong-side stops (e.g., long stop above entry) become “valid” risk, and trades can execute that should be rejected.
- **Required fix**: Validate **stop side before abs**:
  - long: `stop < entry`
  - short: `stop > entry`
  - otherwise reject/skip the signal with a clear reason.

#### P0.3 Target validation incomplete (present)

- **Present in**:
  - Readable engine (`engine.py`) validates `fixed_r` requires `target_r > 0`, but **does not validate**:
    - finite entry/stop/target values
    - fixed_price target side (long target > entry, short target < entry)
  - Fast engine (`fast.py`) does **not validate** `target_r > 0` or target side; it only checks `tm in (1,2)` and `act_risk > 0`.
  - Combiner fast/detailed similarly only check `(tm in (1,2))` and `act_risk > 0`, not `target_r` validity nor fixed-price target side.
- **Impact**: Invalid/floating garbage targets can silently trade; fixed-price targets can be behind entry (nonsense).
- **Required fix**:
  - Reject if any required price is non-finite.
  - For `fixed_r`: require `target_r` finite and `> 0`.
  - For `fixed_price`: require `target` finite and correct side vs entry.

#### P0.4 “Config validation incomplete” (present)

- **Observation**:
  - There is no unified validation layer for common config fields.
  - Engines/sweeps rely on scattered checks (some in strategies, some in engine, many not checked at all).
- **Required fix**:
  - Introduce common validation helpers and call them from `engine.py`, `sweep.py`, combiner precompute and run/sweep.

#### P0.5 Combiner cooldown may leak across sessions (partially present / needs explicit semantics)

- **Fast combiner** (`_simulate_combiner_numba`) resets `daily_trades` and `daily_r` on new session (`sid != prev_sess`), **but does not reset `cooldown_until`** on session boundary.
- **Detailed combiner** (`simulate_combiner_legacy_logs`) also does not reset `cooldown_until` at session boundary.
- **Impact**: A loss late in day can impose cooldown into next day because cooldown is tracked in **bar index** units.
- **Required fix**:
  - Reset cooldown at session boundary (default).
  - If a “global cooldown across sessions” is desired, it must be explicit and tested.

#### P0.6 Fast combiner `daily_trade_number` is not real (present)

- **Fast combiner**: `simulate_combiner_numba` emits `daily_trade_number: 0` for every trade.
- **Detailed combiner**: `daily_trade_number` is tracked and written.
- **Impact**: diagnostics are inconsistent; any downstream analysis relying on that field is wrong for the fast path.
- **Required fix**: track per-session entry count in numba and store it per trade.

#### P0.7 `max_open_positions` exists but simulator supports only 1 (present, implicit)

- `CombinerConfig` has `max_open_positions`, but `_simulate_combiner_numba` is single-position (`in_pos` scalar).
- **Impact**: configs can claim multi-position support, but behavior is always 1.
- **Required fix**: hard fail if config requests `max_open_positions != 1` until implemented.

#### P0.8 Opposite-direction conflict reason granularity (partially present / missing)

- Current rejection coding uses `REJ_LOWER_PRIORITY_CONFLICT` for “not selected” and also for “opposite-direction skip-all” path (it increments the same bucket).
- Detailed logs do have a distinct string `opposite_direction_skip` (but fast path does not expose a separate reason).
- **Required fix**: add explicit rejection reason for opposite-direction conflict/skip in fast path and metrics rollups.

---

### P1 — Feature no-lookahead + cache key hardening

#### P1.1 Full-session lookahead columns exist (present)

- `src/features/levels.py` builds and merges:
  - `session_open`, `session_high`, `session_low`, `session_close`
- `session_open` is safe; **`session_high/low/close` are lookahead** intraday.
- **Impact**: any strategy using `session_high/low/close` intraday would leak future info.
- **Current status**: none of the 10 strategies’ `required_features()` explicitly reference these, but the columns exist and are “tempting” footguns.
- **Required fix**: rename / clearly mark as lookahead, and provide safe “so far” equivalents (cummax/cummin, and “close so far” if needed).

#### P1.2 ORB broadcast levels are lookahead unless gated (present)

- `src/features/orb.py` broadcasts ORB levels to the entire session via merge.
- It also provides `after_orb` and strategies (e.g. `orb_continuation`) generally gate with it, but nothing enforces it.
- **Required fix**: add *_known variants (or NaN/False before ORB is complete) so strategies can depend on explicit “known” columns and reduce accidental lookahead.

#### P1.3 Feature-key caching incomplete in sweep + candidate precompute (present)

- `src/backtest/sweep.py:_feat_key` only keys on `(orb_open_minutes, vwap_bands, vol_windows)`.
- `src/combiner/candidate.py:_feat_key` also only keys on `(orb_open_minutes, vwap_bands, vol_windows)`.
- But feature builder supports additional knobs (`price_action_windows`, `volume_windows`, plus strategy-specific feature params like `compression_window`, `opening_hold_minutes`, etc.).
- **Impact**: if future configs vary those windows, caches can be incorrect or silently reuse wrong feature frames/arrays.
- **Required fix**: centralize a FeatureBuildConfig/feature_key that includes all feature knobs used by `build_basic_features`, and use it consistently across engine/sweep/combiner/research.

#### P1.4 Context-key completeness per strategy (risk present)

- Many strategies compute precomputed arrays in `prepare_signal_context` using config-driven windows (e.g. `failed_orb` uses `fail_window_bars` to set `ww`, `vwap_trend_pullback` uses `trend_window` to pick persistence/slope columns).
- Some context_keys already include critical params; others may omit config fields that affect context (especially if `atr_series()` accepts configurable column choice—needs confirmation when `_atr_helpers.py` is reviewed during Phase C).
- **Required action**: explicit audit per strategy: list config fields used in `prepare_signal_context`, ensure `context_key()` includes them.

---

### P2 — Strategy hidden-parameter mismatches / config clarity

Based on inspected implementations + YAMLs:

- **`gap_acceptance_failure`**:
  - Default YAML is `side: long_only`; focused grid is also `long_only`.
  - Implementation `_gap_af_numba` sets `cand_short` but never populates it; it is effectively **long-only**.
  - This should be made explicit via `validate_config()` (reject `side != long_only`) unless short logic is implemented + tested.

- **`prior_day_level_trap`**:
  - Default YAML is `level_type: prior_day_low`; focused grid fixes `prior_day_low`.
  - Implementation only uses `prior_day_low` in required features and context; effectively **prior-day-low long trap**.
  - Make explicit via validation (reject unsupported `level_type`/`side`) unless expanded + tested.

- **`afternoon_continuation`**:
  - `features.midday_window` exists in YAML and `normalized_param_key`, but code uses fixed `rolling_high_60_prior` / `rolling_low_60_prior` and `vwap_persistence_above_60`.
  - This parameter currently looks like **dead uniqueness** unless wired to feature-building windows/columns.

- **Rolling helper semantics**:
  - In features, many “*_prior” columns are explicitly shifted; in strategy fast utils, some rolling helpers are inclusive vs prior-exclusive; naming should be clarified or aliased to avoid confusion.

---

### P3 — Postprocess / diagnostics depth (present as “missing features”)

- Current postprocess dedupes by **config key** (`candidate_ids_json` + combiner settings) — not behavior-level.
- No cost-as-R, expectancy distribution, daily trade number breakdown (fast path doesn’t even emit the number), and no behavior-unique outputs.
- These are enhancements planned after P0/P1/P2 correctness is in place.

---

## Files that will require edits (planned)

### Commit group A — Engine correctness & shared execution validation

- `src/backtest/metrics.py` (max_drawdown baseline)
- `src/backtest/fast.py` (drawdown baseline, stop/target validation in fast execution path)
- `src/backtest/engine.py` (stop/target/finite validation, avoid `abs` before validation)
- `src/backtest/sweep.py` (wire shared validation; later: feature_key refactor)
- `src/combiner/simulator.py` (stop/target validation, cooldown reset, daily_trade_number, rejection reasons)
- `src/combiner/metrics.py` (surface new rejection counts; keep API stable)
- `src/combiner/run.py` (validate `max_open_positions==1`; pass-through rejection reporting)
- **New (likely)**: `src/backtest/execution.py` + optional `src/backtest/constants.py` or `src/backtest/execution_numba.py`
- **Tests (new)**: `tests/test_metrics_drawdown.py`, `tests/test_execution_engine.py`, `tests/test_combiner_execution.py`

### Commit group B — Feature no-lookahead & feature-key hardening

- `src/features/levels.py` (mark/rename lookahead + add intraday-so-far)
- `src/features/orb.py` (add *_known columns gated by `after_orb`)
- `src/features/feature_config.py` (document new columns)
- **New (likely)**: `src/features/feature_key.py` (FeatureBuildConfig + key)
- Update call sites to use feature_key:
  - `src/backtest/engine.py`, `src/backtest/sweep.py`, `src/combiner/candidate.py`, `src/research/check_strategy_fast_parity.py`
- **Tests (new)**: `tests/test_feature_no_lookahead.py`

### Commit group C — Strategy config validation + context-key audit

- `src/strategies/strategy/base.py` (add `validate_config()` hook)
- Each strategy plugin: add `validate_config()` and fix/confirm `context_key()` completeness for params used inside `prepare_signal_context`.
- Possible small YAML cleanup for unsupported params/sides (do not change strategy ideas; only make behavior explicit).
- **Tests (new)**: `tests/test_strategy_context_keys.py`, `tests/test_config_validation.py`

### Commit group D — Combiner/postprocess diagnostics (after correctness)

- `src/combiner/postprocess.py` (behavior-level dedupe, cost-aware leaderboards)
- `src/combiner/behavior.py` (new)
- `src/backtest/metrics.py` and/or `src/combiner/metrics.py` (cost-as-R, R-distribution, daily breakdowns)
- **Tests (new)**: `tests/test_combiner_behavior.py`, `tests/test_cost_as_r_metrics.py`

### Commit group E — Tests/validation/docs consolidation

- Add `pytest` to `requirements.txt` (if not present)
- Add `pytest.ini`, `tests/README.md`
- Run the light test suite + compileall + loader list + small parity smoke (only after correctness changes)

---

## Planned commits (as requested)

- **A**: engine correctness (drawdown baseline, stop/target validation, finite checks, combiner cooldown reset, real daily_trade_number, max_open_positions guard) + core tests
- **B**: feature no-lookahead + centralized feature_key + tests
- **C**: strategy validate_config + context_key audit + config/YAML cleanup (explicitly reject unsupported options) + tests
- **D**: combiner/postprocess behavior-level dedupe + cost-aware diagnostics + tests
- **E**: test suite consolidation + docs updates (`README.md`, `PROGRESS.md`, `CHANGES.md`) + hardening closeout note

---

## Notes / constraints confirmed

- **Data**:
  - QQQ coverage artifacts confirm complete 2020–2026 (617,160 rows; 1,588 sessions; duplicates dropped by `read_bars`: 0).
  - SPY remains incomplete (48 missing months) and should not be used for robustness yet.
- **Artifact policy**: `.gitignore` correctly ignores `data/raw/` and heavy result artifacts while force-including curated summaries and candidate YAML libraries.
- **Layer 2**: current “top unique systems” are **config-unique**, not behavior-unique (by design in postprocess).

