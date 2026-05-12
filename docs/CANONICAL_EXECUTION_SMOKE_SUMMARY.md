# Canonical execution smoke — summary (2026-05-11)

## Hardened

- **`src/execution`**: readable modules; `ExitReason.REJECTED`; `TradeResult` helpers (`is_win`, `total_qty_frac`, `has_partial`); `ExitPlan.max_hold_bars_cap`; fill helpers (`raw_exit_price_for_reason`, `is_time_based_exit`, `is_price_level_exit`); PnL `gross_pnl_per_share` / `net_pnl_per_share_from_gross`; **conservative trailing** (check prior bar’s trail; ratchet after other checks); **exit order** per updated `docs/EXECUTION_SEMANTICS.md`.
- **`src/management`**: scalp plan adds `max_hold_bars_cap`.
- **`src/backtest/engine.py`**: `trade_results_to_frame`; canonical `sig_*` column note.
- **`src/combiner`**: real `selection` / `state` helpers + tests; `simulator.py` docstring clarifies legacy-only extension policy.

## Tests added / expanded

**49** active `pytest` cases (synthetic bars only).
- Execution: exits (`target_first`), fill helpers, path (stop, EOD, short on/off, invalid risk, NFT, max-hold cap), trailing same-bar guard, partial `total_qty_frac`, PnL gross helper.
- **Management**: `test_management_modes.py`.
- **Combiner scaffold**: `test_combiner_selection_state.py`.

## Semantics now covered (synthetic)

- Fixed target, stop, max-hold (+ plan cap), EOD, end-of-data, MFE/MAE.
- Same-bar `stop_first` / `target_first`.
- Partials: touch trigger, close fill, weighted R, qty sum.
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

**`EXPAND_EXECUTION_TEST_MATRIX`**
