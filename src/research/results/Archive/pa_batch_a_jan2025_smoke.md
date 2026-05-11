# PA Batch A — Jan 2025 sweep smoke (not Layer 1)

**Purpose:** wiring / crash / impossible-geometry check only — **not** performance claims.

**Window:** QQQ **2025-01-01 → 2025-01-31**.  
**Command template:** `python src/backtest/sweep.py --strategy <name> --testing-config src/strategies/testing_parameters/<name>_focused.yaml --asset equity --symbols QQQ --start 2025-01-01 --end 2025-01-31 --top 20 --min-trades 1 --max-combos 50 --tag pa_batch_a_jan2025_smoke --progress-every 20`

## Summary

| strategy | exit | result rows | best trades (display top) | notes |
|----------|------|-------------|---------------------------|--------|
| pa_trading_range_bls_hs | 0 | 18 | 18 | Negative R on best-PF row; smoke OK |
| pa_failed_range_breakout_trap | 0 | 18 | 14 | Positive PF on leader; smoke OK |
| pa_tight_channel_pullback | 0 | 18 | 0 | No fills in Jan sample for evaluated grid slice |
| pa_mtr_reversal | 0 | 18 | 0 | No fills in Jan sample for evaluated grid slice |

Outputs written under `src/strategies/testing_parameters_results/<strategy>/sweep_*_pa_batch_a_jan2025_smoke/` (gitignored heavy tree; CSV companion here is curated).

**Warning:** zero-trade sweeps for two strategies indicate **sparse signals** on this short window and/or strict thresholds — follow up in Layer 1 economics, not from this smoke alone.
