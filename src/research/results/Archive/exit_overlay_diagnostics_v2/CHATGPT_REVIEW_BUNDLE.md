# CHATGPT_REVIEW_BUNDLE — Exit overlay diagnostics v2 (max_hold alignment refinement)

Readable from GitHub raw. **Alignment:** still **`ALIGNMENT_FAIL`** for headline clone **`cfg_0015`**. **`--mode overlay` did not run.** **Combiner production code was not changed.**

---

## 1. Git / validation

- **Branch:** `main` (verify after push).
- **Checks:** `python -m compileall -q src` — OK; `python -m pytest -q` — **496+** tests (see `NEXT_HANDOFF.md` §B after this cycle).
- **Artifact validation:** `python -m src.research.validate_research_artifacts --root src/research/results/exit_overlay_diagnostics_v2 --csv-only --output .../exit_overlay_diagnostics_v2_artifact_validation.csv`.
- **Tracked-heavy:** no tracked `trade_context_panel.csv`, parquet, `overlay_trade_results_v2.csv`, `alignment_trade_detail.csv`, etc.

---

## 2. Why max_hold refinement was needed

Prior failure narrative focused on **terminal-bar** ordering (**max_hold** vs intrabar **stop/target**). Research needed explicit **`max_hold_priority`** modes plus row-level **exit bar index** to test that hypothesis on the **real** 10,628-row panel.

---

## 3. Previous full-panel failure recap

- **`cfg_0015`:** low mean/median |ΔR|, but **`total_r_diff` ≈ +52.4R** → **`ALIGNMENT_FAIL`**.
- **5188** panel rows **`exit_reason=max_hold`**; **476** rows where replay hits **`stop`**/**`target`** first (mass of signed R drift).

---

## 4. Combiner max_hold semantics audit

- **Source:** `src/combiner/simulator.py` (numba path ~423–460; Python mirror ~972–1009).
- **Per bar (long):** **stop/target from OHLC first**; if both, **stop wins**; **only then** `max_hold` via **`bars_held = i - entry_idx + 1`** vs `max_hold_m`, exit at **close** with slip; then EOD / session / end-of-data.
- **Terminal bar:** **max_hold does not run before** intrabar stop/target on that bar.
- **Curated write-up:** `max_hold_alignment_v1/combiner_max_hold_semantics.{md,csv}`.

---

## 5. Max_hold drift diagnostics (cfg_0015)

- **476 / 5188** mismatches: replay **`stop`** (200) or **`target`** (276).
- **All 476** have **`replay_exit_bar_index` < `panel_exit_idx`** — **pre-terminal** divergence (not same-bar terminal conflict).
- **Aggregates:** `max_hold_alignment_v1/max_hold_drift_overview.{csv,md}`, `max_hold_drift_by_{profile,window,candidate,context,bars_held}.csv`, `max_hold_drift_examples_sanitized.csv`.
- **Builder (local detail → aggregates):** `python -m src.research.build_max_hold_alignment_v1_aggregates` — reads **gitignored** `local_rows/alignment_trade_detail.csv`.

---

## 6. New max_hold priority modes (research-only)

| config_id | max_hold_priority | Headline |
|-----------|-------------------|----------|
| cfg_0015 | intrabar_first | Baseline best pick |
| cfg_0016_mh_forced | forced_first_on_terminal_bar | Slightly lower total_r_diff (~51.2R), still FAIL |
| cfg_0017_mh_panelauth | panel_exit_reason_authoritative | **Identical** to cfg_0015 on this panel (override only at `j==panel_exit_idx`) |
| cfg_0018_mh_skipconf | skip_terminal_bar_conflicts | **PASS** only by **excluding** mismatched rows — diagnostic, not economic |

- **Implementation:** `src/research/exit_overlay_alignment.py` (`CloneReplayConfig.max_hold_priority`, `combiner_clone_long_walk`), CLI **`--max-hold-priorities`** in `run_exit_overlay_diagnostics_v2.py`.
- **Detail columns:** `replay_exit_bar_index`, `bars_held_replay`, `panel_exit_reason`, `panel_exit_idx` (`SimResult.exit_bar_index` in `exit_overlay_sim.py`).

---

## 7. Alignment rerun result

- **Rows:** 10,628; **bars:** 617,160; **`synthetic_or_real=real`** (`alignment/full_panel_alignment_manifest.csv`).
- **Configs in grid:** **18** (`alignment/alignment_config_manifest.csv`).
- **Best economic pick (pick_best_config):** still **`cfg_0015`** / **`ALIGNMENT_FAIL`** (`alignment_grid_results.csv`, `alignment_best_config.yaml`).

---

## 8. Overlay gate decision

- **`OVERLAY_BLOCKED_ALIGNMENT_FAIL`** (and blocked as **non-economic** if only skip-mode PASS).
- **File:** `max_hold_alignment_v1/overlay_gate_after_max_hold_alignment.{md,csv}`.

---

## 9. Overlay result if run

- **Not run.**

---

## 10. If overlay did not run — exact reason

- Headline alignment **FAIL**; **`skip_terminal_bar_conflicts`** PASS is **not** an acceptable economic clone baseline.

---

## 11. Combiner bug assessment

- **No proven production bug** from alignment alone.
- **Pattern:** panel **`max_hold`** at `exit_idx` vs replay **stop/target** on **strictly earlier** bar indices → needs **trace / materialization** audit (entry bar, stop/target, session alignment), not only terminal ordering.
- **File:** `max_hold_alignment_v1/combiner_bug_assessment.{md,csv}`.

---

## 12. Exit vs router/quality status

- Router/quality remains the **actionable selection** path until an **economic** clone alignment passes and overlay reruns (`comparison_not_run_reason.md`).

---

## 13. Scalp / short status

- **Deferred** — see `scalp_short_after_exit_overlay_v2.{md,csv}` if present.

---

## 14. Decision

**`REFINE_REPLAY_ALIGNMENT`**

---

## 15. Explicit non-runs

- No WFO / live / SPY / broad L2 / Global L1.
- No production router / exit-management integration.
- No strategy / feature / selected-candidate YAML edits.
- No production combiner semantics change in this task.
- No row-level committed artifacts.

---

## 16. Recommended next step

Audit **pre-terminal** materialization for the **476** rows (entry index, stop/target vs bars, `panel_exit_idx` cap, session join), then adjust **research-only** replay only if justified; rerun **`--mode alignment`**.

---

## 17. Comparison table (configs)

See `max_hold_alignment_v1/max_hold_alignment_comparison.{csv,md}`.
