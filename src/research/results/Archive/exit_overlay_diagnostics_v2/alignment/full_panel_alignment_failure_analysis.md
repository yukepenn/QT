# full_panel_alignment_failure_analysis

**Best config:** `cfg_0015` | **Label:** `ALIGNMENT_FAIL`

## Summary

- Aggregate `total_r_diff` exceeds PASS / PASS_WITH_WARNINGS budgets while per-trade mean/median may still look small.
- Inspect `full_panel_alignment_failure_max_hold_path_divergence.csv` when panel `exit_reason` is `max_hold` but replay exits `target` / `stop`.

## By panel exit_reason

| exit_reason | rows | mean_abs_r_diff | sum_signed_r_diff | exit_reason_match_rate |
| --- | --- | --- | --- | --- |
| max_hold | 5188 | 0.07160665551921586 | 52.40313920704777 | 0.9082498072474943 |
| target | 1862 | 1.2879302589212261e-14 | 1.8677948077083784e-11 | 1.0 |
| stop | 3570 | 3.392493257991851e-15 | -1.2002843163827492e-11 | 1.0 |
| end_of_session | 8 | 4.163336342344337e-17 | -3.3306690738754696e-16 | 0.0 |

## Max-hold path divergence

| exit_reason_replay | rows |
| --- | --- |
| stop | 200 |
| target | 276 |

