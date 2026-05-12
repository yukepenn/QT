# Strategy selection — controlled Layer1

**Scope:** Exactly **three** strategies for the first controlled execution-backed Layer1 rebuild. Optional later families are listed for roadmap only — **not** in first run.

## 1. `pa_buy_sell_close_trend`

- **Loader key:** `pa_buy_sell_close_trend`
- **Implementation:** `src/strategies/strategy/pa_buy_sell_close_trend.py`
- **Loader:** Registered (part of 35-strategy registry).
- **Feature groups:** PA regime / range windows, VWAP, ATR-like, bull trend columns (see `required_features()` — includes `session_date`, `minute_from_open`, OHLC, `vwap`, `close_near_high`, etc.).
- **Signal contract:** Standard `sig_*` after `prepare_canonical_signals` (`standard_sig_v1`).
- **Testing YAMLs:** `src/strategies/testing_parameters/pa_buy_sell_close_trend_focused.yaml` (and tuned v1–v3 variants).
- **Archived candidates:** May exist under `src/research/results/Archive/**` — **read-only** reference; new Layer1 output must not depend on Archive as active source.
- **Trade style:** Long-only intraday continuation after strong bull bar / trend context.
- **Reason included:** Core PA family; well covered in tests and pipeline validation.
- **Risk:** Large default **focused** grid (hundreds of combos) — **must** cap with `--max-combos` or reduced grid file.
- **Estimated grid size (focused YAML):** **432** combinations (2×2×2×2×3×3×3).
- **First controlled run:** **true** (with strict combo cap).

## 2. `gap_acceptance_failure`

- **Loader key:** `gap_acceptance_failure`
- **Implementation:** `src/strategies/strategy/gap_acceptance_failure.py`
- **Loader:** Registered.
- **Features:** Opening hold, gap norm, session/prior close, VWAP, etc. (`required_features()` includes `session_open`, `prior_day_close`, `gap_prior_range_norm`, …).
- **Testing YAMLs:** `gap_acceptance_failure_focused.yaml`, `gap_acceptance_failure_refined_v1.yaml`.
- **Trade style:** Long gap-failure / reclaim setups in first hour context.
- **Risk:** Moderately large focused grid; confirm `read_bars` includes opening bars needed for gap logic.
- **Estimated grid size (focused):** **192** combinations.
- **First controlled run:** **true** (with cap).

## 3. `cci_extreme_snapback`

- **Loader key:** `cci_extreme_snapback`
- **Implementation:** `src/strategies/strategy/cci_extreme_snapback.py`
- **Loader:** Registered.
- **Features:** CCI windows 14/20 (and config-driven `cci_*` columns), swing high, ATR-like.
- **Testing YAMLs:** `cci_extreme_snapback_focused.yaml`.
- **Trade style:** Long CCI oversold / snapback.
- **Risk:** Smaller grid; watch feature column alignment when `cci_window` changes (strategy loads multiple cci columns).
- **Estimated grid size (focused):** **32** combinations.
- **First controlled run:** **true** (can run full grid or cap for parity with other legs).

## Optional later (design only — do not run in first controlled Layer1)

| Strategy | Notes |
|----------|--------|
| `vwap_reclaim_reject` | `vwap_reclaim_reject_focused.yaml` exists |
| `vwap_trend_pullback` | `vwap_trend_pullback_focused.yaml` |
| `failed_orb` | `failed_orb_focused.yaml` / refined |
| `orb_continuation` | `orb_continuation_focused.yaml` |

## Excluded from this design package

- The other **32** registered strategies — not part of **controlled** Layer1 v1.
