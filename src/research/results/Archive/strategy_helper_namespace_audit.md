# Strategy helper namespace audit (`src/strategies/strategy/`) — 2026-05-10

## 1. Current flat folder status

`src/strategies/strategy/` is a **single flat directory** of **~51 `.py` files**: one `BaseStrategy` implementation per registered plugin, plus a few **shared helper modules** co-located with plugins for historical convenience.

## 2. True strategy plugins

Each concrete `BaseStrategy` subclass registered in `loader._STRATEGY_BY_NAME` (35 entries), including all `pa_*` names such as `pa_buy_sell_close_trend`, `pa_failed_range_breakout_trap`, etc.

## 3. Helper / interface modules (non-plugins)

| Module | Role |
|--------|------|
| `base.py` | `BaseStrategy`, validation hooks, shared signal column init. |
| `fast_utils.py` | Numba-friendly session thinning, min-risk filters, shared fast-path utilities. |
| `_atr_helpers.py` | ATR column resolution for strategies. |
| `pa_batch_a_utils.py` | **Shim (post-cleanup):** re-exports PA long finalize / stop-target helpers from `src.strategies.common.pa`. |
| `pa_common.py` | **Shim (post-cleanup):** re-exports PA config / reason helpers from `src.strategies.common.pa`. |

## 4. Helpers that should eventually live outside the plugin folder

- **PA-specific but not plugin-specific:** `pa_context_windows`, `pa_range_window`, `long_stop_target`, `finalize_long_signals_df`, `signals_df_from_arrays`, etc. — now implemented under **`src/strategies/common/pa.py`**.
- **`fast_utils.py` / `_atr_helpers.py`:** generic cross-strategy utilities; **documented for a later move** (not moved in this phase to avoid churn).

## 5. Helpers that remain for compatibility

- `src/strategies/strategy/pa_batch_a_utils.py` and `src/strategies/strategy/pa_common.py` stay as **import-compatible shims** so existing `from src.strategies.strategy.pa_batch_a_utils import …` lines keep working.

## 6. Loader policy

- **`loader.py`** only imports concrete strategy classes; **helper modules are never keys** in `_STRATEGY_BY_NAME`.

## 7. Recommended policy (target)

1. **Strategy plugins** stay in `src/strategies/strategy/`.
2. **`base.py`** may remain next to plugins for now (tight coupling to signal schema).
3. **New shared helpers** that are not `BaseStrategy` subclasses go under **`src/strategies/common/`** (e.g. `common/pa.py`).
4. **Shims** in `strategy/` re-export until a deliberate migration pass updates imports and proves parity.
5. **Never** register helper modules as strategy names.
