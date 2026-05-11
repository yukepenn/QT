# Candidate selection — PA Batch A tuned v1 (QQQ 2023–2024)

Generated via `src/research/select_candidates.py --manifest sweep_manifest.csv`.

## Strict thresholds

- `min_trades`: **30**
- `min_profit_factor`: **1.05**
- `min_total_r`: **0**
- `max_drawdown_r`: **-50**
- `max_avg_bars_held`: **120**
- `max_eod_count`: **0**
- `max_end_of_data_count`: **0**
- `--top-per-strategy`: **5**

## Outcome

- **10** strict YAMLs: **5** `pa_trading_range_bls_hs`, **5** `pa_failed_range_breakout_trap`
- **No strict YAML:** `pa_tight_channel_pullback`, `pa_mtr_reversal` (see `no_candidate_strategies.txt`)

## Diagnostic relaxed

**Not run** — strict set already spans **two** PA families (`pa_trading_range`, `pa_range_breakout_failure`).
