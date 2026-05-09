# Layer 1 sweep manifest — tuned Batch 1 v1 (QQQ 2023–2024)

Tag: `layer1_v2_batch1_tuned_qqq_2023_2024_v1`

| strategy | raw_grid | result_rows (min_trades≥40) | notes |
|----------|----------|-------------------------------|--------|
| bollinger_squeeze_breakout | 1024 | 128 | `bollinger_squeeze_breakout_tuned_v1.yaml` |
| rsi_failure_swing | 768 | 120 | `rsi_failure_swing_tuned_v1.yaml` |

Candidate selection uses manifest mode with strict thresholds; relaxed fallback applies **per strategy** if strict yields zero rows (per `select_candidates.py`).
