# Baseline validation

| Check | Result |
|-------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | 125 passed (after adapter + tests) |
| `python -m src.strategies.loader --list` | 35 strategies |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | exit 0 |
| `python -m src.combiner.run --help` | shows `--engine` and `--dry-run` |

## Tracked-heavy scan

PowerShell `git ls-files | Select-String` for trades/parquet/npy patterns: **no matches** in index.
