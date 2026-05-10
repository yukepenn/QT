# PA Batch B/C tuned v2 Layer 2 — diagnostics interpretation (QQQ 2023–2024)

## Signal mass by family

From `diagnostics/candidate_signal_summary.csv` (strict 10 YAMLs, `pa_batch_bc_core` selection):

- **`pa_buy_sell_close_trend`:** ~**461** long signals per ranked YAML (five candidates ≈ **2.3k** raw signals summed in precompute; aggregate long-only mass dominates the book).
- **`pa_climax_reversal`:** **51** signals per YAML (**255** summed) — an order of magnitude smaller than close-trend.

## Cross-family overlap

Overlap / conflict matrices (`candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`) show **substantial same-bar overlap potential** between the two families (close-trend bars are dense; climax bars are a subset of the session timeline). In the router, **`metadata_priority`** favors the higher-priority / higher-score candidate; with default priorities, **climax can win head-to-head** on bars where both fire.

## Within-family “duplicates”

All five **climax** YAMLs share the **same signal timestamps and counts** (51 each) — they are **parameter variants** with identical signal placement in this window. The five **close-trend** YAMLs differ slightly in counts (459–468) but are **highly redundant** intraday paths.

## Does `pa_climax` matter?

Yes, but **marginally in trade count**: fixed **core top1** shows **43** climax fills vs **426** close-trend fills (469 trades total). Climax contributes **~14.6 R** of **~48.6 R** in that portfolio (~30%). So climax **does** add R, but the **router + dedupe** story is still **close-trend-dominated**.

## Will close-trend dominate Layer 2 rankings?

**Sweep / `top_unique`:** rows sort by `combiner_score`; **`pa_climax` single-candidate sets score highest** (~+1.23) because they are compact, high-PF systems, while wide **close-trend** systems score **negative combiner_score** (~−2.7) under the same score formula despite large total_r. So **leaderboard ≠ economic dominance** — interpret alongside `total_r`, `profit_factor`, and cost stress.

## Implications

- Treat **multi-YAML same-strategy** rows as **grid diversity**, not independent behavior.
- Any **mini-WFO** design must assume **priority / overlap** will continue to throttle the weaker-frequency family unless grids or priorities are retuned.
