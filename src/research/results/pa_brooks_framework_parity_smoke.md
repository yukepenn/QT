# Brooks PA framework — fast parity smoke (2026-05-10)

## Purpose

Re-validate **`check_strategy_fast_parity.py`** after PA feature / helper additions. Window: **QQQ 2025-01-01 → 2025-01-31**, **`--max-combos 2`**.

## Results

| strategy | testing_config | exit_code | total_mismatch_approx | notes |
|----------|----------------|-----------|------------------------|-------|
| failed_orb | failed_orb_focused.yaml | 0 | 0 | non-PA control |
| pa_buy_sell_close_trend | pa_buy_sell_close_trend_tuned_v2.yaml | 0 | 0 | |
| pa_climax_reversal | pa_climax_reversal_tuned_v2.yaml | 0 | 0 | |
| pa_trading_range_bls_hs | pa_trading_range_bls_hs_tuned_v1.yaml | 0 | 0 | |
| pa_failed_range_breakout_trap | pa_failed_range_breakout_trap_tuned_v1.yaml | 0 | 0 | |
| pa_second_entry_pullback | pa_second_entry_pullback_focused.yaml | 0 | 0 | |

CSV: **`pa_brooks_framework_parity_smoke.csv`**.

## Explicit non-runs

No Layer 1 / Layer 2 / mini-WFO / full WFO / live.
