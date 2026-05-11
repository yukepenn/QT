# PA `context_key` — signal fingerprint / parity check (2026-05-10)

## Approach

Per project instructions, we did **not** commit a separate binary/hash fingerprint file. Validation is:

1. **`check_strategy_fast_parity.py`** (pandas vs fast arrays) on representative configs **before and after** `context_key` edits — all runs reported **0** mismatched fields.
2. **`tests/test_pa_context_key_scope.py`** — asserts threshold-only mutations leave `context_key` stable and change `normalized_param_key`; shape mutations change `context_key`.

## Commands run (post-change)

- `failed_orb` — `failed_orb_focused.yaml`, QQQ 2025-01 — 2025-01-31, `--max-combos 2`
- `pa_buy_sell_close_trend` — `pa_buy_sell_close_trend_tuned_v2.yaml`, same window
- `pa_climax_reversal` — `pa_climax_reversal_tuned_v2.yaml`
- `pa_trading_range_bls_hs` — `pa_trading_range_bls_hs_tuned_v1.yaml`
- `pa_broad_channel_zone` — `pa_broad_channel_zone_tuned_v2.yaml`
- `pa_failed_range_breakout_trap` — `pa_failed_range_breakout_trap_tuned_v1.yaml`
- `pa_generic_breakout_pullback` — `pa_generic_breakout_pullback_tuned_v2.yaml`

## Result

All parity checks completed with **`TOTAL_MISMATCH_FIELDS approx=0`**.

## Limitation

Parity covers sampled grid combos (`--max-combos 2`), not exhaustive Cartesian proof over every YAML row.
