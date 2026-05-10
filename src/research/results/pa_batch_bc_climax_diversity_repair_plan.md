# PA Batch B/C — climax diversity repair plan

## 1. Current blocker

Layer 1 **strict top-5** exports showed **`pure_signal_hash` collapse** for `pa_climax_reversal` (and partial collapse for close-trend), which **blocked reduced Layer 2 v3** even though sweep economics looked acceptable.

## 2. Evidence from v2 Layer 2

See `src/combiner/results/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/layer2_pa_batch_bc_tuned_v2_summary.md`: **`behavior_unique` ≈ 1**, combiner leaderboard skewed to compact climax rows; **0.02** cost stress marginal on the dominant path.

## 3. Evidence from v3 Layer 1

`layer1_pa_batch_bc_tuned_v3_summary.md` and `pa_batch_bc_candidate_signal_diversity_v3/strategy_diversity_summary.csv`: climax still **1 / 5** unique `pure_signal_hash` among strict YAML exports.

## 4. Hypotheses

| ID | Hypothesis |
|----|-------------|
| **H1** | **Selector problem:** diverse strict rows exist **deeper in the ranked sweep CSV**, but `select_candidates` only surfaces score-top rows that share one mask. |
| **H2** | **Axis problem:** strict region is large but **signal mask** ties many parameter cells together. |
| **H3** | **True limitation:** only one economically viable climax mask in-window (then **cap at one path**). |

## 5. Exact checks to run

1. `sweep_result_signal_diversity.py` on **v3** `results.csv` for both strategies: strict filters, **top 100** pool, report **unique `pure_signal_hash` counts** for heads **20 / 50 / 100**.
2. If **H1**: build **`selected_candidates_repaired`** from `unique_signal_hash_candidates_*.csv` + exporter.
3. Re-run **`candidate_signal_diversity.py`** on repaired root.
4. **`check_selected_candidates_fast_context.py`** smoke window.
5. If gates pass: **reduced Layer 2 repaired** (same grid shape as spec).

## 6. Conditional actions

- **If ≥2 unique climax hashes in strict top-100:** export **up to 3** diverse climax YAMLs; **no** strategy code change.
- **If exactly 1:** export **one** climax + `CLIMAX_CAPPED_ONE_PATH.md`; still allow Layer 2 if close-trend carries diversity (**decision doc**).
- **If H3 across full strict pool:** document and **DEFER** further PA B/C Layer 2 until a future v4 grid or optional default-preserving signal parameter (explicit separate phase).

## 7. Explicit non-runs

- **No** new strategy plugins, **no** new Brooks primitives, **no** backtest engine edits.
- **No** mini-WFO / full WFO / live.
- **No** PA Batch A, **no** `refined_failed_orb`, **no** relaxed diagnostic rows in core Layer 2.
