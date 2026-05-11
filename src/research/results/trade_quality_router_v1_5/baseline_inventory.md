# Trade Quality Router v1.5 — baseline inventory

**Purpose:** snapshot of repo state and file availability before interpreting v1.5 diagnostics. **Update git tip** with `git log -1 --oneline` after each commit.

## Git tip (fill at commit time)

- **Branch:** `main`
- **Tip:** `ccdd0bb` — `Research: extend trade quality enrichment diagnostics` (repo HEAD may include handoff-only commits after this SHA)

## Handoff decision (pre–v1.5 commit)

- **v1 decision:** `NEED_MORE_TRADE_ENRICHMENT` (see `NEXT_HANDOFF.md` at repo root before v1.5 update).

## v1 curated files (tracked / expected)

| Area | Path |
|------|------|
| Summary | `src/research/results/trade_quality_router_v1/trade_quality_router_v1_summary.md` |
| Design | `src/research/results/trade_quality_router_v1/regime_router_design_from_evidence_v1.md` |
| Schema | `src/research/results/trade_quality_router_v1/trade_output_and_feature_schema_inventory.md` |
| Taxonomy | `src/research/results/trade_quality_router_v1/setup_taxonomy_v1.csv` |
| Key findings | `src/research/results/trade_quality_router_v1/analysis/trade_quality_key_findings.csv` |
| Analysis summary | `src/research/results/trade_quality_router_v1/analysis/trade_quality_analysis_summary.md` |
| VWAP regime / trade# / exit | `src/research/results/trade_quality_router_v1/analysis/vwap_baseline_global_l2/*.csv` |
| Indicator mtp1 | `src/research/results/trade_quality_router_v1/analysis/indicator_completion_mtp1/*.csv` |
| Quality thresholds | `src/research/results/trade_quality_router_v1/quality_score/threshold_simulation_*.csv` |

## Local-only (do not commit)

| Artifact | Typical path |
|----------|----------------|
| Raw combiner trades | `src/research/results/trade_quality_router_v1/local_runs/**/trades.csv` |
| v1 enriched row CSVs | `src/research/results/trade_quality_router_v1/enriched_trades/*_enriched.csv` |
| v1 scored row CSVs | `src/research/results/trade_quality_router_v1/quality_score/scored_trades_*.csv` |
| v1.5 indicator mtp2/3 raw | `src/research/results/trade_quality_router_v1_5/local_runs/indicator_mtp{2,3}/run_*/trades.csv` |
| v1.5 staging enrich | `src/research/results/trade_quality_router_v1_5/enriched_staging/*_enriched.csv` |

## Indicator mtp=2 / mtp=3 raw trades

- **Present locally (this machine):** yes — under `trade_quality_router_v1_5/local_runs/indicator_mtp2/` and `.../indicator_mtp3/` (timestamped `run_*` folders).
- **In git:** no (policy).

## Missing files for automation

- **None** for curated v1.5 outputs once scripts have been run with local enriched inputs; if `enriched_trades/` is absent, regenerate with `src/research/enrich_combiner_trades.py` from local `trades.csv` (not committed).

## v1.5 scripts (research-only)

- `src/research/decompose_regime_unknown.py`
- `src/research/validate_trade_quality_holdout.py`
- `src/research/analyze_exit_slip_attribution.py`
- `src/research/build_indicator_mtp_diagnostics.py`
- `src/research/score_trade_quality_v15.py`
- `src/research/trade_quality_unknown.py` (helpers)

## Diagnostic YAMLs (v1.5)

- `src/research/results/trade_quality_router_v1_5/layer2_diag_indicator_mtp2.yaml`
- `src/research/results/trade_quality_router_v1_5/layer2_diag_indicator_mtp3.yaml`
