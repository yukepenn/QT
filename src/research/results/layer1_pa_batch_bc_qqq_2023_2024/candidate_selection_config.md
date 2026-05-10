# Strict Layer 1 candidate selection — PA Batch B/C

Primary selection uses `src/research/select_candidates.py` in **manifest** mode (paths from `sweep_manifest.csv`). **Relaxed rows are not used** for primary `selected_candidates/`.

## Strict command (authoritative)

```bash
python src/research/select_candidates.py \
  --manifest src/research/results/layer1_pa_batch_bc_qqq_2023_2024/sweep_manifest.csv \
  --output-root src/research/results/layer1_pa_batch_bc_qqq_2023_2024 \
  --top-per-strategy 5 \
  --min-trades 30 \
  --min-profit-factor 1.05 \
  --min-total-r 0 \
  --max-drawdown-r -50 \
  --max-avg-bars-held 120 \
  --max-eod-count 0 \
  --max-end-of-data-count 0
```

## Outcome

- **5** YAMLs written, all **`pa_buy_sell_close_trend`** (`PA_BUY_SELL_CLOSE_TREND_001` … `005`).
- All other strategies: **no rows** passing strict filters (see `candidate_summary.md` and `no_candidate_strategies.txt`).
