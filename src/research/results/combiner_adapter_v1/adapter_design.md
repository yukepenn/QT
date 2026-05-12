# Combiner adapter design (v1)

## Boundary

1. **Precompute** builds bar arrays + per-candidate signal matrices (side, valid, stop, target preview, mode codes, risk preview). No PnL.
2. **Selection** (`selection.py`) picks one candidate among competitors on a bar (priority + deterministic tie-break).
3. **State** (`state.py`) tracks day resets, cooldown bar index, trades/day, realized R for daily loss budget.
4. **Adapter** (`adapter.py`) walks bars sequentially (max one overlapping trade), builds `TradeIntent`, calls `simulate_trade_path`, maps `TradeResult` to combiner trade rows.
5. **Execution** owns fill, stop/target resolution, R math, same-bar policy.

## Input contract (per selected signal)

- `candidate_id`, `strategy`, `family`, `setup_type` (from `Candidate` + metadata)
- `side`, `signal_idx`, `entry_idx` (next-bar entry: `entry_idx = signal_idx + 1`)
- `stop_price`, `target_price` / `target_r`, `target_mode`, `risk_per_share` optional
- `max_hold_bars`, `qty`, `management_mode` default `none`
- Bar context: full `DataFrame` passed to `simulate_trade_path`

## Layer2 must not

- Implement independent intrabar fills, trailing, or R definitions.
- Hardcode router regimes.

## Legacy compatibility

- `simulate_combiner_legacy_numba` / `simulate_combiner_legacy_logs` load `archive/legacy_combiner/reference_simulator.py` (registered in `sys.modules` for dataclass resolution).
- `simulate_combiner_numba` remains an alias to legacy for existing imports.

## Version stamps

- `execution_semantics_version` from `ExecutionPolicy`
- `combiner_adapter_version` = `combiner_adapter_v1` (module constant in `trade_intent_adapter.py`)
- `result_lineage` = `mainline_layer2` on canonical trade rows
