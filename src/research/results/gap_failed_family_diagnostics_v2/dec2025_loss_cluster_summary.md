# Dec 2025 loss cluster summary

## Per-run summary

                                                  run_id  trades   total_r  profit_factor_r  worst_trade_r
 layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1       8 -8.066056         0.000000      -1.021277
layer3_mini_wfo_v2a_qqq_2023_2024_train_2025_202604_test       8 -8.066056         0.000000      -1.021277
layer3_mini_wfo_v2b_qqq_2020_2024_train_2025_202604_test      10 -6.273707         0.170346      -1.021277

## By strategy

                 group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
gap_acceptance_failure      21 -21.173708 -1.008272       0.0   -1.021277         0.000000      17.714286                   1
            failed_orb       5  -1.232111 -0.246422       0.4   -1.009615         0.511114      12.000000                   3

## By exit_reason

   group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
    stop      23 -23.191726 -1.008336       0.0   -1.021277         0.000000           17.0                   1
max_hold       2  -0.458105 -0.229052       0.5   -0.502222         0.087845           15.0                   1
  target       1   1.244012  1.244012       1.0    1.244012              NaN           11.0                   1

## By day

     group  trades   total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
2025-12-30       3 -3.063830 -1.021277  0.000000   -1.021277         0.000000       3.000000                   1
2025-12-11       3 -3.028483 -1.009494  0.000000   -1.009615         0.000000       4.333333                   1
2025-12-03       3 -3.025210 -1.008403  0.000000   -1.008403         0.000000      12.000000                   1
2025-12-23       3 -3.018519 -1.006173  0.000000   -1.006173         0.000000      23.000000                   1
2025-12-16       3 -3.017857 -1.005952  0.000000   -1.005952         0.000000       6.000000                   1
2025-12-12       3 -3.015464 -1.005155  0.000000   -1.005155         0.000000       8.000000                   1
2025-12-29       3 -3.009119 -1.003040  0.000000   -1.003040         0.000000      34.000000                   1
2025-12-10       3 -1.969127 -0.656376  0.333333   -1.006623         0.021914      45.000000                   2
2025-12-18       1 -0.502222 -0.502222  0.000000   -0.502222         0.000000      15.000000                   1
2025-12-01       1  1.244012  1.244012  1.000000    1.244012              NaN      11.000000                   1

## By entry minute bucket

group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
 0-15      24 -23.147609 -0.964484  0.041667   -1.021277         0.001902      16.916667                   2
15-30       2   0.741790  0.370895  0.500000   -0.502222         2.477015      13.000000                   2

## By risk bucket

group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
>0.10      26 -22.405819 -0.861762  0.076923   -1.021277         0.054365      16.615385                   3

## By gap direction

   group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
gap_down      21 -20.129090 -0.958528  0.047619   -1.021277         0.002187      16.047619                   2
  gap_up       4  -3.520741 -0.880185  0.000000   -1.006173         0.000000      21.000000                   2
 unknown       1   1.244012  1.244012  1.000000    1.244012              NaN      11.000000                   1

## By gap size bucket

    group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
    >1.50      19 -17.613455 -0.927024  0.052632   -1.021277         0.002499      17.578947                   2
0.50-1.00       6  -6.036376 -1.006063  0.000000   -1.006173         0.000000      14.500000                   1
  unknown       1   1.244012  1.244012  1.000000    1.244012              NaN      11.000000                   1

## By VWAP side

     group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
below_vwap      12 -12.135380 -1.011282  0.000000   -1.021277         0.000000       6.333333                   1
above_vwap      14 -10.270439 -0.733603  0.142857   -1.006623         0.111444      25.428571                   3

## By ORB context

     group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
inside_orb      26 -22.405819 -0.861762  0.076923   -1.021277         0.054365      16.615385                   3

