# PA common helper adoption policy — 2026-05-10

## Canonical import path

- **New code** should import PA shared helpers from **`src.strategies.common.pa`** (e.g. `pa_range_window`, `finalize_long_signals_df`, `pa_context_windows`).

## Backward compatibility

- **`src.strategies.strategy.pa_batch_a_utils`** and **`src.strategies.strategy.pa_common`** remain **thin shims** that re-export the same symbols. Existing strategy plugins and scripts may keep their current import paths.

## Strategy plugin migration

- **No mass import rewrite** in this phase: shims avoid churn and guarantee **zero** intended signal / economics drift.
- Any future migration of `pa_*` strategy files to `common.pa` imports should:
  1. Change **imports only** (no logic edits), or
  2. Run **`check_strategy_fast_parity.py`** per touched strategy and capture fingerprints if used.
- **Do not** change `sig_reason` formatting or threshold logic in a “cleanup” PR without an explicit plan and tests.

## Research scripts

- `pa_gate_diagnostics.py` and similar may continue importing from **`pa_batch_a_utils`** until opportunistically updated to `common.pa`.

## Fingerprints / behavior hashes

- Treat **reason strings**, threshold ordering, and risk field reads as **behavior-sensitive**. Compatibility shims preserve byte-identical helper **implementations** (moved, not rewritten).
