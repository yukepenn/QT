# Canonical execution smoke — plan

## Goal

Prove the **reference** engine in `src/execution/path.py` matches documented
semantics (fills, exit order, trailing conservatism, partials, NFT, shorts)
**before** any Champion migration or Layer2 production work.

## Scope

- Synthetic bars only (tests + `scripts/canonical_execution_smoke.py`).
- No parquet, no sweeps, no combiner Numba migration in this phase.

## Checklist

1. Types / policy aligned with `docs/EXECUTION_SEMANTICS.md`.
2. Fill + PnL helpers covered by unit tests.
3. Exit detection helpers + `simulate_trade_path` integration tests.
4. Management `ExitPlan` templates smoke-tested.
5. Backtest adapter maps signals → `TradeIntent` → execution (existing test).
6. Combiner `selection` / `state` deterministic helpers tested.
7. Accounting grep inventory identifies remaining legacy duplicates.

## Exit criteria

- `python -m pytest -q` green on active `tests/`.
- `python scripts/canonical_execution_smoke.py` prints three scenarios without error.
- `docs/CANONICAL_EXECUTION_SMOKE_SUMMARY.md` updated for handoff.
