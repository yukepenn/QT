# Phase 0 — manifest inventory (trade quality router v1)

- **git tip (during work):** `4c77f4c` — Docs(handoff): avoid stale tip SHA in table (verify with `git log -1 --oneline` after final push).
- **Branch:** `main`.
- **Handoff decision (incoming):** post Global L2 cost/turnover **`TUNE_LAYER2_COST_TURNOVER_AGAIN`** (`NEXT_HANDOFF.md` before this task).
- **Result roots inspected:** `src/combiner/results/layer2_qqq_global_2023_2024_v2/`, `src/research/results/layer1_global_qqq_2023_2024_v2/`, local `src/research/results/trade_quality_router_v1/local_runs/` (gitignored / not committed).
- **Local-only sweep folders:** `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/**` (untracked heavy).
- **`top_runs/`:** present under cost_turnover root only locally; not committed.
- **`trades.csv`:** not in tracked tree; regenerated under `trade_quality_router_v1/local_runs/run_*` for this task only.
- **Curated Global L2 summaries present:** `layer2_cost_turnover_tuned_comparison.{csv,md}`, `layer2_global_full_summary.md`, etc. — **no mismatch** with handoff narrative.
- **Files mentioned in `NEXT_HANDOFF`:** all referenced curated paths exist locally in repo; heavy sweep dirs may be absent on a fresh clone (expected).
