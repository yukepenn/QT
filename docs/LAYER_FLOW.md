# Layer flow (Layer 1 / 2 / 3) — architecture reset

**Date:** 2026-05-11

This document ties **research layers** to **module ownership** after the execution reset. Machine-readable rows: `docs/LAYER_FLOW.csv`.

## Layer 1 — Candidate factory

**Purpose:** Per-strategy parameter exploration and candidate library construction.

**Pipeline (mainline target):**

1. Load validated bars (`src/data`).
2. Build no-lookahead features (`src/features`).
3. Load strategy; generate raw signals aligned to the standard signal contract (`src/strategies`, `docs/SIGNAL_CONTRACT.md`).
4. **`run_strategy_backtest`** (`src/backtest/engine.py`) maps rows → `TradeIntent` → **`simulate_trade_path`** (`src/execution/path.py`).
5. Aggregate metrics (`src/backtest/metrics.py`); emit configs / YAML / metadata for Layer 2.

**Current status:** Layer 1 is the **mainline** path: `read_bars` → `strategy_runner` → `run_strategy_backtest` → `simulate_trade_path` → `metrics`. Parameter sweep and CLI live in **`src/backtest/sweep.py`** (synthetic `--smoke`, real-symbol sweep, `--validate-pipeline`). Historical Numba sweep code is under **`archive/legacy_backtest/`** (not a mainline import).

**Future acceleration:** Numba only under `src.execution.fast_path` **after** parity tests vs `simulate_trade_path` — never a second PnL definition in `backtest.fast`.

**Must not:** Own fill/PnL semantics outside `src/execution`.

## Layer 2 — Combiner / candidate competition

**Purpose:** When multiple candidates can fire, choose one under guards (priority, cooldown, daily loss, max trades).

**Pipeline (mainline target):**

1. Load candidate configs / precomputed signal matrices (`precompute`, `signal_cache`) — **cache only**, no accounting.
2. `combiner.selection` — deterministic arbitration.
3. `combiner.state` — day/session guards.
4. (Future) router adjusts allowed / priority / `management_mode`.
5. Build `TradeIntent` → **`simulate_trade_path`** → aggregate `TradeResult`.

**Current status:** Mainline Layer 2 accounting is **not implemented** yet. `src/combiner/simulator.py` exposes rejection/exit code constants and raises **`NotImplementedError`** for `simulate_combiner_numba` / `simulate_combiner_legacy_logs`. The historical Numba implementation is archived as **`archive/legacy_combiner/reference_simulator.py`**.

**Must not:** Implement independent intrabar fill/exit/PnL.

## Layer 3 — Fixed profile / OOW / WFO validation

**Purpose:** Evaluate **frozen** systems across calendar windows (smoke, OOW, full WFO when enabled).

**Pipeline (mainline target):**

1. Load frozen Layer 2 + policy + semantics version stamps.
2. Walkforward harness (`src/walkforward`) orchestrates runs; each trade path should go through **`simulate_trade_path`** once the Layer 2 adapter exists.

**Current status:** Harnesses (`runner.py`, `fixed_system.py`, `folds.py`) still call **`src.combiner.run`**, which depends on the combiner simulator. Until Layer 2 is reimplemented, those entry points are **blocked** by the simulator stub. Layer 3 is pending Layer 2 migration.

**Must not:** Tune parameters inside fixed OOW checks; must not own trade accounting.

## research/

Thin runners and curated aggregates only; no canonical accounting.

## portfolio/

Sizing, daily risk, equity curve — **after** per-trade results from execution; does not redefine fill/PnL.
