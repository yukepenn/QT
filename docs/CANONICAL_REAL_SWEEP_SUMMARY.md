# Canonical real-symbol sweep — summary

**Date:** 2026-05-11

## What shipped

- **`src/backtest/strategy_runner.py`:** load/merge config, grid flattening, feature build, signal generation, `prepare_canonical_signals`, and `validate_canonical_pipeline` (no backtest).
- **`src/backtest/sweep.py`:** `run_canonical_real_symbol_sweep`, `run_single_canonical_from_signals`, CLI flags `--asset`, `--validate-pipeline`, `--dry-run`, full real-symbol argument set, artifact writers, guarded `--data-root` usage.
- **Tests:** strategy runner, real connector (monkeypatched `read_bars`), CLI smoke.

## CLI recap

| Mode | Command sketch |
|------|----------------|
| Synthetic | `python -m src.backtest.sweep --smoke` |
| Metadata validate | `python -m src.backtest.sweep --validate-pipeline --strategy <name>` |
| Full pipeline validate | add `--symbol QQQ --start YYYY-MM-DD --end YYYY-MM-DD` (uses `--data-root` or defaults to `data/raw/ibkr`) |
| Real sweep | same as full validate **plus** required `--data-root`; optional `--grid`, `--config`, `--output-root`, `--dry-run` |

## Non-goals

Historical research grids, WFO, combiner, Champion migration claims.
