# exit_overlay_diagnostics_v2_summary

## What ran

- **Real** full-panel **alignment** on **10,628** rows (three Champion profiles × four windows) against local **QQQ** parquet under **`data/raw/ibkr`** (**617,160** bar rows; **0** missing sessions).
- **2026-05-11 refinement:** alignment grid expanded to **18** configs with research-only **`max_hold_priority`** modes; alignment **reran** and refreshed `alignment/*` + `bar_load_meta.csv`.
- **Aggregates:** `max_hold_alignment_v1/*` built via `python -m src.research.build_max_hold_alignment_v1_aggregates` (consumes local-only `local_rows/alignment_trade_detail.csv`).

## Result

- **Best headline config:** `cfg_0015` (`alignment_best_config.yaml`, `max_hold_priority=intrabar_first`).
- **Headline |ΔR|:** mean ≈ **0.035R**, median ≈ **0**, p90 ≈ **0**, max ≈ **1.85R** (`alignment_grid_results.csv`).
- **Total R:** replay − panel ≈ **+52.4R** → **`ALIGNMENT_FAIL`**.
- **Dominant drift:** **476 / 5188** panel **`max_hold`** rows where replay exits **`stop`/`target` first** — **all 476** exit on a bar index **before** `panel_exit_idx` (**pre-terminal**), not terminal-bar max_hold ordering (`max_hold_alignment_v1/max_hold_drift_overview.md`).
- **Modes:** `forced_first_on_terminal_bar` → ~**+51.2R** total drift; `panel_exit_reason_authoritative` **unchanged** vs `cfg_0015` on this panel; `skip_terminal_bar_conflicts` shows **PASS** only by **excluding** mismatches (diagnostic).

## What did not run

- **`--mode overlay`** — **skipped** (`overlay_gate_after_max_hold_alignment.md`).

## Decision

**`REFINE_REPLAY_ALIGNMENT`** — see `exit_overlay_diagnostics_v2_decision.md`.
