# PA Batch B/C — repaired Layer 2 v3 behavior & cost completion

Window: QQQ **2023-01-01 → 2024-12-31**. Candidate root: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/selected_candidates_repaired/selected_candidates`.

## 1. Why this rerun was necessary

The first repaired Layer 2 sweep used **`--detail-top 0`**, so **`top_runs/`** trade folders were not written. Postprocess therefore **skipped meaningful behavior dedupe** (no `trades.csv` to hash). The earlier summary still said **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN`**, which was **not** justified until behavior evidence existed.

This pass re-swept with **`--detail-top 15`** (local sweep dir **`sweep_20260510_221442/`**, not committed) and postprocessed with **`--write-behavior-unique`**, **`--dedupe-top 50`**, **`--behavior-dedupe-top 30`**, **`--cost-stress-top 10`**, **`--write-period-breakdowns`**.

## 2. Behavior-unique results

| Metric | Value |
|--------|--------|
| Config rows considered (`--behavior-dedupe-top`) | **30** |
| Rows with `trades.csv` loaded | **15** |
| Rows missing matched `top_runs` | **15** |
| **Behavior-unique strong hashes** | **1** |
| Weak / low-quality hashes | **0** |

**Top behavior system (only row):** `pa_climax`, `top_per_strategy=1`, single **`PA_CLIMAX_REVERSAL_DIVERSE_001`**, **50** trades, **strong** `behavior_hash`, `total_r ≈ 5.91`, `profit_factor ≈ 1.358`, `profit_factor_r ≈ 1.203` (see `behavior_unique_systems.csv`).

**Close-trend vs climax vs core in behavior space**

- Among the **15** configs that produced trade logs in the behavior slice, **dedupe collapses to one** realized trade sequence (climax-only, one candidate ID).
- **`pa_close_trend`** and **`pa_batch_bc_core`** do **not** appear as separate behavior hashes in this slice — core diversity at the **trade-sequence** layer is **not** observed here (combiner dominance + missing `top_runs` for half the slice).

## 3. Cost stress (leading `unique_rank` 1 — `pa_climax` single-candidate)

Slippage ladder from `cost_stress/cost_stress_results.csv` / `cost_stress_summary.md` (same economics for `unique_rank` 1–10 in this run — all the same underlying 50-trade path):

| `slippage_per_share` | `total_r` | `profit_factor` | `max_drawdown_r` |
|----------------------|-----------|-----------------|------------------|
| **0.005** | **7.405** | **1.463** | **-6.149** |
| **0.010** | **5.910** | **1.358** | **-6.290** |
| **0.020** | **3.029** | **1.259** | **-6.550** |
| **0.030** | **-1.156** | **1.124** | **-10.278** |

- **0.02 gate:** `total_r > 0`, `profit_factor > 1.05` — **passes** for this path.
- **0.03:** `total_r` **negative** — does **not** hold at 0.03.

## 4. `cost_robust_systems` composition

With `--min-trades-cost-rank 30` and robust filters (`0.02` slip, `total_r > 0`, `profit_factor > 1.05`, `max_drawdown_r > -50`, median cost cap):

- **Matching rows: 10**, all **`candidate_set = pa_climax`**, all the same **`PA_CLIMAX_REVERSAL_DIVERSE_001`** economics (grid knob duplicates only).
- **No** `pa_close_trend` and **no** `pa_batch_bc_core` rows in that table for this postprocess pass → **single-family cost survival** in the robust slice.

## 5. Core vs single-family (sweep economics, not behavior hash)

From the regenerated **`rank_by_total_r.csv`** (local; gitignored pattern `rank_by_*.csv`):

- **Best `pa_batch_bc_core`:** combo **96**, `top_per_strategy=2`, **`total_r ≈ 48.66`**, **`profit_factor ≈ 1.245`**, **517** trades (dominated by close-trend fills + small climax share — see sweep `results.csv` row for combo 96).
- **Best `pa_close_trend`-only family (representative):** e.g. combo **30**, **`total_r ≈ 44.16`**, **`profit_factor ≈ 1.255`**, **476** trades.
- **Best `pa_climax`-only (combiner-score leader / unique slice):** combo **33** region, **50** trades, **`total_r ≈ 5.91`** at **0.01** slip baseline in cost table.

**Readout**

- **Core improves `total_r`** vs either single-family row on this grid (portfolio stacking).
- **Cost-stress / robust leaderboards** are still **climax-skewed** at the sampled `unique_rank` top and robust filter — risk of **single-family overclaim** if one freezes “the robust system” from `cost_robust_systems` alone.

## 6. Decision (exactly one)

### **B. `TUNE_PA_BATCH_BC_GRIDS_AGAIN`**

Rationale (maps to gate B):

1. **`behavior_unique = 1`** — does **not** satisfy the “≥ 2 strong hashes” branch, and there is **no** second non-degenerate behavior path in the completed slice.
2. **Half** of the behavior-dedupe rows lacked `top_runs`** — evidence is improved but still **incomplete**; even so, the **15** traced rows **collapse to one** hash.
3. **`cost_robust_systems`** is **100% `pa_climax` / one ID** — “only climax survives” the published robust filter in this configuration.
4. **Portfolio core** remains attractive on **`total_r`** but is **not** the object of the robust cost table — **do not** advance to mini-WFO design on **`PROCEED`** until behavior **and** cost gates align without single-family overclaim.

**Not chosen:** **A** (behavior + cost gate not met), **C** (clear tuning path: fix `top_runs` coverage / rebalance cost leaderboards / widen stress to core rows), **D** (no invalid hashes).

## 7. Explicit non-runs

- **mini-WFO**, **full WFO**, **live/paper** — not executed.

## 8. Optional local follow-ups (not committed here)

- Inspect **`behavior_unique_run_map.csv`** vs sweep `top_runs/` naming for the **15 missing** rows (tooling / rank mapping).
- Raise **`--cost-stress-top`** or add targeted postprocess for **`pa_batch_bc_core`** combos from `results.csv` / local `rank_by_total_r.csv`.
