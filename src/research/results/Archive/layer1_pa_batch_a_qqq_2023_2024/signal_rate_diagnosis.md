# Signal / trade-rate diagnosis

Computed from each strategy's `results.csv` plus **best row** metrics aligned with `sweep_manifest.csv` (best row = highest finite `profit_factor`).

## Dedup note

Focused YAML expands to **108** raw grid cells; `sweep.py` **deduplicates** parameter fingerprints so each run completed **18** distinct combo rows (`combinations_skipped_duplicate=90`). Trade-rate stats below are on those **18** rows.

## Summary

| Strategy | result_rows | max_trades | median_trades | best PF | best total R | Jan 2025 hint | Assessment |
|----------|-------------|------------|----------------|----------|--------------|---------------|--------------|
| pa_trading_range_bls_hs | 18 | 443 | 426 | 1.095 | -6.93 | had trades | **Viable signal rate** on 2023–2024; **strict selection fails** `min_total_r>=0` (best R still negative). |
| pa_failed_range_breakout_trap | 18 | 331 | 331 | 1.135 | +2.84 | had trades | **Viable signal rate**; only family with **strict** candidates. |
| pa_tight_channel_pullback | 18 | 14 | 14 | 0.943 | -3.04 | 0 trades Jan | **Sparse vs BLS/trap**; Jan zero-trade **not** a full-window bug — still low edge. |
| pa_mtr_reversal | 18 | 1 | 1 | n/a (inf in one row) | +1.98 (single-trade combo) | 0 trades Jan | **Ultra-sparse** (max 1 trade / combo on dedup grid); **gate_too_strict_or_bug_suspected** for economics (not parity failure). |

## Jan vs 2023–2024

- **`pa_tight_channel_pullback`:** Jan smoke zero-fill; full window shows **14** trades max per combo — **resolved** as “not globally dead”, still **weak** for Layer 1 strict gates.
- **`pa_mtr_reversal`:** Jan smoke zero-fill; full window shows **at most 1** trade per evaluated combo — **remains structurally ultra-sparse**; tune grid/thresholds before treating as portfolio-ready.
