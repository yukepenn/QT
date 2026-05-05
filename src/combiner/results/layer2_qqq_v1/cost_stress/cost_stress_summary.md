# Cost stress — recovery placeholder

**Status:** `cost_stress_results.csv` is **not present** in this workspace copy (or was not committed). Any tables that appeared here previously are **not authoritative** until regenerated.

**Regenerate** after restoring `src/research/results/layer1_all10_qqq_v1/selected_candidates/*.yaml` and a full sweep folder with `results.csv`:

```bash
python src/combiner/postprocess.py ^
  --sweep-dir src/combiner/results/layer2_qqq_v1/sweep_<timestamp>_sweep_v1_full ^
  --output-root src/combiner/results/layer2_qqq_v1 ^
  --dedupe-top 50 ^
  --cost-stress-top 5 ^
  --candidate-root src/research/results/layer1_all10_qqq_v1/selected_candidates ^
  --config src/combiner/configs/layer2_qqq_v1.yaml ^
  --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30
```

Slippage grid: **0.005, 0.01, 0.02, 0.03**; commission **0.0**. Labels are written generically in `cost_stress_results.csv` (`cost_robustness_label`).
