# CHATGPT_REVIEW_BUNDLE — Layer1 execution-backed controlled (design)

## 1. Git / validation

- **Branch:** `main` (at design time aligned with `origin/main`).
- **`python -m compileall -q src`:** OK (design-time).
- **`python -m pytest -q`:** **149** passed.
- **`python -m src.backtest.sweep --help` / `--smoke` / `--validate-pipeline`:** OK (`__main__` guard).
- **Combiner / research `--help`:** OK (see `baseline_validation.csv`).
- **`python -m src.backtest.sweep --dry-run`:** PA + QQQ short window + `--max-combos 1` OK.
- **`validate_research_artifacts`** on this result root: OK (**14** path rows in `layer1_execution_backed_controlled_artifact_validation.csv`).

## 2. Why this design is needed

Controlled Layer1 must become the **new candidate factory** without broad sweeps, duplicate PnL engines, or ambiguous data roots. This package pins **three** strategies, **repo-local QQQ** windows, **grid caps**, **artifact schema**, and **validation gates** before any real run.

## 3. Current execution-backed status

Layer2 combiner **`execution_backed`** is hardened. Layer1 **mainline** already uses **`simulate_trade_path`**; **`fast_path.py`** remains non-canonical until parity.

## 4. Layer1 pipeline state

`read_bars` → `strategy_runner` → **`run_strategy_backtest`** → **`simulate_trade_path`** → **`summarize_trades`**. Only **`src/execution`** owns accounting. Details: `layer1_pipeline_state.md` / `.csv`.

## 5. Data design

**`data/raw/ibkr`** only; QQQ partitions **2020–2026** committed. Preferred run window **2023-01-01..2024-12-31** with **2024 H1** fallback. `data_design.md`.

## 6. Strategy selection

**`pa_buy_sell_close_trend`**, **`gap_acceptance_failure`**, **`cci_extreme_snapback`** only for first controlled run. `strategy_selection_design.md`.

## 7. Grid design

Use **`--max-combos`** (**64** PA/GAP, **32** CCI) against focused YAMLs. `grid_design.md`.

## 8. Candidate schema

Future **`selected_candidates/*.yaml`** + indices + `sweep_results.csv`; no real YAML in this design commit. `candidate_artifact_schema.md`.

## 9. Execution policy

Default intraday policy: **STOP_FIRST**, slippage/commission from YAML, EOD minute; note **`min_risk_per_share`** threading gap in `engine.py` for run task. `execution_policy_design.md`.

## 10. Run commands

`run_commands.md`, `run_commands.ps1`, `run_commands.sh` — preflight + sweep templates (**real sweeps commented** in shell scripts).

## 11. CLI capability / runner gaps

`cli_capability_check.md` + `runner_gap_analysis.md` — no `--engine` on sweep; no built-in YAML selection.

## 12. Validation gates

`validation_gates.md` / `.csv`.

## 13. Decision

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## 14. Explicit non-runs

No real Layer1 sweep in this task, no broad Layer2/Layer3, WFO, live, SPY sweeps, router, new strategies, semantics edits, legacy delete, Numba accounting, heavy artifacts.

## 15. Recommended next step

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
