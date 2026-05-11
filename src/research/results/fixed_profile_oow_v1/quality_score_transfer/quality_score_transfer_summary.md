# Quality score transfer (OOW)

Train thresholds on **2023–2024** session dates only; apply to other dates in the same trade file.
**Requires** `entry_regime_label` on trades — use `enrich_combiner_trades.py` on each `trades.csv` if missing.

Outputs: `vwap_score_transfer.csv`, `indicator_score_transfer.csv` (split from combined when present).
