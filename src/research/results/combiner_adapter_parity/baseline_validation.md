# Baseline validation — combiner_adapter_parity

Commands run after code changes (post-fixture):

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **133** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK — `--engine` documents `legacy_reference` / `execution_backed` (and aliases) |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.run_combiner_adapter_parity` | OK — writes `parity/` + default `smoke/` placeholders |

Tracked-heavy patterns: no new large artifacts staged in this task (existing Archive paths unchanged).
