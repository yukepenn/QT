# exit_overlay_diagnostics_v2_summary

## What ran

- **Real** full-panel **alignment** on **10,628** rows (three Champion profiles × four windows) against local **QQQ** parquet under **`data/raw/ibkr`** (**617,160** bar rows; **0** missing sessions).
- **Synthetic** prior alignment CSVs were **archived** to `alignment/archive_synthetic_pre_full_panel/` before overwriting curated `alignment/` outputs.

## Result

- **Best config:** `cfg_0015` (`alignment_best_config.yaml`).
- **Headline |ΔR|:** mean ≈ **0.035R**, median ≈ **0**, p90 ≈ **0**, max ≈ **1.85R** (aggregate row in `alignment_grid_results.csv`).
- **Total R:** replay − panel ≈ **+52.4R** → **`ALIGNMENT_FAIL`** (exceeds PASS / PASS_WITH_WARNINGS `total_r_diff` gates).
- **Root cause (aggregate):** panel **`max_hold`** vs replay **`target`/`stop`** on a **476-row** subset; see `alignment/full_panel_alignment_failure_analysis.md` and CSVs.

## What did not run

- **`--mode overlay`** (contextual overlays, ambiguity sweep) — **skipped** because alignment did not pass gates.

## Decision

**`REFINE_REPLAY_ALIGNMENT`** — see `exit_overlay_diagnostics_v2_decision.md`.
