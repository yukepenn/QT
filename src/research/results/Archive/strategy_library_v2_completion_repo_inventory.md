# Strategy Library v2 — completion repo inventory (snapshot)

**Date:** 2026-05-09. **Strategies:** 16 → 25. **Purpose:** record inspected layout before v2_completion plugin work.

## Root / config

| Path | Role |
|------|------|
| README.md, PROJECT_STATUS.md, PROGRESS.md, CHANGES.md | Project narrative |
| docs/ARTIFACT_POLICY.md | Commit vs local artifacts |
| .gitignore, pytest.ini | Hygiene / test config |

## Backtest / combiner / features / strategies (high level)

- `src/backtest/`: `engine.py`, `fast.py` (generic Numba), `sweep.py`, `metrics.py`, `execution.py`
- `src/combiner/`: `run.py`, `sweep.py`, `precompute.py`, `candidate.py`, `diagnostics.py`, `simulator.py`, `postprocess.py`, `behavior.py`, `signal_cache.py`
- `src/features/`: `build_features.py`, `feature_config.py`, `feature_key.py`, `feature_store.py`, `levels.py`, `time_features.py`, `vwap.py`, `orb.py`, `volatility.py`, `volume.py`, `price_action.py`, `indicators.py`, `channels.py`, `regime.py`, `utils.py`, `build_types.py`
- `src/strategies/strategy/`: `base.py`, `fast_utils.py`, `_atr_helpers.py`, + one module per strategy plugin
- `src/strategies/loader.py`, `metadata.yaml`, `metadata.py`, `parameters/*.yaml`, `testing_parameters/*.yaml`
- `tests/`: feature, strategy, combiner, walkforward suites

## Answers (inventory checklist)

1. **Feature modules:** time, vwap, orb, levels, volatility, price_action, volume, **indicators**, **channels**, **regime** (all present).
2. **indicators/channels/regime:** yes, under `src/features/`.
3. **Columns:** see `FEATURE_COLUMNS` in `feature_config.py` (includes expanded indicators + multi-day level fields after completion).
4. **Registered strategies (after completion):** 25 names from `loader.available_strategies()`.
5. **Planned nine plugins:** all newly added (none pre-existed under those names).
6. **Reuse:** `fast_utils` session/rolling helpers, `_atr_helpers.atr_series`, `validate_common_strategy_config`, Numba kernels colocated in strategy files.
7. **Templates:** RSI / VWAP reclaim / prior-day trap patterns for oscillator, reclaim, and level-trap families.
8. **Duplicates:** avoided second feature_key system; MACD grid required explicit tuple superset in YAML.
9. **Import cycles:** none introduced (strategies import features only via DataFrame columns at runtime).
10. **Bugs fixed:** SMA reclaim Numba `mb` parameter; MACD column coverage for grid pairs.

See `strategy_library_v2_completion_implementation_plan.md` and `strategy_library_v2_completion_feature_audit.md` for tables.
