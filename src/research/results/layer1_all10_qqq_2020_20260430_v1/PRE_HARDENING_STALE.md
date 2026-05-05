# Pre-hardening / stale results

This result root (`layer1_all10_qqq_2020_20260430_v1`) was produced **before** research platform hardening **Commits A–D** were complete on `main`.

- **Rankings, sweep CSVs, and `selected_candidates/` YAMLs** may not match behavior of the current codebase (execution validation, drawdown baseline, feature keys, `validate_config`, metrics, and combiner diagnostics all changed).
- **Keep for historical reference only.**
- **Rerun** Layer 1 (and downstream selection) from a post-hardening tag/root before using outputs for Layer 2 or Layer 3 decisions.

See `src/research/results/rerun_plan_after_hardening.md` and `hardening_closeout_20260505.md`.
