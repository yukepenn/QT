# Canonical execution smoke — summary (2026-05-11)

## Hardened

- **`src/execution`**: readable modules; `materialize_trade_levels` for entry/risk/target; `ExitReason.REJECTED`; `TradeResult` gross/net R (`r_multiple` = net); `ExitPlan.max_hold_bars_cap`; `ExecutionPolicy.scale_fill_policy` (`close` / `trigger_price`); fill helpers; PnL `gross_pnl_per_share` / `net_pnl_per_share_from_gross`; **conservative trailing** (check prior bar’s trail; ratchet after other checks); **exit order** per updated `docs/EXECUTION_SEMANTICS.md`.
- **`src/management`**: scalp plan adds `max_hold_bars_cap`.
- **`src/backtest/engine.py`**: raw `sig_*` → `TradeIntent` only (no adapter fill/risk/target); `trade_results_to_frame`; canonical column note.
- **`src/backtest/metrics.py`**: aggregates `r_multiple` / `net_pnl` / optional `total_gross_r` without recomputing trade R from OHLC.
- **`src/combiner`**: real `selection` / `state` helpers + tests; `simulator.py` docstring clarifies legacy-only extension policy.

## Tests added / expanded

**68** active `pytest` cases (synthetic bars only).
- Execution: exits (`target_first`), fill helpers, path (stop, EOD, short on/off, invalid risk, NFT, max-hold cap), trailing same-bar guard, partial `total_qty_frac`, PnL gross helper.
- **Management**: `test_management_modes.py`.
- **Combiner scaffold**: `test_combiner_selection_state.py`.

## Semantics now covered (synthetic)

- Fixed target, stop, max-hold (+ plan cap), EOD, end-of-data, MFE/MAE.
- Same-bar `stop_first` / `target_first`.
- Partials: touch trigger, **`scale_fill_policy`** (`close` vs `trigger_price`), weighted R, qty sum.
- Trailing: prior-level check, no optimistic same-bar ratchet trigger.
- NFT after N bars when unrealized R below threshold.
- Shorts gated by `allow_short`.

## Adapter / scaffold status

| Area | Status |
|------|--------|
| Backtest `run_strategy_backtest` | Minimal MVP; uses execution for accounting |
| Combiner `simulator` | Still **legacy Numba** re-export |
| Router / portfolio | Unchanged scaffolds |

## Legacy

- `src/backtest/legacy/*`, `src/combiner/legacy/*` retain duplicate accounting until migration.

## Next recommended step

**`HOLD_AND_REVIEW`**
