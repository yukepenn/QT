# trade_quality_score_design v2

Weights: regime_fit 30%, level 20%, signal 20%, cost_safety 15%, freshness 15% → **sum = 100%**.

## Buckets
- **A**: composite ≥ 75
- **B**: 55–75
- **C**: < 55

**Not implemented** in combiner in this task.
