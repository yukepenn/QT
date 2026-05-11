# PA Brooks primitives — Numba / fast-path audit — 2026-05-10

## 1. `price_action.py`

- **Numba:** `@njit` helpers present for small rolling / bar math (see file header region: cached jitted functions for range-width or similar primitives).
- **Scope:** Helpers operate on **numpy scalars/arrays** passed from pandas-derived inputs; no Python objects cross the hot jitted kernels beyond what Numba supports.

## 2. `pa_swings.py`

- **Numba:** `_bars_since_last_in_session`, `_rolling_sum_shift1_session` — session-scoped, numpy array in/out.
- **Pandas:** Rolling range highs/lows, `groupby("session_date")`, and concat of new columns remain **pandas-heavy** — acceptable: feature build runs **once per `feature_key`** and is cached by FeatureStore / Layer 1–2 precompute patterns.

## 3. `regime.py`

- **Vectorized numpy / pandas** for PA router columns; no custom Numba in the Brooks router block.
- **Caching:** Same “build once per key” assumption as other feature stages.

## 4. Strategy fast path

- Strategies continue to expose **`prepare_signal_context` → `generate_signal_arrays_from_context`** with **numpy arrays** for the Numba backtest path.
- **`src/backtest/fast.py`** and combiner simulation paths were **not modified** in this cleanup phase.

## 5. Performance expectation

- Additional swing columns add marginal pandas work at feature-build time; **no evidence** that Numba-rewriting the whole `pa_swings` groupby stack is warranted before Layer 2 profiling.
- **Recommendation:** keep pandas groupbys until Layer 2 / precompute profiling shows a hotspot; avoid speculative Numba refactors.

## 6. Optional timing smoke

- Not instrumented as a strict CI test; developers may time `build_features_from_config` on QQQ Jan 2025 locally if investigating regressions.
