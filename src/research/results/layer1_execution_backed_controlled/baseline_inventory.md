# Baseline inventory — Layer1 execution-backed controlled (design)

**Date:** 2026-05-11  
**Git tip before this design work:** `fce5dda` (`Research(execution): harden execution-backed semantics`).

## Handoff / decisions (pre-task)

- **NEXT_HANDOFF** pointed at **`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`** after execution-backed hardening.
- **Execution-backed status:** Layer2 combiner hardened; **Layer1 mainline** already routes accounting through **`run_strategy_backtest` → `simulate_trade_path`** (see `src/backtest/engine.py`). No separate Layer1 Numba PnL.

## Layer1 pipeline entry points

| Area | Path |
|------|------|
| Bars | `src/data/read_bars.py` |
| Features | `src/features/build_features.py` (via `feature_key.build_features_from_config`) |
| Strategies | `src/strategies/loader.py` |
| Signals | `src/backtest/signal_adapter.py` |
| Orchestration | `src/backtest/strategy_runner.py` |
| Sweep CLI | `src/backtest/sweep.py` |
| Metrics | `src/backtest/metrics.py` |

## Data

- **Repo-local only:** `data/raw/ibkr` (equity `bars_1min`, `symbol=QQQ` monthly `data.parquet`).
- **QQQ committed span:** calendar years **2020–2026** present on disk (2026 through last committed month).

## Strategies / tests

- **Registered strategies:** **35** (`available_strategies()`).
- **Controlled design set:** 3 keys only (see `strategy_selection_design.md`).
- **Pytest:** **149** tests collected (same as full suite at design time).

**Design session note:** `src/backtest/sweep.py` now includes **`if __name__ == "__main__"`** so **`python -m src.backtest.sweep`** matches documented runbooks (previously the module loaded without invoking **`main()`**).

## Result root (this task)

`src/research/results/layer1_execution_backed_controlled/` — design-only CSV/MD/runbooks; **no** real sweep outputs committed here.

## Non-goals (explicit)

No broad Layer1/Layer2/Layer3, WFO, live/paper, SPY research sweeps, router, new strategy families, signal semantics changes, selected candidate YAML edits, legacy archive/delete, Numba `fast_path` implementation, second PnL engine, or forbidden heavy artifacts. **No `D:` paths** in committed research text (use repo-relative `data/raw/ibkr`).
