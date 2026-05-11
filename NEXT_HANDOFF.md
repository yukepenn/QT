# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `4de1248` — Docs(handoff): record push for global L1 |
| New commit | After pull: **`git log -1 --oneline`** (message **Research(global-l2): document full sweep results** or similar) |
| Push status | Run **`git push`** after commit |
| Working tree | Clean except **untracked**: `src/strategies/testing_parameters_results/**`; `src/combiner/results/layer2_qqq_global_2023_2024_v2/sweep_20260511_005622/` (full sweep dir); `src/combiner/results/layer2_qqq_global_2023_2024_v2/sweep_full_console*.log`; `src/combiner/results/layer2_qqq_global_2023_2024_v2/cost_stress/feature_store_stats.json`; `src/combiner/results/layer2_qqq_global_2023_2024_v2/cost_stress/candidate_precompute_profile.csv`; heavy diagnostics JSON; `src/research/results/layer1_global_qqq_2023_2024_v2/run_console.log` |

## B. Task scope

| | |
|--|--|
| Requested | Full-window Global Layer 2 v2 combiner sweep (QQQ 2023–2024, l2_core), postprocess (cost stress + dedupe + behavior), curated summaries + indexes + handoff; **no** strategy edits / mini-WFO / full WFO / live / SPY |
| Completed | `combiner.sweep` **336** combos; `postprocess` (`dedupe-top 50`, `cost-stress-top 25`, `behavior-dedupe-top 30`, period breakdowns); curated **`layer2_global_full_*`** pack + standard **`top_unique`**, **`behavior_unique`**, **`cost_stress`**, **`cost_robust`** exports; **`RESULTS_INDEX`** ×2, **`PROJECT_STATUS`**, **`PROGRESS`**, **`CHANGES`** |
| Intentionally not done | Commit **`sweep_*`**, **`top_runs/`**, raw logs, **`feature_store_stats.json`**; mini-WFO; full WFO; live/paper; SPY; **`--use-signal-cache`** on first attempt failed (**WinError 5** `.cache` rename on OneDrive — rerun succeeded **without** cache flag) |

## C. Files changed

| Area | Paths |
|------|-------|
| Curated combiner results | `src/combiner/results/layer2_qqq_global_2023_2024_v2/layer2_global_full_summary.md`, `layer2_global_full_top_systems.csv`, `layer2_global_cost_stress_summary.csv`, `layer2_global_behavior_dedupe_summary.csv`, `top_unique_systems.{csv,md}`, `top_unique_run_map.csv`, `behavior_unique_systems.{csv,md}`, `behavior_unique_run_map.csv`, `cost_robust_systems.{csv,md}`, `cost_stress/cost_stress_{results.csv,summary.md}`, `cost_stress/candidate_precompute_profile_summary.{csv,md}` |
| Indexes / docs | `src/combiner/results/RESULTS_INDEX.md`, `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Local-only heavy | `sweep_20260511_005622/` (`results.csv`, `summary.md`, **`top_runs/`** with trades/equity/logs), `sweep_full_console*.log`, `cost_stress/candidate_precompute_profile.csv`, `cost_stress/feature_store_stats.json` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | **OK** (before commit) |
| `python -m src.strategies.loader --list` | **35** strategies |
| `pytest -q` | **374 passed** (before Layer 2 heavy run) |
| Postprocess | Exit **0**; dedupe **50** unique from **336** sweep rows; behavior **3** unique / **30** hashed |

## E. Layer 2 research results

| Metric | Value |
|--------|--------|
| Candidate YAMLs (l2_core root) | **66** |
| Sweep precompute universe | **34** candidates (union over grid sets) |
| Grid combinations | **336** completed |
| Best headline (`unique_rank` 1) | **`vwap_core`** — **VWAP_RECLAIM_REJECT_001** + **VWAP_TREND_PULLBACK_001** — **combiner_score ≈ 1.32**, **total_r ≈ 42.2**, **PF ≈ 1.21**, **337 trades**, **maxDD_r ≈ -10.5** (baseline slip **0.01**) |
| Cost stress (+0.02 slip) | **`robust_positive_at_0_02`** for top ranks (still **PF > 1**, **total_r > 0**); **+0.03** slip → **PF < 1** / **total_r < 0** for rank-1 profile |
| Behavior-unique (top 30 detail) | **3** (all **vwap** pair variants — cooldown / **max_trades_per_day**) |
| Multi-family note | **`indicator_completion_core`** reaches **unique_rank ~49–50** with **~43.5 total_r** but **combiner_score ~0.35** — not competitive vs VWAP headline |
| **Decision** | **`TUNE_LAYER2_COST_TURNOVER`** |

## F. Explicit non-runs

- mini-WFO, full WFO, live/paper, SPY  
- Strategy plugin changes  
- Committing **`sweep_*`**, **`top_runs/`**, **`testing_parameters_results/**`**, heavy diagnostics  

## G. Risks / caveats

- **In-sample** QQQ **2023–2024** only.  
- **Long-only** l2_core — **no** short/both validation.  
- **Headline winners are cost-sensitive** — PF collapses under **+0.03** incremental slip vs baseline **0.01**.  
- **Leaderboard duplication:** top dedupe rows repeat **vwap_core** grid knobs; true **behavior** diversity is limited.  
- **Signal cache on Windows/OneDrive** may hit **`PermissionError`** — use **no cache flag** or local cache root outside synced folders.

## H. Recommended next step

**Exactly one:** **`TUNE_LAYER2_COST_TURNOVER`** — tighten **`max_trades_per_day`**, cooldown/session rules, or stress ladder **before** Layer 3 smoke; optionally revisit combiner **objective weights** so multi-strategy buckets (`indicator_completion_core`) are not dominated only by **`combiner_score`** if economic **`total_r`** matters.
