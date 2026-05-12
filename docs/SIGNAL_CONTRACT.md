# Strategy signal contract (canonical)

Strategies may keep internal column names during transition. Downstream adapters map into this canonical schema.

## Canonical `sig_*` DataFrame (Layer 1 / backtest adapter)

The **reference backtest adapter** (`run_strategy_backtest`) validates the columns in `STANDARD_SIGNAL_COLUMNS` from `src/strategies/strategy/base.py` (including `sig_valid`, `sig_side`, `sig_stop`, `sig_target_mode`, `sig_target`, `sig_target_r`, `sig_risk_per_share`, `sig_entry_ref`, `sig_reason`, `sig_strategy`).

Optional columns consumed by execution when present include `sig_max_hold_bars`, `sig_candidate_id`, `sig_management_mode`.

**Light adapter:** `src/backtest/signal_adapter.py`

- `infer_signal_mapping(strategy_name)` — reads optional `output_contract` from metadata (`old_col` → `sig_*`).
- `canonicalize_signal_frame(df, mapping)` — renames only; does not invent prices.
- `validate_canonical_signal_frame` / `assert_canonical_signal_frame` — standard column presence plus sanity on rows where `sig_valid` is true (`sig_target_mode` in `fixed_r` / `fixed_price` / `none`, non-zero `sig_side`, finite `sig_stop`).

## Conceptual columns (documentation / combiner context)

Some docs and routers refer to denormalized names:

| Column | Type | Notes |
|--------|------|--------|
| `signal_valid` | bool | Mapped from `sig_valid` or strategy-specific flag |
| `side` | int8 | `+1` long, `-1` short |
| `stop_price` | float | From `sig_stop` |
| `target_price` | float | Preview or recomputed at entry for `fixed_r` |
| `target_r` | float | R multiple for `fixed_r` targets |
| `target_mode` | str | `fixed_r` \| `fixed_price` |
| `risk_per_share` | float | Positive distance entry→stop |
| `max_hold_bars` | int | Bars from entry bar; optional |
| `reason` | str | Human-readable |
| `candidate_id` | str | Stable id for combiner |
| `strategy` | str | Strategy id |
| `family` | str | From metadata |
| `setup_type` | str | Taxonomy bucket |
| `management_mode` | str | e.g. `fixed_r`, `scalp`, `swing` |

## Adapter policy

- `backtest` / `combiner` adapters read `sig_*` columns and populate `TradeIntent` + `ExecutionPolicy`.
- `src/backtest/engine.py` documents expected `sig_*` names; use `trade_results_to_frame` to inspect raw `TradeResult` rows.
- Full strategy refactors are **out of scope** for phase 0–3; metadata must load for every registered strategy where possible.

## Metadata

See `src/strategies/metadata.yaml` + `metadata.py` for `family`, `setup_type`, `playbook`, `allowed_sides`, `default_management_mode`, `required_features`, and optional `output_contract` mapping hints.
