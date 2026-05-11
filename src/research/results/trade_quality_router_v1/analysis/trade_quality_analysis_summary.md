# Trade quality analysis (consolidated)

Quantile buckets: see per-system `*_summary.md` files. Low-sample rows flagged in CSV.

## Per-system totals

- **indicator_completion_mtp1**: n=502, total_r=43.546, win_rate=0.504
- **vwap_baseline_global_l2**: n=337, total_r=42.203, win_rate=0.504
- **vwap_lower_turnover**: n=294, total_r=36.707, win_rate=0.503

## Cost sensitivity note

Symmetric proxy: extra `+0.01` slip/share per leg vs baseline adds roughly `-0.02 / risk_per_share` R per round trip when applied to both entry and exit. Target fills are modeled with slip in the combiner; see design doc for limitations.
