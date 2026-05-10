# PA Brooks primitives — post-addition cleanup summary — 2026-05-10

## 1. Purpose

After commit **`ac7b7e4`** (Brooks PA feature primitives), this phase performs **engineering cleanup**: clearer helper **namespace**, **side-specific** naming for failed-breakout ages, **registry / feature_key** tests, and documentation — **without** research reruns or signal changes.

## 2. Why this is cleanup, not research

- **No** Layer 1 / Layer 2 / mini-WFO / full WFO / live runs.
- **No** changes to PA strategy entry/stop/target rules; economics and selected YAMLs remain valid.

## 3. Helper namespace decision

- **Problem:** Generic PA helpers lived beside 35 strategy plugins under `src/strategies/strategy/`, encouraging further accumulation.
- **Decision:** Introduce **`src/strategies/common/pa.py`** for shared PA logic; keep **`strategy/pa_batch_a_utils.py`** and **`strategy/pa_common.py`** as **compatibility shims**.

## 4. New `src/strategies/common/pa.py`

- Hosts: `pa_range_window`, `pa_regime_window`, `atr_col_name`, `pa_context_windows`, `pa_family_from_strategy_name`, `build_pa_reason`, `safe_bool_array`, `safe_float_array`, `long_stop_target`, `finalize_long_signals_df`, `signals_df_from_arrays`.

## 5. Compatibility shims

- `pa_batch_a_utils.py` / `pa_common.py` re-export from `common.pa` with deprecation notes in module docstrings.

## 6. Side-specific PA primitive fix

- **`pa_failed_breakout_age_{N}`** historically counted bars since **`pa_failed_breakout_down_{N}`** only.
- **Added:** `pa_failed_breakout_down_age_{N}`, `pa_failed_breakout_up_age_{N}` (bars since last down/up failed breakout flag in session).
- **Preserved:** `pa_failed_breakout_age_{N}` as a **copy of down-age** for backward compatibility.

## 7. Feature registry / `feature_key` audit

- See **`pa_brooks_feature_registry_audit.md`**.
- Tests: **`tests/test_pa_brooks_feature_registry.py`**.

## 8. Numba / fast-path audit

- See **`pa_brooks_numba_fastpath_audit.md`**. No backtest engine edits.

## 9. Tests

- `tests/test_strategy_helper_namespace.py` — `common.pa` import, shims, loader count, helpers not registered.
- `tests/test_pa_swing_side_specific_primitives.py` — side ages + legacy alias + trapped asymmetry.
- `tests/test_pa_brooks_feature_registry.py` — column presence + `feature_key` sensitivity.
- `tests/test_pa_swing_primitives.py` — extended column list.

## 10. Validation

- Full **`pytest`** green (353 tests at last run).
- **`compileall`** OK; loader **35** strategies; fast parity spot checks recommended post-push (failed_orb + PA YAMLs).

## 11. Explicit non-runs

- No Layer 1, Layer 2, mini-WFO, full WFO, live/paper.

## 12. Next recommendation

1. Execute **PA Batch B/C reduced Layer 2** using **tuned v2** `selected_candidates`.
2. **Defer tuned v3** Brooks primitive grids until Layer 2 diagnostics show where PA gates fail.
3. **Defer mini-WFO** until reduced Layer 2 passes behavior + **0.02** cost-stress gates.
