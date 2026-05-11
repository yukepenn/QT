# Candidate selection — PA Batch A Layer 1 (QQQ 2023–2024)

Generated via `src/research/select_candidates.py --manifest sweep_manifest.csv`.

## Strict thresholds (primary `selected_candidates/`)

- `min_trades`: **30**
- `min_profit_factor`: **1.05**
- `min_total_r`: **0**
- `max_drawdown_r`: **-50**
- `max_avg_bars_held`: **120**
- `max_eod_count`: **0**
- `max_end_of_data_count`: **0**
- `--top-per-strategy`: **5**
- **No** `--allow-relaxed-fallback` on the primary export.

## Outcome

- **Strict YAMLs written:** 4 (all **`pa_failed_range_breakout_trap`**).
- **No strict YAML:** `pa_trading_range_bls_hs` (best rows fail `min_total_r`), `pa_tight_channel_pullback`, `pa_mtr_reversal`.

## Diagnostic relaxed (non-authoritative)

Folder: `diagnostic_relaxed_selection/` — thresholds `min_trades=18`, `min_profit_factor=1.0`, `min_total_r=-3`, `max_drawdown_r=-60`, `max_avg_bars_held=150`. **Still only** `pa_failed_range_breakout_trap` rows pass; see that folder’s `candidate_summary.md` (header below patched to label **diagnostic**).

## Output files

- `selected_candidates.csv`, `selected_candidates/*.yaml`
- `candidate_summary.md`, `summary.txt`
- `no_candidate_strategies.txt`
- `candidate_fast_context_check.{csv,md}` (strict YAMLs only)
