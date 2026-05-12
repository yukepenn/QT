# Layer flow (Layer 1 / 2 / 3) — architecture reset

**Date:** 2026-05-11

This document ties **research layers** to **module ownership** after the execution reset. Machine-readable rows: `docs/LAYER_FLOW.csv`.

## Layer 1 — Candidate factory

**Purpose:** Per-strategy parameter exploration and candidate library construction.

**Pipeline (canonical target):**

1. Load validated bars (`src/data`).
2. Build no-lookahead features (`src/features`).
3. Load strategy; generate raw signals aligned to the standard signal contract (`src/strategies`, `docs/SIGNAL_CONTRACT.md`).
4. **`run_strategy_backtest`** (`src/backtest/engine.py`) maps rows → `TradeIntent` → **`simulate_trade_path`** (`src/execution/path.py`).
5. Aggregate metrics (`src/backtest/metrics.py`); emit configs / YAML / metadata for Layer 2.

**Current status:** Reference single-strategy path exists. **Grid sweep** on the reference engine supports **synthetic smoke** and a **real-symbol MVP** (`run_real_symbol_sweep`, `src/backtest/strategy_runner.py`, CLI `--validate-pipeline` / `--dry-run`). Default CLI (no args) prints help and exits non-zero. Historical Numba sweep code is under **`archive/legacy_backtest/`** (not a mainline import).

**Future acceleration:** Numba only under `src.execution.fast_path` **after** parity tests vs `simulate_trade_path` — never a second PnL definition in `backtest.fast`.

**Must not:** Own fill/PnL semantics outside `src/execution`.

## Layer 2 — Combiner / candidate competition

**Purpose:** When multiple candidates can fire, choose one under guards (priority, cooldown, daily loss, max trades).

**Pipeline (canonical target):**

1. Load candidate configs / precomputed signal matrices (`precompute`, `signal_cache`) — **cache only**, no accounting.
2. `combiner.selection` — deterministic arbitration.
3. `combiner.state` — day/session guards.
4. (Future) router adjusts allowed / priority / `management_mode`.
5. Build `TradeIntent` → **`simulate_trade_path`** → aggregate `TradeResult`.

**Current status:** `src/combiner/simulator.py` re-exports **legacy Numba** `simulate_combiner_numba` explicitly from `combiner/legacy/simulator_legacy.py`. **Not** canonical execution.

**Must not:** Implement independent intrabar fill/exit/PnL.

## Layer 3 — Fixed profile / OOW / WFO validation

**Purpose:** Evaluate **frozen** systems across calendar windows (smoke, OOW, full WFO when enabled).

**Pipeline (canonical target):**

1. Load frozen Layer 2 + policy + semantics version stamps.
2. Walkforward harness (`src/walkforward`) orchestrates runs; each trade path goes through **canonical execution** once Layer 2 adapter exists.

**Current status:** Harnesses (`runner.py`, `fixed_system.py`, `folds.py`) call **`src.combiner.run`** and therefore **legacy** accounting today. Layer 3 is **not** canonical vs the new execution package until combiner/backtest adapters are fully wired.

**Must not:** Tune parameters inside fixed OOW checks; must not own trade accounting.

## research/

Thin runners and curated aggregates only; no canonical accounting.

## portfolio/

Sizing, daily risk, equity curve — **after** per-trade results from execution; does not redefine fill/PnL.
