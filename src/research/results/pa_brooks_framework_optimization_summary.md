# Brooks PA framework optimization — phase summary (2026-05-10)

## 1. Purpose

Add a **Brooks-compatible PA optimization layer**: reusable **feature primitives**, coarse **regime / Always-In / trade-mode** columns, **magnet** proximity helpers, a small **`pa_common`** module, **tests**, and **curated docs** — without new strategy plugins or research sweeps.

## 2. Current state before this phase

- PA **`context_key`** optimization shipped; PA Batch B/C **tuned v2 Layer 1** complete; **reduced Layer 2** for Batch B/C **not** run (design doc only).

## 3. Files changed (high level)

- `src/features/price_action.py`, `pa_swings.py`, `regime.py`, `levels.py`, `build_features.py`, `feature_config.py`, `feature_key.py` (via `PaFeatureConfig` / build wiring), **`pa_brooks_enums.py`**, **`pa_magnet_columns.py`**
- `src/strategies/strategy/pa_common.py` (**new**)
- Tests: `tests/test_pa_bar_primitives.py`, `test_pa_swing_primitives.py`, `test_pa_regime_router_features.py`, `test_pa_level_magnet_features.py`, `test_pa_common.py`, `test_pa_required_features_no_lookahead.py`
- Research artifacts: `pa_brooks_framework_optimization_plan.md`, `pa_brooks_feature_primitives_summary.md`, `pa_brooks_strategy_compatibility_audit.md`, `pa_brooks_feature_smoke.{md,csv}`, `pa_brooks_framework_parity_smoke.{md,csv}`, this summary

## 4. Feature primitives added

See **`pa_brooks_feature_primitives_summary.md`** for the authoritative column list.

## 5. PA common helper

- **`pa_context_windows(config)`** → `(pa_range_window, pa_regime_window, atr_column)`
- **`pa_family_from_strategy_name`**, **`build_pa_reason`**, **`safe_bool_array`**, **`safe_float_array`**
- **Not** wired into all strategies in this phase (avoids accidental reason / hash drift).

## 6. No-lookahead proof

- Implementation uses prior / same-bar-safe patterns consistent with existing `src/features` conventions; tests cover session boundaries, finiteness, and **no `LOOKAHEAD` in PA `required_features`**.
- Full feature frames may still contain diagnostic **`full_session_*_LOOKAHEAD`** columns from `levels.py` (3 names); strategies do not require them.

## 7. Strategy compatibility audit

See **`pa_brooks_strategy_compatibility_audit.md`** (core vs diagnostic vs deferred; **`pa_failed_range_breakout_trap`** `require_tr_regime` / `tr_regime_max` naming note — **doc only**, no behavior change).

## 8. Default-preserving refactors

- **None** applied to PA strategy signal paths in this phase (Phase 6 optional dedupe deferred to avoid any reason-string / fingerprint drift).

## 9. Tests

- Full `pytest` green after additions (**337** tests at last full run on this branch).
- New PA primitive / common / required-feature tests listed in §3.

## 10. Feature smoke

- **`pa_brooks_feature_smoke.md`** + **`.csv`** — three configs, Jan 2025 QQQ slice, column counts.

## 11. Parity smoke

- **`pa_brooks_framework_parity_smoke.md`** + **`.csv`** — `failed_orb` + five PA strategies, **`total_mismatch_approx = 0`**, exit 0.

## 12. Explicit non-runs

- No Layer 1, Layer 2, mini-WFO, full WFO, live/paper, no new strategies, no deletion of curated YAMLs/CSVs.

## 13. Next recommendation

1. Run **PA Batch B/C reduced Layer 2** using **tuned v2** `selected_candidates` first (combiner + cost stress + behavior dedupe gates).
2. **Do not** run mini-WFO until that Layer 2 slice passes internal economics / robustness bars.
3. Consider **tuned v3** PA YAMLs that **opt in** to new primitives **only if** Layer 2 evidence says PA grammar needs refinement.
