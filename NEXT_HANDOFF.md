# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `d359306` — Docs(handoff): link follow-up commit |
| New commit | `ea2e77a` — Research(global-l2): tune cost turnover diagnostics |
| Follow-up | Docs/CHANGES commits after `ea2e77a` — see `git log ea2e77a..HEAD --oneline` |
| Push status | **Pushed** `main` → `origin` (verify tip with `git log -1 --oneline`) |
| Working tree | Clean for tracked files; **untracked local-only:** `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/**` (`sweep_*`, `top_runs/`, full `cost_stress/`, etc.); other pre-existing untracked heavy paths under Global L2 v1 folder per prior handoff |
| Expected untracked local-only heavy artifacts | Tuned diagnostic sweeps under `layer2_qqq_global_2023_2024_v2_cost_turnover/`; do **not** `git add` these |

## B. Task scope

| | |
|--|--|
| Requested | Tune / diagnose Global L2 **cost, turnover, session constraints, objective** after full-window v2; no new strategies/features; no mini-WFO |
| Completed | `analyze_layer2_cost_turnover` + `build_layer2_tuned_comparison`; tuned YAMLs (72+64+80 combos); preflight + design + gate docs; **216** combos **run local-only** + postprocess exit **0** each |
| Intentionally not done | Commit `sweep_*` / `top_runs/` / heavy `cost_stress` dumps; mini-WFO; full WFO; live; SPY; `--use-signal-cache` on OneDrive |

## C. Files changed

| Area | Paths |
|------|--------|
| Scripts | `src/combiner/analyze_layer2_cost_turnover.py`, `src/combiner/build_layer2_tuned_comparison.py` |
| Tests | `tests/test_analyze_layer2_cost_turnover.py` |
| Configs | `src/combiner/configs/layer2_qqq_global_2023_2024_v2_cost_turnover.yaml`, `layer2_sweep_qqq_global_2023_2024_v2_lower_turnover_vwap.yaml`, `layer2_sweep_qqq_global_2023_2024_v2_family_diverse.yaml`, `layer2_sweep_qqq_global_2023_2024_v2_non_vwap.yaml`, `CONFIG_INDEX.md` |
| Curated results / docs | `src/combiner/results/layer2_qqq_global_2023_2024_v2/layer2_cost_turnover_diagnostic_summary.md`, `layer2_score_decomposition.csv`, `layer2_cost_adjusted_ranking.csv`, `layer2_family_dominance_summary.csv`, `layer2_turnover_summary.csv`, `layer2_cost_turnover_tuning_design.md`, `layer2_tuned_preflight.md`, `layer2_cost_turnover_tuned_comparison.{md,csv}`, `layer2_cost_turnover_gate_decision.md` |
| Indexes / project docs | `src/combiner/results/RESULTS_INDEX.md`, `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Local-only heavy | `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/**` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m src.strategies.loader --list` | **35** strategies |
| `pytest -q` | **379** passed |
| New tests | `tests/test_analyze_layer2_cost_turnover.py` |
| Postprocess (each tuned track) | Exit **0** |
| Tracked-heavy check | No matches for forbidden patterns in **tracked** files (run `git ls-files \| Select-String …` before commit) |

## E. Research results

- **Original Global L2 baseline (rank-1 unique):** `vwap_core` — VWAP_RECLAIM_REJECT_001 + VWAP_TREND_PULLBACK_001 — **total_r ~42.2**, **PF ~1.21**, **337** trades, **maxDD ~−10.5R** @ slip **0.01**; **+0.02** still positive; **+0.03** **negative** R / **PF < 1**.
- **Tuned tracks run:** A **72**, B **64**, D **80** (see `layer2_cost_turnover_tuned_comparison.md` for sweep folder names).
- **Best lower_turnover_vwap (combiner rank-1):** same VWAP pair, **294** trades, **total_r ~36.7**, **maxDD ~−15.5R**; **+0.02** still positive; **+0.03** still fails.
- **Best family_diverse / non_vwap:** **indicator_completion_core** five-pack — **total_r ~43.5**, **502** trades; **+0.02** positive; **+0.03** still **negative** total_r (PF ~**1.05**).
- **Cost-adjusted / decomposition:** see `layer2_cost_adjusted_ranking.csv`, `layer2_score_decomposition.csv`; VWAP dominance explained by production **`combiner_score`** weights vs multi-strategy **max_hold / DD / bars-held** penalties (documented in `layer2_cost_turnover_diagnostic_summary.md`).
- **indicator_completion_core:** still **economically higher total_r** than VWAP headline but **low combiner_score**; under stress, **slightly less awful PF @ 0.03** than VWAP but **not** viable on **total_r**.
- **Gate decision:** **`TUNE_LAYER2_COST_TURNOVER_AGAIN`** (`layer2_cost_turnover_gate_decision.md`).

## F. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; strategy additions; feature primitives; selected YAML edits; heavy artifact commits; `git add .`

## G. Risks / caveats

In-sample QQQ **2023–2024** only; long-only l2_core; no short/both validation; slippage ladder is incremental vs **0.01** baseline; OneDrive + signal cache (**WinError 5**) — runs used **no** `--use-signal-cache`; VWAP remains the **combiner** leader; non-VWAP economics are **indicator**-heavy and **high-turnover**.

## H. Recommended next step

**Exactly one:** **`TUNE_LAYER2_COST_TURNOVER_AGAIN`**
