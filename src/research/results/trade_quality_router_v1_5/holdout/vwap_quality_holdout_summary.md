# VWAP quality score — calendar holdout (v1.5)

Train thresholds for `top80` / `top60` are **20th / 40th percentile** of **train** scores, applied to **test**.
Row `test_top80_thr_test_dist_DIAG` uses **test** distribution (leakage diagnostic; do not use for decisions).

Example 2023→2024 test top80 (train threshold): **167** trades, total_r **9.594580883496665**

## Robustness

- If test `total_r` under train-threshold top80 beats test `all` inconsistently across splits, treat as **not robust**.
