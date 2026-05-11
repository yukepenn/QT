# exit_overlay_implications — router_quality_refinement_v2

## Questions answered (evidence-based)

| question | answer |
|----------|--------|
| Does router/quality refinement look promising enough to integrate first? | **Partially.** Several **offline** variants improve PF / maxDD proxy with ≥60% retention (notably `late_climax_guard`, percentile `top80`, `bottom_cut_20`), but tradeoffs remain (especially **`primary_mtp2_meta` total R`** sensitivity and **in-sample** quality thresholds). This is **not** sufficient to justify immediate combiner integration. |
| Or should next step be exit overlay diagnostics? | **Yes (recommended).** Exit readiness preview (`exit_mode_assignment_preview.csv`) already shows **`trend_swing`** and **`runner`** as strongest average R modes vs **`scalp`** negative in the heuristic preview. |
| Do `trend_swing` / `runner` remain promising? | **Yes**, per committed exit readiness aggregates in `local_detailed_trade_context_replay_v1/exit_overlay_readiness_v1/`. |
| Is scalp still low priority? | **Yes**, unless new **non-heuristic** simulations contradict the preview. |
| Which exit overlay to test first? | **1) `trend_swing`**, **2) `runner`**, then **`no_followthrough_exit`** / **`regime_degradation_exit`** as structured stress probes; **`scalp`** last. |
| What data is needed for exit overlay simulation? | Intraday **bar path** (OHLC + timestamps), existing **entry/exit idx**, and a deterministic assignment function from design tables — beyond what the row panel alone guarantees. |
| Can the local row panel support exit simulation? | **Partially:** it supports **labels / readiness / attribution**, but **full** exit-path simulation typically needs **bar-path replay** (or enriched intraday series), not only one row per trade. |

## CSV mirror

- `exit_overlay_implications.csv`
