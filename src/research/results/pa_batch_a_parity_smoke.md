# PA Batch A — fast parity smoke (QQQ Jan 2025)

Window: **2025-01-01 → 2025-01-31**. Command: `python src/research/check_strategy_fast_parity.py` with each strategy’s `*_focused.yaml` and `--max-combos 2`.

| strategy | exit_code | total_mismatch_fields | notes |
|----------|-----------|----------------------|--------|
| pa_trading_range_bls_hs | 0 | 0 | Pandas vs fast context parity OK |
| pa_failed_range_breakout_trap | 0 | 0 | same |
| pa_tight_channel_pullback | 0 | 0 | same |
| pa_mtr_reversal | 0 | 0 | same |

**Legacy check:** `failed_orb` with `failed_orb_focused.yaml` on the same window — **exit 0**, mismatch fields **0**.

Machine-readable companion: `pa_batch_a_parity_smoke.csv`.
