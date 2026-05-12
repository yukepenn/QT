# Runner / CLI gap analysis — Layer1 controlled

## What exists today

- **`python -m src.backtest.sweep`** invokes **`main()`** (``if __name__ == "__main__"`` guard added when wiring this design package so documented ``-m`` invocations match tests).

- **`python -m src.backtest.sweep`** supports:
  - **`--strategy`**, **`--symbol`**, **`--start`**, **`--end`**, **`--data-root`**, **`--asset`**
  - **`--grid`** (YAML/JSON grid document)
  - **`--output-root`**, **`--max-combos`**, **`--no-save`**, **`--dry-run`**
  - **`--smoke`** (synthetic), **`--validate-pipeline`**
- Real-symbol path calls **`run_real_symbol_sweep`** → **`run_strategy_backtest`** → **`simulate_trade_path`**.

## Gaps vs ideal “controlled Layer1 product”

1. **No `--engine` flag:** Cannot select an alternate backtest engine from CLI. **Mitigation:** Mainline is already path-backed; document **`execution_engine: execution_backed`** on candidate YAML at selection time.

2. **`engine` column = `reference`:** Sweep stamps `ENGINE_LABEL = "reference"` (historical name). **Mitigation:** Treat as “mainline path engine”; optionally rename in a tiny follow-up PR.

3. **Selection / YAML export:** Implemented as thin **`src/research/run_layer1_execution_backed_controlled.py`** (`promote` with default dry-run; **`--write`** persists YAML + `CANDIDATE_INDEX.csv` under the active candidate root). Still **no** `--engine` on sweep.

4. **`min_risk_per_share` on `ExecutionPolicy`:** **Resolved** — `BacktestConfig` + `run_strategy_backtest` + sweep policy construction thread **`risk.min_risk_per_share`** (and backtest fallback) into **`default_intraday_policy`**.

5. **Post-hoc metrics:** `trades_per_month`, exit histograms may need optional local trade export — **not** for git commit.

## Proposed thin runner

`src/research/run_layer1_execution_backed_controlled.py` — **implemented** (promote + validate-candidates); remains thin (no backtest / no PnL).
