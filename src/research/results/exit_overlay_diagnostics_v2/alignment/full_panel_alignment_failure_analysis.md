# full_panel_alignment_failure_analysis

Git tip: `42ffe0bc32c4` | Best grid config: `cfg_0015` | Overall label: `ALIGNMENT_FAIL`

## Headline

- Per-trade mean and median absolute R differences are **small** (~0.035R mean, ~0R median) for `cfg_0015`.
- **Aggregate gate fails**: `total_r_diff` exceeds the ≤5R (PASS) / ≤15R (PASS_WITH_WARNINGS) budgets.
- Drift concentrates where the **panel exit path** disagrees with the **clone walk**.

## Panel `max_hold` vs replay exit (path divergence)

- Among 5188 panel rows with `exit_reason == max_hold`, **476** have |ΔR| > 0.
- For mismatched rows, replay `exit_reason_replay` is often **`target`** or **`stop`**, not `max_hold`.
- When replay exit differs from panel exit, `panel_exit_price_when_original` does not apply; simulated fills drive R divergence.

## By panel exit_reason

| exit_reason | rows | mean_abs_r_diff | sum_signed_r_diff | exit_reason_match_rate |
| --- | --- | --- | --- | --- |
| max_hold | 5188 | 0.07160665551921584 | 52.40313920704778 | 0.9082498072474943 |
| target | 1862 | 1.2845435420684491e-14 | 1.8679724433923184e-11 | 1.0 |
| stop | 3570 | 3.3658727843481775e-15 | -1.2016165840122994e-11 | 1.0 |
| end_of_session | 8 | 0.0 | 0.0 | 0.0 |

## Max-hold path divergence counts

| exit_reason_replay | rows |
| --- | --- |
| stop | 200 |
| target | 276 |

## Next debug targets

1. Reconcile **max_hold** labeling in the panel vs combiner walk (target/stop vs cap on same bar).
2. Compare **`exit_idx`** vs walk terminal index for max_hold rows.
3. Research-only diagnostic: when panel exit is `max_hold`, optionally force terminal bar fill without intermediate intrabar re-resolution.
