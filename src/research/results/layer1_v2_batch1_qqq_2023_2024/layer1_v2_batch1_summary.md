# Layer 1 — Strategy Library v2 Batch 1 (QQQ 2023–2024, partial)

This folder contains a **partial** Layer 1 export for Batch 1:

- Source sweep: `rsi_failure_swing` capped run (`--max-combos 150`) on **2023-01-01 → 2024-12-31** with tag `layer1_v2_batch1_qqq_2023_2024` under `src/strategies/testing_parameters_results/`.
- Selection: `select_candidates.py` with `min_trades=25`, `min_profit_factor=1.02`, `min_total_r=-5`, `max_drawdown_r=-60`, `top_per_strategy=5`.

Other Batch 1 strategies were **not** swept to completion in this commit; re-run `sweep.py` + `select_candidates.py` with the same tag convention when ready.
