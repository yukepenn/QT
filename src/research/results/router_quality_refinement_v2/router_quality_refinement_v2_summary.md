# router_quality_refinement_v2_summary

This cycle refreshed **repo docs consistency**, fixed a small **`json` import** bug in `run_trade_quality_score_v2.py`, added **`run_router_quality_refinement_v2.py`** + **`router_quality_refinement_v2_lib.py`**, and generated **aggregate-only** router/quality v2 diagnostics under `router_v2/` and `quality_v2_refined/`.

## What worked

- **Softer router masks** (`late_climax_guard`, `gap_context_guard`, `combined_light_guard`) can improve **PF_R** and/or **maxDD proxy** while keeping **≥60%** trade retention on key profiles (see `router_v2/router_v2_results.csv`).
- **Quality v2 refinements**: **`percentile_profile_top80`** and **`bottom_cut_20`** on `original_v2_score` show **~80% retention** with PF / maxDD proxy improvements for multiple profiles — flagged **`IN_SAMPLE_DIAGNOSTIC`**.

## What did not work / stayed risky

- **`soft_downweight_proxy`** improves PF on **`pa_gap_mtp2_meta`** but is **too destructive** on **`pa_only_mtp1_meta`** under the configured guardrails (large `delta_total_r`).
- **Fixed `fixed_AB` / `relaxed_AB`** thresholds remain **over-filtering** vs the 60–85% retention goal (see `quality_v2_refined/quality_variant_results.csv`).

## Outputs index

- Router: `router_v2/*`
- Quality: `quality_v2_refined/*`
- Combined: `combined_light_guards/*` (ran because promising rows existed)
- Review bundle: `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `chatgpt_key_tables.csv`
