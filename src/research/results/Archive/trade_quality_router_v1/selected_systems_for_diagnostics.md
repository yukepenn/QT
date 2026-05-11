# Selected systems for trade-quality diagnostics

Three systems only (evidence set A–C). Family-diverse row C matches **`indicator_completion_core`** with **`max_trades_per_day: 1`** (see `layer2_sweep_qqq_global_2023_2024_v2_family_diverse.yaml` grid); without `mtp=1`, the same five-pack produces ~1000 trades on QQQ 2023–2024 and **does not** match `layer2_cost_turnover_tuned_comparison.csv`.

| Label | Track | Config YAML | Regenerate trades |
|--------|--------|-------------|-------------------|
| `vwap_baseline_global_l2` | Original Global L2 VWAP pair | `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml` | `python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates --config src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set vwap_core --top-per-strategy 1 --output-root src/research/results/trade_quality_router_v1/local_runs --tag diag_vwap_baseline` |
| `vwap_lower_turnover` | Tuned lower-turnover VWAP | `layer2_diag_vwap_lower_turnover.yaml` (repo) | Same with `--config src/research/results/trade_quality_router_v1/layer2_diag_vwap_lower_turnover.yaml --tag diag_vwap_lower_turnover` |
| `indicator_completion_mtp1` | Indicator five-pack @ mtp=1 | `layer2_diag_indicator_mtp1.yaml` | Same with `--config .../layer2_diag_indicator_mtp1.yaml --candidate-set indicator_completion_core --tag diag_indicator_mtp1` |

Curated comparison metrics: `src/combiner/results/layer2_qqq_global_2023_2024_v2/layer2_cost_turnover_tuned_comparison.csv`.

**Do not commit** `local_runs/**` or `**/trades.csv`.
