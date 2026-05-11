# trade_context_panel_summary

## Policy
- **Champion v0** summaries only; **no** row-level trade tape committed.
- See `trade_context_missing_inputs.csv` for columns that need **local-only** replay + enrich.

## Outputs
- `trade_context_available_fields.csv` — fields derivable from curated `complete_*` tables.
- `trade_context_panel_aggregated_by_*.csv` — window / period / exit / trade# / market-context (if present).

## Future local-only command draft (not executed here)
```text
python -m src.research.fixed_profile_oow postprocess --runs-root <local_layer3_runs_root> --profiles ...
# then offline merge trades with FeatureStore columns into trade_context_panel row-level (local disk only)
```
