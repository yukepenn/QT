# Baseline validation

All Phase 1 checks were run on **2026-05-11** after implementing the exit-overlay runner and tests.

| Check | Result |
|-------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **142** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.run_combiner_adapter_parity --help` | OK |
| `python -m src.research.run_exit_overlay_execution_path --help` | OK |

**Tracked-heavy note:** `git ls-files` still matches historical `local_runs` text stubs under `src/research/results/Archive/...`; this task did not add `top_runs`, `trades.csv`, `npy`, or similar under the new result root.

Machine-readable duplicate: `baseline_validation.csv`.
