# Format pass — core research modules (maintainability)

## Files inspected

- All Python modules listed in the P0 format scope (loader, features, backtest, combiner, walkforward, research, PA strategies).
- Root `.gitignore` (section headers / comments only).
- `README.md`, `PROJECT_STATUS.md` — reviewed; **no edits** (already readable prose).

## Files reformatted

Applied **`black`** (same style as repo toolchain when present):

- `src/strategies/loader.py`
- `src/strategies/strategy/base.py`
- `src/features/build_features.py`, `feature_key.py`, `feature_config.py`, `price_action.py`, `pa_swings.py`, `regime.py`, `levels.py`
- `src/backtest/execution.py`, `fast.py`, `sweep.py`
- `src/combiner/simulator.py`
- `src/walkforward/mini_wfo.py`
- `src/research/select_candidates.py`
- All `src/strategies/strategy/pa_*.py` (including `pa_batch_a_utils.py`)

## Files left unchanged by Black

- `src/features/build_types.py` — already matched Black output (`black --check` clean).

## Other edits (non-semantics)

- `.gitignore` — reorganized comment sections (**Secrets**, **Python**, **Jupyter/OS**, **Caches**, **Data**, **Heavy combiner / research / walkforward**, **Heavy strategy outputs**, **Curated summaries**); **no ignore rules removed or weakened**.

## Validation (post-format)

- `python -m pytest -q` — **242 passed**
- `python -m compileall -q src` — **OK**
- `python src/strategies/loader.py --list` — **35 strategies**
- `check_strategy_fast_parity.py` — **failed_orb** focused smoke — **TOTAL_MISMATCH_FIELDS approx=0**

## Statement

**No intended behavior changes** — formatting and `.gitignore` comment structure only.
