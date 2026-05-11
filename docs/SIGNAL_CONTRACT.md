# Strategy signal contract (canonical)

Strategies may keep internal column names during transition. Downstream adapters map into this canonical schema.

## Canonical columns

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

- `backtest` / `combiner` adapters read legacy `sig_*` columns and populate `TradeIntent` + `ExecutionPolicy`.
- Full strategy refactors are **out of scope** for phase 0–3; metadata must load for every registered strategy where possible.

## Metadata

See `src/strategies/metadata.yaml` + `metadata.py` for `family`, `setup_type`, `playbook`, `allowed_sides`, `default_management_mode`, `required_features`, and optional `output_contract` mapping hints.
