# CHATGPT_REVIEW_BUNDLE — Layer1 config / candidate contract alignment

## 1. Git / baseline

- Branch: `main`; pre-work tip recorded as **`afc4461`** in `baseline_inventory.csv`.

## 2. Why alignment was needed

Controlled Layer1 run requires **one resolved override contract** for `fixed` + `grid`, **policy threading** for `min_risk`, **max-trades aliases**, and **combiner-compatible candidate YAML** under a stable **runtime root** — without running broad sweeps in this task.

## 3. Correct Layer1 ownership

- **`src/execution/`** — sole accounting truth.
- **`src/strategies/parameters/`** — base configs.
- **`src/strategies/testing_parameters/`** — Layer1 grids.
- **`src/strategies/testing_parameters_results/l1_execution_backed_controlled/`** — active promoted candidates (runtime).
- **`src/research/results/`** — audit/design only.

## 4. Fixed / grid merge contract

`normalize_override_mapping` + `grid_combos_from_document`: **fixed ∪ grid** per combo; **overlap → `ValueError`**; `validate_testing_grid_for_strategy` uses the same resolution as `run_real_symbol_sweep`; **`params_json`** includes flattened fixed + grid keys.

## 5. YAML risk / backtest → execution mapping

See `contract_map.csv` / `contract_map.md`. **`risk.min_risk_per_share`** → **`BacktestConfig`** → **`default_intraday_policy`**. Max-trades: **`backtest.max_trades_per_session`** wins over **`backtest.max_trades_per_day`** and **`risk.*`** aliases.

## 6. Execution policy threading

Implemented in **`engine.py`** and **`sweep.py`** (`min_risk_per_share` on policy construction).

## 7. Candidate active root + schema

Runtime root: **`src/strategies/testing_parameters_results/l1_execution_backed_controlled/`** (README only until promotion). YAML must expose **`strategy`**, **`config`**, **`metrics`**, **`metadata`**, **`selection`**, **`source`**, plus **`execution.execution_engine: execution_backed`**.

## 8. Promotion / validation script

**`src/research/run_layer1_execution_backed_controlled.py`**: `promote` (dry-run default; **`--write`** persists) and **`validate-candidates`**. No backtests / no PnL inside the script.

## 9. Scale-out regression status

Remaining-qty semantics **unchanged**; see `scaleout_regression_status.md`.

## 10. Tests / validation

**163** `pytest`; **`tests/test_layer1_contract_alignment.py`** covers merge, policy, promotion temp-dir write, validate empty/malformed.

## 11. Explicit non-runs

No real Layer1 sweep, Layer2/3, WFO, live/paper, SPY, router, new strategies, semantics edits, Archive moves, legacy delete, Numba, heavy artifacts.

## 12. Decision

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## 13. Recommended next step

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
