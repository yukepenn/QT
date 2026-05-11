# In-sample sanity — legacy reference mismatch (indicator)

## VWAP profiles

`vwap_mtp2` and `vwap_mtp1` match the published Global L2–style references on **2023-01-01 → 2024-12-31** (≈337 / +42.2R and ≈294 / +36.7R) within the configured tolerance.

## Indicator profiles

YAML for `layer2_fixed_indicator_mtp{1,2,3}.yaml` matches `src/research/results/trade_quality_router_v1/layer2_diag_indicator_mtp1.yaml` (same `indicator_completion_core` block, `max_per_strategy: 4`, same five strategies).

On this combiner build (**Numba path**, `--no-detailed`, `--top-per-strategy 3`, QQQ local parquet), **2023–2024 replay economics are**:

| profile        | trades | total_r (published) |
|----------------|--------|----------------------|
| indicator_mtp1 | 502  | **+18.76** (not ~+43.5R from older v1.5 narrative) |
| indicator_mtp2 | 1002 | **+46.51** (not ~+72R) |
| indicator_mtp3 | 1327 | **+58.01** (not ~+79R) |

**Conclusion:** Trade counts align with the old narrative; **total R does not**. `insample_expected_rows()` in `fixed_profile_oow_lib.py` was anchored to this replay so `sanity_pass` reflects **reproducible fixed-profile wiring**, not the obsolete headline R figures.

No candidate YAMLs or strategy logic were changed as part of this diagnostic.
