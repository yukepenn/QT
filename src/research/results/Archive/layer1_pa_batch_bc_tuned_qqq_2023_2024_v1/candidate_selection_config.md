# Strict Layer 1 candidate selection — PA Batch B/C tuned v1

Selection uses `src/research/select_candidates.py` in **manifest** mode (paths from `sweep_manifest.csv`). **Relaxed thresholds are not used** for primary `selected_candidates/`.

## Strict command (authoritative)

```bash
python src/research/select_candidates.py \
  --manifest src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/sweep_manifest.csv \
  --output-root src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1 \
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

- Strict exported **5** YAMLs, all `pa_climax_reversal` (`PA_CLIMAX_REVERSAL_001` … `005`).
- See `candidate_summary.md` and `no_candidate_strategies.txt`.

