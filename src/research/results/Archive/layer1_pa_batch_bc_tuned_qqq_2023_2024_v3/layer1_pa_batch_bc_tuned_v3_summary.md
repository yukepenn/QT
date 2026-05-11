# PA Batch B/C — tuned v3 Layer 1 summary (QQQ 2023–2024)

## 1. Purpose

Address **candidate signal diversity** and **cost/hold** concerns raised by **Layer 2 v2** (`TUNE_PA_BATCH_BC_GRIDS_AGAIN`) without adding strategies or engine changes.

## 2. Why v2 Layer 2 failed

See `pa_batch_bc_tuned_v3_plan.md` and `src/combiner/results/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/layer2_pa_batch_bc_tuned_v2_summary.md`: **behavior dedupe collapsed**, climax strict exports were **`pure_signal_hash` clones**.

## 3. Candidate diversity diagnostic (v2 baseline)

Root: `pa_batch_bc_candidate_signal_diversity_v2/`

- Confirmed **climax 5× identical** `pure_signal_hash` and **close-trend** split into **2** hash groups (3+2).

## 4. v3 YAML design

- `src/strategies/testing_parameters/pa_buy_sell_close_trend_tuned_v3.yaml` — raw **1152** (entry/body/trend/VWAP-side/target_r/max_hold).
- `src/strategies/testing_parameters/pa_climax_reversal_tuned_v3.yaml` — raw **1152** (signal-first axes + stop/target/hold secondary).

Grid sizing: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/grid_review.{csv,md}`.

## 5. Gate preflight

`pa_batch_bc_gate_diagnostics_v3_preflight/` — both strategies **nonzero** `final_valid_signals` on first combo (`pre_sweep_gate_decision.md`).

## 6. Sweep results

Manifest: `sweep_manifest.csv` / `sweep_manifest.md`.

| strategy | status | raw_grid | result_rows | best PF | best total_r | best trades |
|----------|--------|----------|-------------|---------|--------------|---------------|
| `pa_buy_sell_close_trend` | ok | 1152 | 1152 | 1.260 | 41.56 | 461 |
| `pa_climax_reversal` | ok | 1152 | 1152 | 1.358 | 5.91 | 50 |

Heavy sweep trees live under `src/strategies/testing_parameters_results/**/sweep_*` (gitignored).

## 7. Strict candidate selection

`selected_candidates.csv` + **10** YAMLs (**5+5**), `candidate_summary.md`, `candidate_selection_config.md`, `summary.txt`, `no_candidate_strategies.txt` (Batch B/C plugins **not** swept here).

## 8. Candidate diversity (v3)

Root: `pa_batch_bc_candidate_signal_diversity_v3/`

`strategy_diversity_summary.csv`:

- `pa_buy_sell_close_trend`: **2** unique `pure_signal_hash` among 5.
- `pa_climax_reversal`: **1** unique `pure_signal_hash` among 5 (**unchanged structural problem**).

`select_diverse_candidates.py` export (duplicate-fill aware): `selected_candidates_diverse/` (same 10 IDs; documented warnings in `diversity_selection_summary.md` / `duplicate_fill_warning.txt`).

## 9. Exit / cost diagnostics

`pa_batch_bc_exit_diagnostics_v3/` — see `pa_batch_bc_exit_diagnostics_v3.md` + CSV.

## 10. Comparison v2 vs v3

- **Close-trend:** v3 strict set probes **lower trade count** configs vs v2 rank-1 row; **0.02** stress remains **positive** on exported rows.
- **Climax:** still **one** discrete signal path in the strict top five; economics moved vs v2 row but **diversity gate unmet**.

## 11. Decision

### **TUNE_PA_BATCH_BC_GRIDS_AGAIN**

Rationale:

1. **Climax strict top five still share one `pure_signal_hash`** — fails the v3 readiness test for a reduced Layer 2 pass focused on **independent** paths.
2. **`selected_candidates_diverse` does not create new hashes** (same YAMLs).
3. Exit table shows **climax remains low-n**; research priority should return to **grid axes that actually move the boolean mask** (or accept **≤1** export row for climax).

### Layer 2 v3

**Not run** (decision ≠ `PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_V3`).

## 12. Explicit non-runs

- **Reduced Layer 2 v3:** not executed.
- **mini-WFO / full WFO / live:** not executed.
