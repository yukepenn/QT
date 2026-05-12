# Combiner ↔ execution contract

## TradeIntent fields (minimum)

- `candidate_id`, `strategy`, `side`, `signal_idx`, `entry_idx`
- `stop_price`, `target_mode`, `target_r` or `target_price`, optional `risk_per_share`
- `max_hold_bars`, `qty`, `management_mode`, `family`, `setup_type`

## TradeResult → combiner row

See `trade_result_to_combiner_row` for column names aligned with legacy `trades_df` where practical, plus `combiner_adapter_version` and `result_lineage`.

## CLI

- `python -m src.combiner.run ... --engine legacy` (default): archived Numba / detailed logs.
- `python -m src.combiner.run ... --engine canonical`: execution-backed sequential adapter.
- `--dry-run`: skip disk writes for main CLI path.
