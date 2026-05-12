# Canonical Layer 2 combiner (design)

**Status:** Mainline `src/combiner/simulator.py` is a **legacy compatibility shim** (explicit re-exports from `combiner/legacy/simulator_legacy.py`). It is **not** canonical execution.

## Target pipeline

1. Load candidate configs and optional precomputed signal matrices (`precompute.py`, `signal_cache.py`).
2. **`combiner.selection`** — pick winning candidate per bar when multiple qualify (priority + deterministic tie-break).
3. **`combiner.state`** — enforce max trades/day, cooldown after loss, daily loss cap, session resets.
4. (Future) **`router`** — may narrow allowed candidates or adjust priority / default `management_mode`.
5. Build **`TradeIntent`** from the winning signal row + policy + `ExitPlan` from `management`.
6. Call **`src.execution.path.simulate_trade_path`**.
7. Aggregate **`TradeResult`** legs into trade logs and metrics frames.

## Module roles (no accounting)

| Module | Role |
|--------|------|
| `candidate.py` | Identity, merged YAML config, metadata — **no** PnL. |
| `precompute.py` | Feature/context caches, profiling — **no** fill semantics. |
| `signal_cache.py` | Cache keys, load/save matrices — **no** PnL. |
| `selection.py` | Pure choice logic. |
| `state.py` | Guard counters; consumes realized R from **already computed** trades. |

## What stays legacy until migrated

- `simulate_combiner_numba`, `simulate_combiner_legacy_logs`, and related constants from `simulator_legacy`.
- `combiner/run.py`, `combiner/sweep.py` orchestration that still calls legacy simulators.

## Before Layer 2 research resumes

- Execution-backed path for at least one frozen candidate set on synthetic bars.
- Parity or explicit divergence notes vs legacy Numba for the same intents.

## Execution-backed `simulate_combiner_canonical` (adapter)

`src/combiner/adapter.py` walks bars sequentially, builds **`TradeIntent`**, and calls **`simulate_trade_path`**. Hardening rules (2026-05):

- **Same-session next-bar entry:** `entry_idx = signal_idx + 1` must satisfy `session_date[entry_idx] == session_date[signal_idx]`; otherwise the signal is skipped (no entry on the first bar of a later calendar session).
- **Min risk:** `ExecutionPolicy.min_risk_per_share = max(combiner_cfg.min_risk_per_share, min_risk_per_candidate[ci])`; trades below the floor fail materialization with **`risk_too_small`** (enforced in `materialize_trade_levels`, not ad-hoc PnL in Layer2).
- **`combiner.state.reset_day`:** clears **`cooldown_until_bar`** and **`open_positions`** on a new **`session_date`** so a prior-session loss cooldown cannot block the next session’s opening bars.
