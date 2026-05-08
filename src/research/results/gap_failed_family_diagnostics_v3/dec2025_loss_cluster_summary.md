# Dec 2025 loss cluster summary

## Per-run summary

                                                                    run_id  trades   total_r  profit_factor_r  worst_trade_r
                   layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1       8 -8.066056         0.000000      -1.021277
                  layer3_mini_wfo_v2a_qqq_2023_2024_train_2025_202604_test       8 -8.066056         0.000000      -1.021277
                  layer3_mini_wfo_v2b_qqq_2020_2024_train_2025_202604_test      10 -6.273707         0.170346      -1.021277
layer3_mini_wfo_v3_refined_gap_failed_qqq_2023_2024_train_2025_202604_test       9 -2.521580         0.552840      -1.008403

## By strategy

                 group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
gap_acceptance_failure      21 -21.173708 -1.008272  0.000000   -1.021277         0.000000      17.714286                   1
            failed_orb      14  -3.753691 -0.268121  0.357143   -1.009615         0.539952      24.928571                   3

## By exit_reason

   group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
    stop      28 -28.223347 -1.007977       0.0   -1.021277         0.000000      18.464286                   1
max_hold       5   0.557924  0.111585       0.6   -0.607477         1.502771      33.000000                   1
  target       2   2.738024  1.369012       1.0    1.244012              NaN      19.500000                   1

## By day

     group  trades   total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
2025-12-03       4 -4.033613 -1.008403       0.0   -1.008403         0.000000      12.000000                   1
2025-12-12       4 -4.022221 -1.005555       0.0   -1.006757         0.000000       8.750000                   1
2025-12-16       4 -4.021480 -1.005370       0.0   -1.005952         0.000000      14.000000                   1
2025-12-30       4 -3.671306 -0.917827       0.0   -1.021277         0.000000      13.500000                   2
2025-12-11       3 -3.028483 -1.009494       0.0   -1.009615         0.000000       4.333333                   1
2025-12-23       3 -3.018519 -1.006173       0.0   -1.006173         0.000000      23.000000                   1
2025-12-29       3 -3.009119 -1.003040       0.0   -1.003040         0.000000      34.000000                   1
2025-12-10       4 -1.483833 -0.370958       0.5   -1.006623         0.262964      45.000000                   2
2025-12-22       1 -1.007812 -1.007812       0.0   -1.007812         0.000000      43.000000                   1
2025-12-04       1 -1.005025 -1.005025       0.0   -1.005025         0.000000      22.000000                   1
2025-12-18       2  0.635989  0.317995       0.5   -0.502222         2.266350      30.000000                   1
2025-12-01       2  2.738024  1.369012       1.0    1.244012              NaN      19.500000                   1

## By entry minute bucket

group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
 0-15      27 -24.675743 -0.913916  0.074074   -1.021277         0.021004      17.962963                   2
15-30       8  -0.251656 -0.031457  0.375000   -1.007812         0.939035      29.500000                   3

## By risk bucket

group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
>0.10      35 -24.927399 -0.712211  0.142857   -1.021277         0.150194           20.6                   3

## By gap direction

   group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
gap_down      27 -24.275081 -0.899077  0.074074   -1.021277         0.021343      18.888889                   2
  gap_up       6  -3.390342 -0.565057  0.166667   -1.007812         0.251341      28.666667                   2
 unknown       2   2.738024  1.369012  1.000000    1.244012              NaN      19.500000                   1

## By gap size bucket

    group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
    >1.50      24 -19.012922 -0.792205     0.125   -1.021277         0.080637      20.416667                   2
0.50-1.00       6  -6.036376 -1.006063     0.000   -1.006173         0.000000      14.500000                   1
0.25-0.50       1  -1.005025 -1.005025     0.000   -1.005025         0.000000      22.000000                   1
    <0.25       1  -1.003623 -1.003623     0.000   -1.003623         0.000000      38.000000                   1
1.00-1.50       1  -0.607477 -0.607477     0.000   -0.607477         0.000000      45.000000                   1
  unknown       2   2.738024  1.369012     1.000    1.244012              NaN      19.500000                   1

## By VWAP side

     group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
below_vwap      15 -15.156621 -1.010441      0.00   -1.021277         0.000000           10.2                   1
above_vwap      20  -9.770778 -0.488539      0.25   -1.006757         0.310773           28.4                   3

## By ORB context

     group  trades    total_r     avg_r  win_rate  max_loss_r  profit_factor_r  avg_bars_held  exit_reason_unique
inside_orb      34 -24.319922 -0.715292  0.147059   -1.021277          0.15337      19.882353                   3
 above_orb       1  -0.607477 -0.607477  0.000000   -0.607477          0.00000      45.000000                   1

