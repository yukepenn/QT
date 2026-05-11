# Unknown regime decomposition summary (v1.5)

Per-system CSVs under each `<system>/` folder. Aggregate keys: `unknown_regime_key_buckets.csv`.

## Router policy suggestion (research only)

- Default **neutral** on `regime_unknown` until sub-buckets are stable across holdouts.
- If early-minute buckets dominate unknown PnL, prefer **decomposed sub-score** over global penalty.

Systems analyzed: indicator_completion_mtp1, vwap_baseline_global_l2, vwap_lower_turnover
