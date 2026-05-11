# Fixed-profile OOW — decision

**Decision:** `NEED_MORE_FIXED_PROFILE_OOW`

## Rationale

- Automated label uses only rows with `status=OK` on **early_oow** + **late_oow** for primary profiles (`vwap_mtp2`, `vwap_mtp1`, `indicator_mtp1`).
- If no combiner runs are present under `local_runs/`, decision defaults to **`NEED_MORE_FIXED_PROFILE_OOW`**.
- Interpret human-in-the-loop using `oow/fixed_profile_oow_metrics.csv`, exit-slip tables, and trade-number CSVs.

## Explicit non-runs

- mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid
- Strategy / feature / selected-candidate YAML edits; hard regime filter; combiner `regime_router`
- Parameter optimization on OOW windows; OOW-driven candidate selection

## Recommended next step

Execute: **`NEED_MORE_FIXED_PROFILE_OOW`** (see `fixed_profile_oow_v1_summary.md` section 15 for narrative).
