# max_hold drift overview

- **Detail source:** `src\research\results\exit_overlay_diagnostics_v2\local_rows\alignment_trade_detail.csv` (local-only; do not commit).
- **Panel:** `src\research\results\local_detailed_trade_context_replay_v1\local_rows\trade_context_panel.csv`.

## Counts

- Panel **`max_hold`** rows (cfg_0015): **5188**
- Rows where replay exits **stop/target** while panel says **max_hold**: **476**
- Of those, replay exit bar **before** `panel_exit_idx`: **476**
- **On** `panel_exit_idx`: **0**
- **After** `panel_exit_idx`: **0**

## Interpretation

All observed mismatches in this full-panel run exit **before** the panel `exit_idx`.
That means the dominant failure mode is **not** same-bar max_hold vs intrabar ordering on the terminal bar; 
it is **pre-terminal** path divergence (replay sees an earlier stop/target fill that the archived panel row did not).

Research-only `panel_exit_reason_authoritative` (only forces max_hold when `j == panel_exit_idx`) therefore **does not**
change aggregate metrics vs `intrabar_first` on this dataset.
