# Exit / slippage attribution (research overlay)

## Simulator behavior (unchanged)

- `src/combiner/simulator.py` uses one `slippage_per_share` for **both** entry and exit fills (`_py_exit_price`).
- Published `r_multiple` already reflects that constant.

## Overlay scenarios (additive deltas vs published)

- `symmetric_stress_extra_r`: marginal **+0.01 slip/share on entry and exit** vs baseline 0.01 → **-0.02/risk** R.
- `target_limit_adjusted_stress_r`: symmetric stress, but **target** exits do not take the extra exit-leg slip vs STRESS.
- `target_limit_baseline_r`: toy recovery of **baseline exit slip** on targets only (limit-at-raw).
- `stop_only_stress_r`: baseline published R plus **one-leg** extra stress on stop/forced exits only.
