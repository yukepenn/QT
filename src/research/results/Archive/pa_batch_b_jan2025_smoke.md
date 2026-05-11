# PA Batch B — Jan 2025 QQQ capped sweep smoke

**Not** formal Layer 1. Engine: `src/backtest/sweep.py` (`numba_fast`). **max_combos=18** per strategy. **min_trades=0** for display.

| Strategy | combinations_completed | max trades (best of 18 rows) |
|----------|------------------------|------------------------------|
| pa_broad_channel_zone | 18 | 0 |
| pa_climax_reversal | 18 | 4 |
| pa_second_entry_pullback | 18 | 0 |
| pa_wedge_reversal | 18 | 6 |

Zero-trade rows are acceptable when parity passes; they inform signal rate only.
