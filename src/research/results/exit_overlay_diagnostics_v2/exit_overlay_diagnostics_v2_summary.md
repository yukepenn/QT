# exit_overlay_diagnostics_v2_summary

- **Harness:** `run_exit_overlay_diagnostics_v2.py` — `alignment` (grid vs panel `r_multiple`) and `overlay` (overlays vs **combiner_clone** headline).
- **Clone:** `exit_overlay_alignment.py` — `combiner_clone_long_walk` mirrors long-side fill/slip, `stop_first` default, max-hold 120, EOD 389.
- **Curated CSV note:** `overlay_v2/*.csv` and `alignment/*.csv` include **synthetic smoke** rows for schema/validation; **re-run locally** on the full panel for economics.
- **Decision:** `exit_overlay_diagnostics_v2_decision.md` → **`REFINE_REPLAY_ALIGNMENT`** until full-panel alignment passes.
