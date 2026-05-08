# Train-only frozen system decision

- Selected candidate_set: **gap_only**
- top_per_strategy=1 max_trades_per_day=1
- daily_max_loss_r=-1.5 cooldown=0
- priority_policy=metadata_priority

## Why

- Filters: min trades / PF_R / total_r / drawdown floor / optional 0.02 cost stress from postprocess.
- Prefer primary candidate sets (`failed_only`, `gap_only`, `failed_gap`) over `failed_gap_with_prior_day_diagnostic` unless diagnostic clearly dominates.
- Prefer `max_trades_per_day=1` when scores are close (train stability).

## Caveat

Selection uses **train 2023–2024 only**; test performance is out-of-sample for this YAML.
