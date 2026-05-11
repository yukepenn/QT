# exit_overlay_diagnostics_v2_decision

## Decision label (exactly one)

**`REFINE_REPLAY_ALIGNMENT`**

## Rationale

- Repo-curated alignment grid on a **single synthetic session row** labels **`ALIGNMENT_FAIL`** for the best grid row; **full Champion v0 panel (~10.6k rows) must be re-run locally** with QQQ parquet to confirm whether **`cfg_0001`**-style combiner defaults (entry open + slip, exit slip, `stop_first`, `max_hold` 120) achieve the ≤0.05R / ≤0.02R median targets.
- V1 **`fixed_target_replay`** drift is explained primarily by **missing combiner exit slip on stop/target** and secondarily by **entry / risk / target materialization** choices — see `combiner_semantics_inventory.md` and `replay_drift_hypotheses.csv`.
- Contextual overlays (`*_contextual`) and ambiguity sweeps are **wired in code**; headline aggregates in git include **synthetic smoke** rows for schema validation — **do not** treat as economic evidence until the alignment gate passes on the real panel.
- Router/quality v2 remains the stronger **trade-selection** path until aligned exit replay proves overlay deltas stable under **`stop_first`** with acceptable ambiguity rates.
- No production exit-management integration; no combiner production edits.

## Recommended next step (exactly one)

Re-run **`python -m src.research.run_exit_overlay_diagnostics_v2 --mode alignment`** on the **local** `trade_context_panel.csv` with **`data/raw/ibkr`** QQQ partitions present; review `alignment/alignment_grid_results.csv`; if **`ALIGNMENT_PASS`** or **`ALIGNMENT_PASS_WITH_WARNINGS`**, re-run **`--mode overlay`** with the written `alignment/alignment_best_config.yaml`.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production router or exit-management in combiner.
- No strategy / feature / selected-candidate YAML edits.
- No short or scalp strategy implementations.
- Row-level `local_rows/**` and `trade_context_panel.csv` remain local-only.
