# alignment_decision

**Label:** `ALIGNMENT_FAIL`

**Recommended gate outcome:** `REFINE_REPLAY_ALIGNMENT`

- If `ALIGNMENT_FAIL` persists after best grid row, treat overlay deltas as **non-actionable** until replay model improves.

## max_hold_priority extension (2026-05-11)

- Grid expanded to **18** configs (`alignment_config_manifest.csv`); new rows: **`cfg_0016_mh_forced`**, **`cfg_0017_mh_panelauth`**, **`cfg_0018_mh_skipconf`** (`alignment_grid_results.csv`).
- **`forced_first_on_terminal_bar`** slightly reduces **`total_r_diff`** (~52.4R → ~51.2R) but remains **FAIL**.
- **`panel_exit_reason_authoritative`** is **identical** to **`cfg_0015`** on this panel: all **476** max_hold mismatches exit **before** `panel_exit_idx`, so the terminal-bar-only override never fires.
- **`skip_terminal_bar_conflicts`** shows **`ALIGNMENT_PASS`** only by **excluding** the 476 contested rows from metrics — **diagnostic only**, not an overlay baseline.

