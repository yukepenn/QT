# Fixed-profile OOW v1 — baseline inventory

## Git tip

Run `git log -1 --oneline` after pull/commit. Primary implementation commit message: **`Research: validate fixed profiles out of window`**.

## Handoff decision (pre-run)

Trade Quality Router v1.5 recommended **`NEED_MORE_TRADE_ENRICHMENT`**. This OOW pack adds **fixed-profile replay + postprocess** scaffolding; automated gate defaults to **`NEED_MORE_FIXED_PROFILE_OOW`** until `local_runs/` contains combiner outputs.

## QQQ data (this workspace)

- **Local parquet:** present — see `data_availability.md` (example: **1588** RTH sessions on **2020-01-01 → 2026-04-30** full span per last `inspect-data` run).
- **Do not download** data in-repo; refresh availability after adding/removing partitions.

## v1 / v1.5 references (tracked)

- `src/research/results/trade_quality_router_v1_5/trade_quality_router_v1_5_summary.md`
- `src/research/results/trade_quality_router_v1_5/router_readiness_decision_v15.md`
- `src/research/results/trade_quality_router_v1_5/trade_quality_router_v1_5_key_findings.csv`
- v1 analysis + quality score paths as in Trade Quality Router task list.

## Fixed-profile configs (this root)

- `configs/layer2_fixed_vwap_mtp2.yaml`
- `configs/layer2_fixed_vwap_mtp1.yaml`
- `configs/layer2_fixed_indicator_mtp{1,2,3}.yaml`

## Local-only (never commit)

- `local_runs/**` (raw `trades.csv`, `metrics.json`, logs)
- Enriched / scored row CSVs produced from those trades

## Paste to ChatGPT (optional)

- `fixed_profile_oow_v1_summary.md`
- `fixed_profile_oow_decision.md`
- `oow/fixed_profile_oow_metrics.csv` (after runs)

## Missing until local execution

- Populated `oow/fixed_profile_oow_metrics.csv` rows with `status=OK`
- Non-empty exit-slip / regime / score-transfer CSVs (depend on runs + optional enrichment)
