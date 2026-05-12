# Baseline inventory — exit overlay on execution path

Captured **before** committing this task’s handoff (git tip matches `baseline_inventory.csv`).

- **Git tip:** `25a38bb` — *Research(combiner): run repo-local data parity*
- **Prior NEXT_HANDOFF decision:** `RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`
- **Readiness label:** `EXECUTION_BACKED_READY_FOR_RESEARCH` (see `combiner_adapter_parity/execution_backed_readiness.md`)
- **Repo-local bars:** `data/raw/ibkr` (QQQ 1m partitions; committed parquet only under this tree)
- **Candidate root (Champion / Archive Layer2 core):** `src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- **Champion IDs exercised:** `PA_BUY_SELL_CLOSE_TREND_003`, `GAP_ACCEPTANCE_FAILURE_001` (profiles `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`)
- **This task result root:** `src/research/results/exit_overlay_execution_path/`
- **Interrupted local outputs:** None required cleanup under the result root before the curated smoke + repo-coverage run (`_local_only/` is gitignored for precompute + replay rows).
