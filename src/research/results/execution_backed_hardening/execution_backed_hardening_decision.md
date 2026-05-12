# Decision — execution-backed hardening

## Label (exactly one)

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Rationale

- **P0 hardening complete:** same-session next-bar entry guard, cooldown + open-position reset on new session, **`min_risk_per_share`** enforced in **`materialize_trade_levels`**, scale-out fractions fixed to **remaining** qty, with **149** focused `pytest` cases including **`test_execution_backed_hardening.py`**.
- **No second PnL engine:** all changes route through existing **`simulate_trade_path`** / **`materialize`** / **`ExecutionPolicy`** — Layer2 does not add parallel risk math.
- **Tiny real smoke OK:** Jan 2024 QQQ dual-candidate **`execution_backed`** smoke re-run post-hardening (aggregate only) under `smoke/` — trade count **23** unchanged vs prior overlay baseline row for the same window (sanity).
- **Docs/handoff synced** for the next human/LLM prompt (see `docs_sync_summary.*`).
- **Broad rebuild not executed:** controlled Layer1 rebuild still needs an explicit **design** pass (PA/GAP/CCI scope, folds, non-goals) before **`RUN_*`**.

## Recommended next step (exactly one)

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Explicit non-runs

No WFO/mini-WFO, live/paper, SPY sweeps, broad Layer1/Layer2, Global Layer1 rerun, router, production exit-management, short/scalp strategies, Champion YAML edits, legacy archive/delete, new Numba accounting engine, raw trade commits.
