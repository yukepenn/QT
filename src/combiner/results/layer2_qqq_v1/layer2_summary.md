# Layer 2 Combiner v1 — summary (recovery / closeout template)

**Recovery note (2026):** This workspace copy may be **incomplete**. See `src/research/results/recovery_status_before.md`. In particular, **`selected_candidates/*.yaml`** must exist (~40 files) before any combiner diagnostics, sweep, fixed runs, or cost stress can be reproduced. **Do not treat missing CSV metrics as validated** until regenerated.

**Sample design:** QQQ equity, **2025-01-01 → 2026-04-30**, Layer 1 library path  
`src/research/results/layer1_all10_qqq_v1/selected_candidates/`.  
All results are **in-sample**; **Layer 3** (holdout) remains deferred.

---

## 1. Executive summary

- Layer 2 v1 architecture: **one signal precompute** per run/sweep, **Numba** `simulate_combiner_numba`, **`enabled_mask`** per combo, **no** per-combo signal regeneration in the sweep inner loop.
- Intended full grid: **1620** combos (`layer2_sweep_qqq_v1.yaml`: 6×3×5×3×3×2).
- **Headline metrics** (from last known good closeout, **not** re-verified on this disk): best family **`trap_family`**, **`top_per_strategy=1`**, three candidates (failed ORB + gap acceptance failure + prior-day level trap variants), order ~**323** trades, **~69 R**, **PF ~1.52**, **max_dd_r ~−12**, **combiner_score ~1.41**. **Replace this bullet** with rows read from `top_unique_systems.csv` once restored.

---

## 2. Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Diagnostics CSVs | `diagnostics/candidate_signal_summary.csv` (and overlap/conflict) | Regenerate if missing |
| Diagnostics narrative | `diagnostics/diagnostics_summary.md` | `postprocess.py --diagnostics-dir` |
| Full sweep | `sweep_*_sweep_v1_full/results.csv` | Regenerate if missing |
| Fixed rollup | `fixed_run_summary.csv`, `fixed_run_summary.md` | After seven `run.py --detailed` + `--collect-fixed-runs` |
| Deduped tops | `top_unique_systems.csv`, `.md`, `top_unique_run_map.csv` | `postprocess.py --dedupe-top` |
| Cost stress | `cost_stress/cost_stress_results.csv`, `cost_stress_summary.md` | `postprocess.py --cost-stress-top` |

---

## 3. Architecture verification

- **Precompute once** + **enabled_mask** + **Numba** path: implemented in `candidate.py`, `sweep.py`, `run.py`, `simulator.py`.
- **Raw parquet** and **`src/data`**: must remain untouched by combiner work.
- **`src/backtest/fast.py`**, **`src/backtest/sweep.py`**: no combiner-specific or strategy-family branches (verify periodically).
- **`postprocess.py`**: generic only; dedupe key = `candidate_set`, `top_per_strategy`, `max_trades_per_day`, `daily_max_loss_r`, `cooldown_after_loss_minutes`, `priority_policy`, `candidate_ids_json`.

---

## 4. Candidate diagnostics

After full-period diagnostics run: report **candidate count**, **total signals**, **by strategy/family**, **zero-signal** IDs, **top overlap/conflict pairs** (see `diagnostics_summary.md`). No strategy tuning in this phase.

---

## 5. Fixed runs

Seven tagged detailed runs (strict_core top1/top3, opening_family, trap_family, vwap_control, all_strict, all_with_relaxed) should be summarized in `fixed_run_summary.csv`. Compare **strict_core vs opening_family**, **trap_family** vs sweep winner config, **vwap_control** contribution, **all_with_relaxed** vs narrow sets.

---

## 6. Full sweep

- **1620** rows expected in `results.csv`.
- Slice winners by `candidate_set`, `max_trades_per_day`, `daily_max_loss_r`, `cooldown_after_loss_minutes`, `priority_policy` using sorted `combiner_score`.

---

## 7. Top unique systems

- `postprocess.py` dedupes **configuration** duplicates (not only metric ties).
- Map detailed folders via `top_unique_run_map.csv` (**combo_id** match to `top_runs/rank_*/summary.txt` when sweep detail exists).

---

## 8. Cost stress

- Slippage: **0.005, 0.01, 0.02, 0.03**; commission **0.0**.
- Labels in results CSV: **`robust_positive_at_0_03`**, **`robust_positive_at_0_02`**, **`positive_but_sensitive`**, **`cost_fragile`** (see `cost_robustness_label` column).

---

## 9. Rejection-count interpretation

1. **`existing_position`**: can count **multiple** signal events per episode while flat is false — congestion diagnostic, not “missed trade” count.
2. **Daily limits / cooldown / max trades**: fast path may **not** log every blocked bar; rejection totals can **under-count** blocked **events** in metrics mode.
3. **`lower_priority_conflict`**: eligible same-bar non-winners — useful conflict signal.

---

## 10. Research interpretation (qualitative)

- Narrow **trap-aligned** sets often score well when they avoid overcrowded `top_per_strategy=3` pools.
- **Breadth** (`all_with_relaxed`) can add **trades/R** but may lower **combiner_score** via drawdown/penalties.
- **max_trades_per_day** and **loss/cooldown** grids often **tie** at the top; primary driver is usually **candidate_set** + **top_per_strategy**.

---

## 11. Recommended next step

1. Restore **Layer 1 YAML** library and optional manifest.  
2. Rerun missing Layer 2 steps **only as needed** (see `recovery_status_before.md`).  
3. **Freeze 1–3** combiner configs for future **Layer 3** holdout — **do not** re-optimize on the same window.

---

## 12. Recovery commands (checklist)

```bash
# Diagnostics
python src/combiner/run.py --candidate-root src/research/results/layer1_all10_qqq_v1/selected_candidates --config src/combiner/configs/layer2_qqq_v1.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set all_with_relaxed --top-per-strategy 5 --diagnostics-only --output-root src/combiner/results/layer2_qqq_v1

python src/combiner/postprocess.py --diagnostics-dir src/combiner/results/layer2_qqq_v1/diagnostics --diagnostics-date-range "2025-01-01 — 2026-04-30" --output-root src/combiner/results/layer2_qqq_v1

# Sweep (if no results.csv)
python src/combiner/sweep.py --candidate-root src/research/results/layer1_all10_qqq_v1/selected_candidates --config src/combiner/configs/layer2_sweep_qqq_v1.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --output-root src/combiner/results/layer2_qqq_v1 --top 20 --detail-top 10 --progress-every 200 --tag sweep_v1_full

# Dedupe + cost stress (set SWEEP to actual folder)
python src/combiner/postprocess.py --sweep-dir %SWEEP% --output-root src/combiner/results/layer2_qqq_v1 --dedupe-top 50 --cost-stress-top 5 --candidate-root src/research/results/layer1_all10_qqq_v1/selected_candidates --config src/combiner/configs/layer2_qqq_v1.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30
```
