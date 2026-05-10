# PA structural target semantics

## Current behavior (Option A — documented, no legacy YAML change)

In `pa_batch_a_utils.long_stop_target`, modes such as `range_mid`, `upper_third`, `range_high`, `prior_swing_high`, `vwap`, `channel_mid`, `prior_high`, etc. compute a **target price at the signal bar**, then convert that into **`TM_FIXED_R`** economics by deriving an effective **R-multiple** vs signal-bar risk (`close − stop`). The fast engine therefore sees **fixed-R target mode**, not a persistent fixed-price structural exit that tracks updated VWAP/range levels bar-by-bar.

This matches **Option A** in the P0 plan: **minimum behavior change**, backward-compatible with existing YAML.

## Explicit `*_fixed_px` modes

Not implemented in this phase. Future work could add explicit modes that map to `TM_FIXED_PX` without renaming legacy strings.

## Tests

See `tests/test_pa_structural_targets.py` — asserts `fixed_r` and structural modes resolve through `TM_FIXED_R`, and invalid geometry returns `None`.

## Impact on prior research

Comparable across runs **if** configs used the same semantic modes; economics remain defined at signal bar. Reruns are **not** required solely because of this documentation—only if strategy math changes later.
