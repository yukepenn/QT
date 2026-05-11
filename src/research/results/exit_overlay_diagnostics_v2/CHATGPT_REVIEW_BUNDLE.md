# CHATGPT_REVIEW_BUNDLE — exit_overlay_diagnostics_v2

## 1. Git / validation

After clone: `python -m compileall -q src`, `python -m pytest -q`, `python src/strategies/loader.py --list`, `python -m src.research.validate_research_artifacts --root src/research/results/exit_overlay_diagnostics_v2 --csv-only --output .../exit_overlay_diagnostics_v2_artifact_validation.csv`.

## 2. Why V2 was needed

V1 `fixed_target_replay` ignored combiner **exit slip** and other fill conventions → large mean abs ΔR vs panel.

## 3. Champion v0 freeze

Unchanged — see v1 bundle / `baseline_inventory.md`.

## 4. V1 replay drift recap

Mean abs diff ~0.28–0.38R (profile×window); overlays were diagnostic only.

## 5. Combiner semantics inventory

See `combiner_semantics_inventory.md` + `.csv`.

## 6. Alignment grid result

See `alignment/alignment_grid_results.csv` (15 curated configs + metrics on synthetic row / full run when executed locally).

## 7. Best clone replay config

`alignment/alignment_best_config.yaml` — **currently `cfg_0005` on synthetic one-row grid**; full panel may favor **`cfg_0001`**.

## 8. Alignment pass/fail

See `alignment/alignment_decision.md` — synthetic row **`ALIGNMENT_FAIL`** → gate **`REFINE_REPLAY_ALIGNMENT`**.

## 9. V2 overlay set

`baseline_original`, `combiner_clone_replay`, `max_hold_tighten_60`, `trend_swing_2R_contextual`, `runner_after_1R_trail_vwap_contextual`, `runner_after_1R_trail_atr_contextual`, `no_followthrough_exit_5bars_contextual`.

## 10–13. Context / weak / ambiguity

See `overlay_v2/trend_swing_v2_context_results.csv`, `runner_v2_context_results.csv`, `no_followthrough_v2_context_results.csv`, `max_hold_v2_context_results.csv`, `overlay_v2_ambiguity_sensitivity.csv`, `overlay_v2_weak_period_results.csv`.

## 14. Ambiguity sensitivity

`stop_first` (headline clone), plus `target_first` / `skip_ambiguous` on overlays in runner.

## 15–16. Context + weak periods

`context_specific_overlay_v2.csv` + `.md`.

## 17. Exit vs router/quality v2

See `exit_vs_router_quality_v2_comparison.md` — router/quality remains primary **selection** evidence until aligned exit replay stabilizes.

## 18. Scalp / short roadmap

See `scalp_short_after_exit_overlay_v2.md`.

## 19. Decision

**`REFINE_REPLAY_ALIGNMENT`** — see `exit_overlay_diagnostics_v2_decision.md`.

## 20. Explicit non-runs

No WFO/live/SPY/broad L2/Global L1; no production router/exit-management; no strategy/feature/YAML edits; no row-level commits.

## 21. Recommended next step

Run full-panel **`--mode alignment`**, then **`--mode overlay`** if alignment passes.
