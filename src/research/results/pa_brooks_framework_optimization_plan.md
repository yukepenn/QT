# Brooks PA framework optimization — plan (2026-05-10)

## 1. Current state

- **PA `context_key` cache optimization** is complete on `main`: all ten `pa_*` strategies key context caches only on `prepare_signal_context` outputs (window / ATR column selectors). See `pa_context_key_cache_optimization_summary.md`.
- **PA Batch B/C tuned v2 Layer 1** (QQQ 2023–2024) is complete and curated under `layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/` with decision **`PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_DESIGN`** (design-only combiner doc).
- **Reduced PA Batch B/C Layer 2** has **not** been executed; mini-WFO remains blocked until Layer 2 economics pass internal gates.

## 2. Why this phase exists

- Improve the **shared PA grammar**: reusable bar and swing primitives, coarse **regime / Always-In / trade-mode** router columns, and **magnet / proximity** helpers built on existing safe columns.
- Add **`pa_common`** helpers for consistent config parsing and future gating — **without** a centralized gate that changes live signals today.
- **Not** adding new strategy plugins or renaming the ten PA shells; research continues on the same strategy names and loader registration.

## 3. No-lookahead requirements

- **No centered rolling pivots** and no swing confirmation that requires future bars.
- Primitives use **current and prior bars**, session-scoped groupbys, and existing same-bar-safe or shift-1 rolling patterns aligned with the rest of `src/features/`.
- Strategies must **not** list `*_LOOKAHEAD` in `required_features`; diagnostics-only `full_session_*_LOOKAHEAD` may exist on the feature frame but stay out of strategy contracts.
- **Delayed-confirmed** pivots (if ever added) are explicitly **backlog** — not in this phase.

## 4. Feature primitives to add

| Layer | Module | Role |
|-------|--------|------|
| Bar quality | `price_action.py` | Strong/weak bull/bear closes, signal / failed signal bars, bull/bear micro-channels (3–5), ATR-free thresholds. |
| Swing / structure | `pa_swings.py` | Pullback counts, two-leg pullback flags, second-entry proxies, failed-breakout age, breakout attempt counts, trapped bulls/bears scores (per `swing_windows`). |
| Regime router | `regime.py` + `pa_brooks_enums.py` | Integer enums; `pa_always_in_side_*`, `pa_regime_label_*`, `pa_trade_mode_*`, late-trend / TR-transition / limit-vs-market scores. |
| Magnets | `levels.py` + `pa_magnet_columns.py` | ORB known, VWAP band proximity in ATR units, `pa_mm_range_*` and `near_pa_mm_range_*` from prior-safe range columns. |

## 5. PA common helper scope

- **`src/strategies/strategy/pa_common.py`**: `pa_context_windows`, `pa_family_from_strategy_name`, `build_pa_reason`, `safe_bool_array`, `safe_float_array`.
- **Adoption**: tests + future strategies; **no** forced rewrite of all PA plugins in this phase (default-preserving).

## 6. Strategy behavior policy

- **Default-preserving**: existing signal conditions, stops, targets, and reason strings used in tests / behavior hashes are unchanged unless a proven correctness bug with tests exists (none identified in this phase).
- New columns are **optional** at the feature layer; strategies do **not** add them to `required_features` until a future tuned grid explicitly consumes them.

## 7. Tests

- `tests/test_pa_bar_primitives.py`
- `tests/test_pa_swing_primitives.py`
- `tests/test_pa_regime_router_features.py`
- `tests/test_pa_level_magnet_features.py`
- `tests/test_pa_common.py`
- `tests/test_pa_required_features_no_lookahead.py`

## 8. Explicit non-runs

- No Layer 1 sweeps, no Layer 2 combiner runs, no mini-WFO, no full WFO, no live/paper.
- No new `pa_*` strategy plugins; no deletion of `selected_candidates/*.yaml` or curated summaries.

## 9. Next step after this phase (unchanged)

Execute **PA Batch B/C reduced Layer 2** with tuned v2 selected candidates first; defer mini-WFO until reduced Layer 2 passes behavior + 0.02 cost stress.
