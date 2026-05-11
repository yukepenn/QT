# Candidate selection — Layer 1 v2 completion (QQQ 2023–2024)

Generated via `src/research/select_candidates.py --manifest sweep_manifest.csv`.

## Strict thresholds

- `min_trades`: 40
- `min_profit_factor`: 1.05
- `min_total_r`: 0
- `max_drawdown_r`: -60
- `max_avg_bars_held`: 120
- `max_eod_count`: 0
- `max_end_of_data_count`: 0

## Relaxed fallback (enabled)

- `min_trades`: 25
- `min_profit_factor`: 1.00
- `min_total_r`: -5
- `max_drawdown_r`: -70
- `max_avg_bars_held`: 150 (`--relaxed-max-avg-bars-held`)

## Top per strategy

- `--top-per-strategy`: **5**

## Output files

- `selected_candidates.csv`
- `selected_candidates/*.yaml`
- `candidate_summary.md`
- `summary.txt`
- `no_candidate_strategies.txt`

Strategies with **no** rows passing strict or relaxed filters are listed in `no_candidate_strategies.txt`.
