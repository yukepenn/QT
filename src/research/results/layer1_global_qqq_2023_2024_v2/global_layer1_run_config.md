# Global Layer 1 run configuration

- asset: `equity`
- symbol: `QQQ`
- window: `2023-01-01` → `2024-12-31`
- audit: `D:\OneDrive - Washington University in St. Louis\QT\src\research\results\global_strategy_audit_v2\strategy_eligibility_matrix.csv`
- tag: `layer1_global_qqq_2023_2024_v2` (safe: `layer1_global_qqq_2023_2024_v2`)
- max_grid_size: **1500**
- strategy_limit: **None**
- preflight_only: **False**
- select_candidates: **True**

Re-run without `--strategy-limit` after validating disk/time budget.
