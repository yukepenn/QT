# P0 correctness cleanup — summary (2026-05-10)

## 1. Purpose

Harden **PA + combiner** foundations before more PA Batch B/C grid work: **formatting**, **session-correct features**, **sweep dedupe keys**, **combiner validation parity**, **structural target documentation**, and **diagnostics** (gates + exits) without Layer 1/2/WFO reruns.

## 2. Formatting outcome

`black` on core research Python + `.gitignore` section comments only. See `format_core_modules_for_maintainability.md`. **No intended behavior change.**

**Git:** `b2dc51f` — `Format core research modules for maintainability`

## 3. `pa_swings` session-boundary fix

Replaced global `shift(1)` in `pa_close_back_inside` with **session-scoped** prior high/low and session-scoped prior `rh`/`rl` for the outside-bars test. **Tests:** `tests/test_pa_swings_session_boundary.py`

## 4. `normalized_param_key` audit / fix

All ten PA strategies now key **entry window**, **ATR buffer**, **max_trades_per_day**, **min_risk_per_share**, and **MTR `wedge_push_min`**, plus tight-channel climax blockers. **Doc:** `pa_normalized_param_key_audit.md`. **Tests:** `tests/test_strategy_normalized_param_keys.py`

**Caution:** older PA Layer 1 sweeps may have under-explored the grid if keys were missing; selective rerun when comparing pre/post rows.

## 5. Combiner detailed validation parity

`simulate_combiner_legacy_logs` now uses `validate_trade_setup` for entry validation (stop side, risk, `target_r`, fixed-price target side, min risk). **Tests:** `tests/test_combiner_detailed_validation_parity.py`

## 6. PA structural target semantics (Option A)

**Option A** chosen: document that structural target **strings** in `long_stop_target` map to **TM_FIXED_R** economics at the signal bar. **Doc:** `pa_structural_target_semantics.md`. **Tests:** `tests/test_pa_structural_targets.py`

## 7. PA gate diagnostics

**Script:** `src/research/pa_gate_diagnostics.py`  
**Outputs:** `src/research/results/pa_batch_bc_gate_diagnostics_v1/`  
**Tests:** `tests/test_pa_gate_diagnostics.py` (import / smoke)

**Finding (tuned v1, 2023–2024):** `pa_broad_channel_zone` is blocked at the **“zone / below upper third”** gate (0 rows pass). `pa_generic_breakout_pullback` → 0 final signals. `pa_second_entry_pullback` very sparse. `pa_buy_sell_close_trend` and `pa_climax_reversal` show non-zero finals.

## 8. PA exit diagnostics

**Script:** `src/research/pa_exit_diagnostics.py` (candidate YAML `config:` + fast backtest metrics + optional 0.02 stress)  
**Outputs:** `src/research/results/pa_batch_bc_exit_diagnostics_v1/`  
**Tests:** `tests/test_pa_exit_diagnostics.py`

**Finding:** `pa_buy_sell_close_trend` strict set is **max-hold heavy**; `pa_climax_reversal` tuned v1 set is **stop/target balanced** on this window (see `pa_batch_bc_exit_diagnostics_v1.md`).

## 9. Validation

- `python -m pytest -q` — **266** passed (at time of summary)
- `python -m compileall -q src` — clean
- `python src/strategies/loader.py --list` — **35** strategies
- Parity smokes: `check_strategy_fast_parity` (failed_orb + listed PA) after changes
- Boundary greps: `LOOKAHEAD` limited to safe columns; no `_feat_key` in `src/**/*.py`
- Tracked heavy artifacts: no `trades.csv` / `top_runs` in new commits

## 10. Explicit non-runs

- No new Layer 1 sweeps, no Layer 2, no mini-WFO, no full WFO, no live/paper, no new strategies, no global shorts, no trailing stops.

## 11. Next recommended step

Design **PA Batch B/C tuned v2** grids from **gate diagnostics** (esp. unstick `pa_broad_channel_zone` zone filter, generic breakout path) and **exit diagnostics** (close-trend hold / target balance), not blind parameter expansion.
