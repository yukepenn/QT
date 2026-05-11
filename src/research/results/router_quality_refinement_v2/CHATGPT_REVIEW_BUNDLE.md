# CHATGPT_REVIEW_BUNDLE — router_quality_refinement_v2

## 1. Git / validation

- **Branch:** `main` (expected).
- **Baseline parent (pre-cycle tip):** `d81a1791bcf7d254b4754988816ea8969dce4c2c` — `Research(router): run local trade context replay`.
- **This cycle commit message:** `Research(router): refine offline quality diagnostics` — resolve SHA with `git log -1 --format=%H` on synced `main`.
- **Validation run in this cycle:** `python -m compileall -q src` OK; `python -m pytest -q` → **474 passed**; `python -m src.strategies.loader --list` → **35** strategies; `validate_research_artifacts` on `router_quality_refinement_v2/` OK (see `router_quality_refinement_v2_artifact_validation.csv`).

## 2. Why this task was needed

- `README.md` had drifted from the **current** Layer1/Layer2/Layer3 + playbook + local-replay architecture.
- Offline router v1 masks included **very aggressive** filters (e.g. `preferred_or_neutral_only` ~**19%** retention in `router_filter_results.csv`).
- Quality v1/v2 fixed buckets were **too sparse** for practical filtering; needed **recalibration experiments** with explicit in-sample diagnostics.

## 3. README / docs consistency update

- `README.md` is now a **short front page** with the seven required sections (what QT is, architecture, Champion v0, active direction, artifact policy, how to review, non-goals).
- Project indexes updated: `PROJECT_STATUS.md`, `CHANGES.md`, `PROGRESS.md`, `RESULTS_INDEX.md`, `NEXT_HANDOFF.md`.

## 4. Champion v0 freeze recap

- `pa_only_mtp1_meta` — **CLEAN_BASELINE** (PA only)
- `pa_gap_mtp2_meta` — **DEFAULT_COMBINED** (PA + GAP)
- `primary_mtp2_meta` — **BREADTH_REFERENCE_ONLY** (PA + GAP + CCI)

## 5. Local panel availability

- **Local-only panel exists** in this workspace: `local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` (**10,628** rows × **170** cols).
- **Committed coverage mirror:** `local_detailed_trade_context_replay_v1/aggregates/trade_context_coverage.csv`.

## 6. Router v1 recap (committed)

- See `local_detailed_trade_context_replay_v1/router_diagnostics_v1/router_filter_results.csv`.
- Headline: v1 includes **highly destructive** filters (`preferred_or_neutral_only`, `context_fit_preferred_only`) alongside softer cuts.

## 7. Router v2 results (this cycle)

- Output folder: `router_quality_refinement_v2/router_v2/`.
- **Promising examples (not production):**
  - `late_climax_guard` improves **PF_R** with **~0.82–0.90** retention on all three profiles (see `router_v2_results.csv`).
  - `gap_context_guard` / `combined_light_guard` show **small** PF / maxDD proxy improvements with **high retention** on some profiles.
- **Too destructive example:** `soft_downweight_proxy` helps **`pa_gap_mtp2_meta`** PF but fails **`pa_only_mtp1_meta`** guardrails (large `delta_total_r`).

## 8. Quality v1/v2 recap

- v1 group table remains in `local_detailed_trade_context_replay_v1/quality_score_v2/quality_group_results.csv` (sparse **A-only** story).
- v2 refined outputs: `router_quality_refinement_v2/quality_v2_refined/quality_variant_results.csv`.

## 9. Quality refinement v2 results (this cycle)

- **Fixed thresholds** (`fixed_AB`, `relaxed_AB`) remain **<60% retention** for default combined — mostly labeled over-filters / sparse.
- **Percentile / bottom-cut** schemes often reach **~70–80% retention** with PF / maxDD proxy improvements — flagged **`in_sample_diagnostic=True`** in results CSV.

## 10. Combined light guards

- Because both router and quality passes produced **`PROMISING`** labels, combined tests ran: `combined_light_guards/combined_guard_results.csv`.
- Example: `late_climax_guard` + `bottom_cut_20` keeps **~70%** trades on `pa_gap_mtp2_meta` but still has **material `delta_total_r`** tradeoffs on `primary_mtp2_meta` in this aggregate pass.

## 11. Exit overlay implications

- See `exit_overlay_implications.md` / `.csv`.
- Heuristic preview (`exit_mode_assignment_preview.csv`) still favors **`trend_swing`** and **`runner`** vs **`scalp`**.

## 12. Scalp / short roadmap status

- See `scalp_short_status_update.md` / `.csv` — **scalp/short remain roadmap-only**; short is a **future standalone** branch.

## 13. Decision

- **`RUN_EXIT_OVERLAY_DIAGNOSTICS`** — see `router_quality_refinement_v2_decision.md`.

## 14. Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 reruns.
- No production router wiring; no strategy signal semantics changes; no selected-candidate YAML edits.
- No committing `local_rows/**`, raw trades, caches, parquet/npy/npz/memmap.

## 15. Recommended next step

- Build/run an **offline exit-overlay diagnostic harness** beginning with **`trend_swing`**, then **`runner`**, emitting **aggregate-only** evidence tables comparable to router/quality outputs.
