# Overlay gate after max_hold alignment refinement

**Decision:** `OVERLAY_BLOCKED_ALIGNMENT_FAIL`

- Headline clone config **`cfg_0015`** still fails aggregate budgets (`total_r_diff` > 15R).
- **`skip_terminal_bar_conflicts`** achieves PASS only by excluding the contested rows — **not** an overlay-eligible baseline.
- **`panel_exit_reason_authoritative`** matches **`intrabar_first`** on this panel because every max_hold/stop/target mismatch exits **before** `panel_exit_idx`.

**Do not run `--mode overlay` until a PASS / PASS_WITH_WARNINGS config exists under an economically interpretable clone policy.**
