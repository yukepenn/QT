# exit_overlay_diagnostics_v2_decision

## Decision label (exactly one)

**`REFINE_REPLAY_ALIGNMENT`**

## Rationale

- Full-panel **real** alignment ran on **10,628** Champion v0 rows with **617,160** QQQ 1m bars (`data/raw/ibkr`, zero missing sessions).
- Best grid row **`cfg_0015`** achieves low **mean / median** absolute R error vs panel, but **aggregate `total_r_diff` ≈ +52.4R** exceeds the **≤5R / ≤15R** budgets → label **`ALIGNMENT_FAIL`** (see `alignment/alignment_grid_results.csv`, `full_panel_alignment_manifest.csv`).
- Failure analysis shows drift is **not** target/stop micro-slips: it concentrates on **5188** panel **`max_hold`** rows; **476** of those have replay exiting **`target`** or **`stop`** first — **path / same-bar ordering** vs panel `max_hold` labeling (`alignment/full_panel_alignment_failure_*`).
- **`--mode overlay`** was **not** executed; existing `overlay_v2/*` aggregates remain **non-authoritative** for economics until alignment passes (see `overlay_v2/overlay_v2_summary.md`, `overlay_v2/full_panel_overlay_manifest.csv`).

## Recommended next step

Refine **`combiner_clone_long_walk`** / panel exit labeling so **max_hold** vs intrabar **stop/target** resolution matches the combiner + archived panel; then rerun **`--mode alignment`**, and only if PASS / PASS_WITH_WARNINGS rerun **`--mode overlay`** with ambiguity policies.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production regime router, no production exit-management integration.
- No strategy plugins, feature primitives, or selected-candidate YAML edits.
- No promotion of configs into production paths.
- No commit of row-level `trade_context_panel.csv`, `alignment_trade_detail.csv` (local-only), `overlay_trade_results_v2.csv`, parquet, logs, caches.
