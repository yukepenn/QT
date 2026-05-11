# Global Layer 2 v2 — full-window evaluation (QQQ 2023–2024)

## 1. Run metadata

| Field | Value |
|--------|--------|
| Git commit (documentation / curated exports) | Run `git rev-parse HEAD` after pull |
| Sweep config | `src/combiner/configs/layer2_sweep_qqq_global_2023_2024_v2.yaml` |
| Base combiner config | `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml` |
| Candidate root | `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates` (**66** YAMLs) |
| Precompute universe (sweep) | **34** candidates (union of enabled strategies across all `candidate_set` × `top_per_strategy` combinations — see `run_global_layer1` / combiner logs) |
| Date window | **2023-01-01** → **2024-12-31** |
| Symbol | **QQQ** (`--asset equity`) |
| Combinations | **336** completed (`7 × 2 × 2 × 3 × 2 × 2` grid — no `long_short_mixed` bucket) |
| Sweep output dir (local) | `src/combiner/results/layer2_qqq_global_2023_2024_v2/sweep_20260511_005622/` — **not committed** (contains `top_runs/`, large CSVs) |
| Engine | Numba combiner path (`simulate_combiner_numba`) |
| Detail reruns | `--detail-top 30` (writes heavy `top_runs/` — **do not commit**) |
| Signal cache | First attempt with `--use-signal-cache` failed on this machine (`PermissionError` renaming `.cache` staging — typical OneDrive/Windows locking). **Successful run omitted** `--use-signal-cache`. |

## 2. Executive answers

1. **Basic performance gates** — **Yes, weakly.** The top deduped systems are profitable in-sample on baseline execution (**slippage 0.01**, commission 0): best cluster **`vwap_core`** with **VWAP_RECLAIM_REJECT_001** + **VWAP_TREND_PULLBACK_001** scores **combiner_score ≈ 1.32**, **total_r ≈ 42**, **PF ≈ 1.21**, **337 trades**.

2. **Cost / slippage stress** — **Mixed.** At **0.02** slip, top rows remain **`robust_positive_at_0_02`** (positive **total_r**, **PF > 1**). At **0.03** slip, **PF falls below 1.0** and **total_r** goes **negative** for the representative **unique_rank 1** profile — edge is **not** robust to an extra **+0.02** incremental slip vs baseline.

3. **Behavior uniqueness** — Among **30** config-unique rows taken for behavior hashing: **3** behavior-unique systems. All three are still the **same VWAP pair**, differentiated mainly by **`max_trades_per_day`** (1 vs 2) and **loss cooldown** (0 vs 15 min). **No** second independent *family* appears in the behavior-unique top set.

4. **Turnover / concentration** — Headline **`vwap_core`** systems run **~337 trades** over **~294** active session-days (**avg_daily_trade_count ~1.15**, **max_daily_trade_count = 2**). **avg_bars_held ~7.5** bars. **worst_day_r** on the rank-1 behavior row about **-2.1 R** (see `behavior_unique_systems.csv`). This is **moderate-high** activity for a 2-year window and **cost-sensitive**.

5. **Gate decision** — **`TUNE_LAYER2_COST_TURNOVER`** — tighten execution assumptions (slippage ladder), router/system caps (**max_trades_per_day**, cooldown), or candidate-set design **before** treating Layer 3 smoke as decisive. Alternative buckets (**`indicator_completion_core`**) show competitive **total_r** but **much lower combiner_score** (~0.35 vs ~1.32 for VWAP), so the sweep objective **overweights** the VWAP pair today.

## 3. Supporting artifacts (curated / committed pattern)

| Purpose | Path |
|---------|------|
| Deduped grid leaders | `top_unique_systems.{csv,md}`, `top_unique_run_map.csv` |
| Behavior dedupe | `behavior_unique_systems.{csv,md}`, `behavior_unique_run_map.csv` |
| Cost stress detail | `cost_stress/cost_stress_{results.csv,summary.md}`, `cost_robust_systems.{csv,md}` |
| This evaluation pack | `layer2_global_full_summary.md`, `layer2_global_full_top_systems.csv`, `layer2_global_cost_stress_summary.csv`, `layer2_global_behavior_dedupe_summary.csv` |

## 4. Short / both

**None.** l2_core remains **long-only** candidates; winning systems use **vwap_reclaim_reject** + **vwap_trend_pullback** only.

## 5. Explicit non-claims

- **In-sample QQQ 2023–2024 only** — not live-ready.
- **No mini-WFO / full WFO / live / paper / SPY** in this task.
- Heavy sweep trees, console logs, and `feature_store_stats.json` remain **local / untracked** per `docs/ARTIFACT_POLICY.md`.
