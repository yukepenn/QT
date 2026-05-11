# overlay_v2_summary

**Status (2026-05-11):** **`--mode overlay` was not executed** on the real full panel because **`alignment_decision.md`** reports **`ALIGNMENT_FAIL`** (aggregate `total_r_diff` exceeds PASS / PASS_WITH_WARNINGS budgets for the best **economic** grid row `cfg_0015`). A **`skip_terminal_bar_conflicts`** row shows **`ALIGNMENT_PASS`** only by excluding max_hold/stop/target mismatches — **not** an overlay-eligible baseline (`alignment_grid_results.csv`, `max_hold_alignment_v1/`).

Existing CSVs under `overlay_v2/` from earlier **synthetic smoke** runs remain for **schema / plumbing validation only**. They are **not** economic evidence on the 10,628-row Champion v0 panel.

**Next:** after replay alignment reaches PASS or PASS_WITH_WARNINGS under a headline clone policy, rerun overlay with `--alignment-config alignment/alignment_best_config.yaml` and refresh aggregates; keep row-level `overlay_trade_results_v2.csv` local-only.
