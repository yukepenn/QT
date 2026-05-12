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

3. **No built-in selection / YAML export:** Sweep writes **`sweep_results.csv`**, **`sweep_summary.md`**, **`sweep_meta.json`** (per existing `write_real_sweep_artifacts`). **No** `selected_candidates/` writer. **Mitigation:** **`ADD_LAYER1_CONTROLLED_RUNNER`** was considered; design decision is **`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`** because sweeps are sufficient for first pass and selection can be a **small** follow-up script in-repo without broad runner.

4. **`min_risk_per_share` on `ExecutionPolicy`:** `run_strategy_backtest` does not yet pass `risk.min_risk_per_share` from strategy YAML into **`default_intraday_policy`**. Combiner hardening **does** wire this. **Mitigation:** one-line policy threading in **`engine.py`** in the **run** task (documented in `execution_policy_design.csv`).

5. **Post-hoc metrics:** `trades_per_month`, exit histograms may need optional local trade export — **not** for git commit.

## Proposed thin runner (not created in this design task)

`src/research/run_layer1_execution_backed_controlled.py` — optional if shell loops become unwieldy; should stay thin (invoke sweep + selection + validate).
