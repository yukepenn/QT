# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push: `git log -1 --oneline` must match `git ls-remote origin refs/heads/main`. |
| Working tree | Stage **curated paths only** — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **163** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --help` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.run_layer1_execution_backed_controlled --help` | OK |
| `python -m src.research.run_layer1_execution_backed_controlled validate-candidates --candidate-root src/strategies/testing_parameters_results/l1_execution_backed_controlled --allow-empty` | OK |
| `python -m src.research.validate_research_artifacts --root src/research/results/layer1_config_candidate_contract_alignment --csv-only` | OK → **8** paths in **`artifact_validation.csv`** |
| `python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only` | OK → **14** paths in **`layer1_execution_backed_controlled_artifact_validation.csv`** |

Optional PA dry-run (short window, no save) was exercised during contract alignment; **no** full controlled PA/GAP/CCI sweeps in this task.

## C. Task scope

**Completed:** **`FIX_LAYER1_CONFIG_AND_CANDIDATE_CONTRACT_BEFORE_RUN`** — align **`fixed:` + `grid:`** merge with runtime and validation, thread **`risk.min_risk_per_share`** into **`ExecutionPolicy`** for Layer1 backtests, **`max_trades_per_day`** / related aliases → **`max_trades_per_session`**, combiner-aligned candidate YAML contract + thin **`run_layer1_execution_backed_controlled`** promote/validate CLI (temp-dir tests), active candidate root **README** only, curated audit under **`src/research/results/layer1_config_candidate_contract_alignment/`**, design-root doc updates.

**Explicit non-runs:** no real controlled Layer1 sweep, no broad Layer1, Layer2/3, WFO, live/paper, SPY research sweeps, router, production exit-management, new strategy families, signal semantic edits, champion/base YAML edits except contract-driven engine/sweep, no real promoted candidate YAMLs, no Archive moves, no legacy delete, no Numba accounting path, no heavy artifact commits.

## D. Config/grid contract

- **`normalize_override_mapping`**: nested dicts → flat dotted keys; lists/scalars are leaves; overlap detection for **`fixed`** vs **`grid`** keys.
- **`grid_combos_from_document`**: each combo = **fixed ∪ one grid point**; **`fixed` ∩ `grid` → `ValueError`**; legacy root-level grid still supported (reserved keys excluded).
- **`validate_testing_grid_for_strategy`** uses the **same** resolved combos as **`run_real_symbol_sweep`**.
- **`params_json`** in sweep rows = **resolved** overrides (fixed + grid) for downstream promotion.

## E. YAML risk/backtest execution mapping

- **`risk.min_risk_per_share`** → **`BacktestConfig.min_risk_per_share`** → **`default_intraday_policy(..., min_risk_per_share=...)`** in **`run_strategy_backtest`** and sweep single-combo helpers.
- **Max trades:** `backtest.max_trades_per_session` > `backtest.max_trades_per_day` > `risk.max_trades_per_session` > `risk.max_trades_per_day` > default **1** (all validated > 0).
- **`backtest.eod_exit_minute`**, slippage, commission, quantity, max_hold, cooldown, recompute_target_from_entry: unchanged ownership — execution still materializes targets from entry on execution-backed path; no second PnL engine.

## F. Candidate root/schema

- **Runtime root:** **`src/strategies/testing_parameters_results/l1_execution_backed_controlled/`** — flat **`*.yaml`** only; **`load_candidates()`** is non-recursive.
- **Research `selected_candidates/`** under the controlled design folder remains **staging/audit** if present; CSV/MD are not runtime truth.

## G. Promotion/validation script

- **`python -m src.research.run_layer1_execution_backed_controlled`** — subcommands **`promote`** (default dry-run; **`--write`** persists YAML + index CSVs) and **`validate-candidates`**.
- Tests: **`tests/test_layer1_contract_alignment.py`** (promotion temp dir + loader + malformed YAML rejection).

## H. Decision

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## I. Explicit non-runs / risks

Same as §C. **Tracked-heavy grep** still hits historical **Archive** paths (pre-existing). **Parquet:** committed under **`data/raw/ibkr/`** (includes **SPY** slices in repo baseline — controlled Layer1 runbook is **QQQ-only**).

## J. Files changed (high level)

`src/backtest/strategy_runner.py`, `src/backtest/engine.py`, `src/backtest/sweep.py`, `src/strategies/loader.py`, `src/research/run_layer1_execution_backed_controlled.py`, `tests/test_layer1_contract_alignment.py`, `src/strategies/testing_parameters_results/l1_execution_backed_controlled/README.md`, `src/research/results/layer1_config_candidate_contract_alignment/**`, `src/research/results/layer1_execution_backed_controlled/*` (schema, execution policy, runner gap, run_commands, artifact CSV), `RESULTS_INDEX.md`, `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `docs/LAYER_FLOW.md`, `docs/MAINLINE_STRUCTURE_SUMMARY.md`.

## K. Local-only artifacts

Future **`runs/`** under **`src/research/results/layer1_execution_backed_controlled/`** — **gitignore** or omit until curated. No real sweep outputs committed in this task.

## L. Recommended next step (exactly one)

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
