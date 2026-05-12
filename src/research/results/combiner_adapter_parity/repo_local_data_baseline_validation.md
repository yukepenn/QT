# Baseline validation — repo-local parity task

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **135** passed |
| `python -m src.strategies.loader --list` | OK (35 strategies listed) |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK (not re-pasted here) |
| `python -m src.research.run_combiner_adapter_parity --help` | OK — shows `--bar-root`, `--data-dir`, `--real-smoke-suite`, `--aggregate-only`, `--dry-run` |
| `python -m src.research.validate_research_artifacts --root src/research/results/combiner_adapter_parity --csv-only` | OK → `combiner_adapter_parity_artifact_validation.csv` |

Recorded: **2026-05-11**.
