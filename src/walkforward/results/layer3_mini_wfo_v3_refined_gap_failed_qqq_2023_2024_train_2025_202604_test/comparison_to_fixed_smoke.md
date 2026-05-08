# Comparison to fixed smoke references

| system | trades | total_r | PF_R | note |
|---|---:|---:|---|---|
| trap_recent_top1 (smoke ref) | 323 | 69.057 | >1 (ref) | High headline R; selected on recent window — not causal train→test.… |
| opening_pair_full_history (smoke ref) | 204 | 7.547 | >1 (ref) | Lower R; broader selection context — use as sanity anchor only.… |
| qqq_mini_wfo_v3_refined_gap_failed_2023_2024_train_2025_202604_test_frozen_rank1 | 139 | 5.058063616601594 | 1.0696313920607203 | Causal path: Layer 1+2 on train only, frozen for test.… |
