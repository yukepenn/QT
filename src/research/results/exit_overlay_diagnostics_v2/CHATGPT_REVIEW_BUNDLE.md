# CHATGPT_REVIEW_BUNDLE — Exit overlay diagnostics v2 (full-panel alignment cycle)

Readable from GitHub raw. **This cycle ran real full-panel alignment** on **10,628** local panel rows; **overlay mode did not run** because alignment **`ALIGNMENT_FAIL`**.

---

## 1. Git / validation

- **Branch:** `main`.
- **Scripts touched:** `src/research/run_exit_overlay_diagnostics_v2.py` (post-alignment manifest + failure CSV/MD writers when label is `ALIGNMENT_FAIL`).
- **Checks:** `python -m compileall -q src` — OK; `python -m pytest -q` — full suite run in this cycle (see `NEXT_HANDOFF.md` §B for counts).
- **Artifact validation:** `python -m src.research.validate_research_artifacts --root src/research/results/exit_overlay_diagnostics_v2 --csv-only --output .../exit_overlay_diagnostics_v2_artifact_validation.csv`.
- **Tracked-heavy:** no tracked `trade_context_panel.csv`, parquet, `overlay_trade_results_v2.csv`, etc.

---

## 2. Why this full-panel run was needed

Committed v2 alignment artifacts were **synthetic smoke** (schema validation only). Economic overlay interpretation requires **combiner_clone** replay to match panel **`r_multiple`** within **per-trade and aggregate** gates on the **real** 10k+ panel.

---

## 3. Local input verification

- **Panel (local-only path, not committed):** `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` — **10,628 × 170**; profiles/windows as expected; see `local_full_panel_input_check.{md,csv}`.
- **QQQ bars:** `data/raw/ibkr` — **617,160** rows; **0** missing sessions vs panel (`bar_load_meta.csv`).

---

## 4. Synthetic v2 artifact warning

- Prior curated **`alignment/*`** numerics were **synthetic**.
- **Archive:** `alignment/archive_synthetic_pre_full_panel/` holds copies before this run.
- **`overlay_v2/*`** CSVs from earlier smoke are **not** updated this cycle — see `overlay_v2/overlay_v2_summary.md` and `overlay_v2/full_panel_overlay_manifest.csv`.

---

## 5. Full-panel alignment result

- **Rows used:** 10,628 (after profile/window filter).
- **Configs:** 15 (`alignment_config_manifest.csv`).
- **Overall label:** **`ALIGNMENT_FAIL`** (`alignment_decision.md`, `alignment_grid_results.csv` best row).
- **Manifest:** `alignment/full_panel_alignment_manifest.csv` — **`synthetic_or_real=real`**.

---

## 6. Best clone config

- **`cfg_0015`:** `entry_bar` + `bar_open_plus_slip` + `panel_exit_price_when_original` + `apply_like_combiner` + `abs_entry_minus_stop` + `stop_first` + `panel_exit_idx` + `panel_target_price` (`alignment_best_config.yaml`).

---

## 7. Alignment pass/fail

- **FAIL** (aggregate gate): `total_r_diff` ≈ **+52.4R** vs budgets (≤5 PASS, ≤15 PASS_WITH_WARNINGS).
- **Per-trade:** mean |ΔR| ≈ **0.035**, median ≈ **0** — good local fit for most rows.

---

## 8. Drift failure analysis

- **Primary mechanism:** **476 / 5188** panel **`max_hold`** rows where replay exits **`target`** (276) or **`stop`** (200) first — `panel_exit_price_when_original` does not apply when exit labels disagree → R drift mass (~+52R signed sum).
- **Files:** `alignment/full_panel_alignment_failure_analysis.md`, `full_panel_alignment_failure_by_exit_reason.csv`, `full_panel_alignment_failure_max_hold_path_divergence.csv`, `full_panel_alignment_failure_by_candidate.csv`, `full_panel_alignment_failure_by_profile.csv`, `full_panel_alignment_failure_examples.csv`.

---

## 9. Overlay results

- **Not run.** Do not use `overlay_v2/*.csv` as full-panel economics until alignment passes and overlay is re-executed.

---

## 10. Ambiguity sensitivity

- **Not run** (overlay skipped).

---

## 11. Context-specific findings

- **Not run.**

---

## 12. Weak-period findings

- **Not run.** See `overlay_v2/weak_period_overlay_v2_interpretation.md`.

---

## 13. Exit vs router/quality comparison

- **Not refreshed.** See `comparison_not_run_reason.md`. Router/quality remains the actionable **selection** path until aligned overlays exist.

---

## 14. Scalp / short roadmap status

- **Deferred** — see `scalp_short_after_exit_overlay_v2.{md,csv}`.

---

## 15. Decision

**`REFINE_REPLAY_ALIGNMENT`**

---

## 16. Explicit non-runs

- No WFO / live / SPY / broad L2 / Global L1.
- No production router / exit-management integration.
- No strategy / feature / YAML edits.
- No row-level panel or overlay CSV commits.

---

## 17. Recommended next step

Fix **max_hold vs intrabar stop/target** reconciliation in **`combiner_clone_long_walk`** (and/or panel exit labeling consistency), then rerun **`--mode alignment`**; if **PASS** or **PASS_WITH_WARNINGS**, rerun **`--mode overlay`** with ambiguity policies and refresh `overlay_v2/*` aggregates.
