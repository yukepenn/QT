# exit_overlay_diagnostics_v2_decision

## Decision label (exactly one)

**`REFINE_REPLAY_ALIGNMENT`**

## Rationale

- Full-panel **real** alignment reran on **10,628** Champion v0 rows with **617,160** QQQ 1m bars; **`alignment_decision`** remains **`ALIGNMENT_FAIL`** for headline clone **`cfg_0015`** (`total_r_diff` ≈ **+52.4R**).
- Combiner audit (`max_hold_alignment_v1/combiner_max_hold_semantics.md`): on each in-position bar, **intrabar stop/target are evaluated before `max_hold`**; terminal **`max_hold` does not preempt** intrabar touches on that bar (`src/combiner/simulator.py`).
- Max_hold drift is **5188** panel rows typed **`max_hold`**; **476** have replay exiting **`stop`** or **`target`** first. Row-level classification (`max_hold_alignment_v1/max_hold_drift_overview.*`): **all 476** replays exit on a bar index **strictly before** `panel_exit_idx` (**pre-terminal** path divergence), not “same bar max_hold vs intrabar”.
- Research-only modes: **`forced_first_on_terminal_bar`** marginally lowers **`total_r_diff`** (~**51.2R**); **`panel_exit_reason_authoritative`** matches **`cfg_0015`** aggregates because the override only applies at **`j == panel_exit_idx`**; **`skip_terminal_bar_conflicts`** yields **`ALIGNMENT_PASS`** only by **excluding** mismatches — **not** overlay-eligible.
- **`--mode overlay`** was **not** executed; gate **`OVERLAY_BLOCKED_ALIGNMENT_FAIL`** (`max_hold_alignment_v1/overlay_gate_after_max_hold_alignment.md`).

## Recommended next step

Reconcile **pre-terminal** replay vs panel for the **476** rows: verify **entry bar index**, **stop/target levels**, **`panel_exit_idx` cap**, and **session bar alignment** against combiner materialization assumptions before changing economic overlay design.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production regime router, no production exit-management integration.
- No strategy plugins, feature primitives, or selected-candidate YAML edits.
- No promotion of configs into production paths.
- No commit of row-level `trade_context_panel.csv`, `alignment_trade_detail.csv` (local-only), `overlay_trade_results_v2.csv`, parquet, logs, caches.
