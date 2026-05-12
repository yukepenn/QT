# Combiner adapter v1 — summary

## What changed

- Added `src/combiner/trade_intent_adapter.py` (`TradeIntent` build, policy bridge, row mapper).
- Added `src/combiner/adapter.py` (`simulate_combiner_canonical` sequential loop).
- Reworked `src/combiner/simulator.py`: lazy legacy load from `archive/legacy_combiner/reference_simulator.py`; canonical entrypoint; `simulate_combiner_numba` → legacy alias.
- Wired `--engine {legacy,canonical}` and `--dry-run` in `src/combiner/run.py`; `run_combiner_fixed_config(..., engine=...)`.
- Wired `--engine` in `src/combiner/sweep.py`.
- Tests: `tests/test_combiner_adapter.py` + updated simulator tests.
- Research bundle under `src/research/results/combiner_adapter_v1/`.
- Added `src/research/validate_research_artifacts.py` for lightweight CSV scans.

## Validation

- `pytest`: 125 passed (post-change in dev session).
- `compileall`: OK.

## Decision

`COMPLETE_COMBINER_ADAPTER_V2` — parity harness and closer legacy alignment remain.
