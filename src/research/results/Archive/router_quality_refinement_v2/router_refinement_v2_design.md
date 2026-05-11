# router_refinement_v2_design (offline diagnostic only)

## Principles

- v1 offline filters were **too aggressive** for default combined (`preferred_or_neutral_only` ~19% retention in v1 table).
- v2 emphasizes **soft removal**, **context-targeted guards**, and **explicit non-blocking** behavior for `unknown_mixed`.
- `late_climax` / `high_chop` remain **diagnostic contexts** — no production “hard router” in combiner.

## Variants (implemented masks)

| variant | intent | retention target | primary columns |
|---------|--------|------------------|-----------------|
| `baseline_all` | control | ~100% | — |
| `soft_avoid_removed` | remove only `trend_short_diagnostic` | ~99.9% | `context_bucket` |
| `soft_downweight_proxy` | drop rare avoid + weaker half of `late_climax` by score | ~65–75% | `context_bucket`, `quality_score_v2` |
| `gap_context_guard` | remove GAP in `late_oow` + `unknown_mixed` only | ~95–99% | `candidate_id`, `window`, `context_bucket` |
| `late_climax_guard` | remove PA trend-chase tail in `late_climax` | ~80–90% | `candidate_id`, `context_bucket`, `decision_pa_late_trend_score_20` |
| `high_chop_guard` | placeholder (no `high_chop` rows in current panel) | ~100% | `context_bucket` |
| `repeat_after_loss_guard` | remove same-family repeats after a loss | varies | `entry_prior_trade_was_loss`, `entry_prior_trade_same_family` |
| `combined_light_guard` | AND of soft avoid + gap guard + repeat guard | ~97–99% | combination |

## Pass / risk notes

- **Overfit risk:** any threshold derived on the same panel used for scoring (quality percentile / bottom-cut) is flagged `IN_SAMPLE_DIAGNOSTIC` in quality outputs.
- **Pass condition (promising heuristic):** retention ≥ 60%, PF or maxDD proxy improves without collapsing `pa_gap_mtp2_meta` total R vs baseline, and without large weak-period deterioration.

See `router_refinement_v2_design.csv` for per-variant design table and `router_v2_config_draft.yaml` for a draft offline config (`enabled: false`).
