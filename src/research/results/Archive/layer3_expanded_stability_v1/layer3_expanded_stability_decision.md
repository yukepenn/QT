# layer3_expanded_stability_decision

## Decision: `PROCEED_TO_PRE_WFO_STABILITY_DESIGN`

### Rationale
- Expanded stability aggregates are computed from **curated complete-smoke** monthly/quarterly/window summaries (no trading rerun).
- **QQQ market context** labels are assigned from **local bar metrics** when parquet partitions exist; otherwise `unknown_mixed` + `market_context_missing_inputs.csv`.
- **Target-limit stress** remains **positive** for `pa_only_mtp1_meta` and `pa_gap_mtp2_meta` on `full_available` per `complete_exit_slip_comparison.csv`.
- **Weak-period exit / candidate quarter slices** are **not** available in curated smoke tables → this run marks **`REQUIRES_LOCAL_DETAILED_REPLAY`** for that attribution layer.
- Overall gate evaluation: **FAIL flags**=no (see `expanded_stability_gate_results.csv`).

### Recommended next step
- **Draft pre-WFO stability design** using window-level stress, quarterly PnL, and QQQ-derived context labels in this output root. Optionally schedule **local-only** weak-quarter replay later for period-sliced exit/candidate tables (do not commit tapes).

### Explicit non-runs
- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global L1 reruns
- No strategy / feature / YAML / router changes

