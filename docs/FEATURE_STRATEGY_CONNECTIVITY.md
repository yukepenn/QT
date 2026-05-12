# Feature ↔ strategy connectivity

**Date:** 2026-05-11

## Data → features

- `src/data/read_bars.py` supplies normalized OHLCV (+ session columns).
- `src/features/build_features.py` / `FeatureStore` add **no-lookahead** columns keyed by `feature_key` / config.

## Features → strategies

- Strategies declare **`required_features()`**; loader validates config against strategy needs.
- `src/strategies/metadata.py` + `metadata.yaml` supply **family**, **setup_type**, **playbook**, **default_management_mode**, **required_features** list for router-era defaults.

## Strategies → backtest

- Strategies emit raw signal columns; the **standard contract** is documented in `docs/SIGNAL_CONTRACT.md`.
- `run_strategy_backtest` maps to `TradeIntent` and calls **canonical execution** (`simulate_trade_path`).

## Strategies → combiner

- Precompute / signal cache store **signals or feature caches** only — never fill or PnL math.

## Metadata

- `get_strategy_metadata` merges YAML with `_FALLBACK` when a strategy has no row — keeps loaders resilient.

CSV: `docs/FEATURE_STRATEGY_CONNECTIVITY.csv`.
