# Prior row-level diagnosis (baseline sweeps)

Source: `layer1_pa_batch_bc_qqq_2023_2024` sweep `results.csv` per strategy.

## pa_broad_channel_zone

- rows: **72** | with_trades: **0** | zero_trades: **72**
- max_trades: **0** | median(nonzero): **** | p75(nonzero): ****
- best PF row: trades=0 pf=0.0000 total_r=0.0000 dd_r=0.0000 avg_bars_held=0.00
- best row trades>=30: **NONE**
- best row trades>=15: **NONE**

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 72 | 0 | 0 |  | 0.0000 | 0.0000 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 72 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| range_low | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| signal_low | 36 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| prior_high | 36 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 1.35 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |
| 1.75 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |
| 2.0 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |
| 75.0 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |
| 90.0 | 24 | 0 | 0 |  | 0.0000 | 0.0000 |

## pa_climax_reversal

- rows: **72** | with_trades: **72** | zero_trades: **0**
- max_trades: **93** | median(nonzero): **93.00** | p75(nonzero): **93.00**
- best PF row: trades=93 pf=0.8793 total_r=-13.7067 dd_r=-17.8986 avg_bars_held=7.37
- best row trades>=30: row=12 trades=93 pf=0.8793 total_r=-13.7067
- best row trades>=15: row=12 trades=93 pf=0.8793 total_r=-13.7067

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 45.0 | 72 | 72 | 93 | 93.00 | 0.8793 | -12.6067 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 72 | 72 | 93 | 93.00 | 0.8793 | -12.6067 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| signal_low | 36 | 36 | 93 | 93.00 | 0.8793 | -12.6067 |
| atr_buffer | 36 | 36 | 93 | 93.00 | 0.8103 | -17.0216 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 36 | 36 | 93 | 93.00 | 0.8793 | -12.6067 |
| vwap | 36 | 36 | 93 | 93.00 | 0.7396 | -17.5812 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 1.5 | 24 | 24 | 93 | 93.00 | 0.8793 | -13.7067 |
| 1.9 | 24 | 24 | 93 | 93.00 | 0.8784 | -13.3736 |
| 1.2 | 24 | 24 | 93 | 93.00 | 0.8638 | -12.6067 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 50.0 | 24 | 24 | 93 | 93.00 | 0.8793 | -12.6067 |
| 65.0 | 24 | 24 | 93 | 93.00 | 0.8793 | -12.6067 |
| 80.0 | 24 | 24 | 93 | 93.00 | 0.8793 | -12.6067 |

## pa_second_entry_pullback

- rows: **72** | with_trades: **36** | zero_trades: **36**
- max_trades: **8** | median(nonzero): **8.00** | p75(nonzero): **8.00**
- best PF row: trades=8 pf=2.3867 total_r=6.5772 dd_r=-1.0667 avg_bars_held=4.50
- best row trades>=30: **NONE**
- best row trades>=15: **NONE**

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 72 | 36 | 8 | 8.00 | 2.3867 | 6.5772 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 72 | 36 | 8 | 8.00 | 2.3867 | 6.5772 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| signal_low | 36 | 18 | 8 | 8.00 | 2.3867 | 6.5772 |
| atr_buffer | 36 | 18 | 8 | 8.00 | 1.4759 | 3.0403 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 36 | 18 | 8 | 8.00 | 2.3867 | 6.5772 |
| prior_high | 36 | 18 | 8 | 8.00 | 0.8298 | 0.2891 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 2.0 | 24 | 12 | 8 | 8.00 | 2.3867 | 6.5772 |
| 1.75 | 24 | 12 | 8 | 8.00 | 2.0800 | 5.3272 |
| 1.35 | 24 | 12 | 8 | 8.00 | 1.5893 | 3.3272 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 24 | 12 | 8 | 8.00 | 2.3867 | 6.5772 |
| 75.0 | 24 | 12 | 8 | 8.00 | 2.3867 | 6.5772 |
| 90.0 | 24 | 12 | 8 | 8.00 | 2.3867 | 6.5772 |

## pa_wedge_reversal

- rows: **72** | with_trades: **72** | zero_trades: **0**
- max_trades: **126** | median(nonzero): **123.00** | p75(nonzero): **126.00**
- best PF row: trades=126 pf=0.9642 total_r=-10.0950 dd_r=-24.7699 avg_bars_held=10.06
- best row trades>=30: row=24 trades=126 pf=0.9642 total_r=-10.0950
- best row trades>=15: row=24 trades=126 pf=0.9642 total_r=-10.0950

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 45.0 | 72 | 72 | 126 | 123.00 | 0.9642 | -8.0123 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 72 | 72 | 126 | 123.00 | 0.9642 | -8.0123 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| signal_low | 36 | 36 | 126 | 123.00 | 0.9642 | -8.0123 |
| atr_buffer | 36 | 36 | 126 | 123.00 | 0.8195 | -21.1504 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 36 | 36 | 126 | 126.00 | 0.9642 | -8.0213 |
| vwap | 36 | 36 | 120 | 120.00 | 0.8427 | -8.0123 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 1.9 | 24 | 24 | 126 | 123.00 | 0.9642 | -8.0123 |
| 1.55 | 24 | 24 | 126 | 123.00 | 0.9441 | -8.0123 |
| 1.25 | 24 | 24 | 126 | 123.00 | 0.9210 | -8.0123 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 55.0 | 24 | 24 | 126 | 123.00 | 0.9642 | -8.0213 |
| 70.0 | 24 | 24 | 126 | 123.00 | 0.9441 | -8.0123 |
| 85.0 | 24 | 24 | 126 | 123.00 | 0.9441 | -8.0213 |

## pa_buy_sell_close_trend

- rows: **108** | with_trades: **108** | zero_trades: **0**
- max_trades: **413** | median(nonzero): **393.50** | p75(nonzero): **407.75**
- best PF row: trades=413 pf=1.2304 total_r=24.0700 dd_r=-10.8558 avg_bars_held=59.34
- best row trades>=30: row=14 trades=413 pf=1.2304 total_r=24.0700
- best row trades>=15: row=14 trades=413 pf=1.2304 total_r=24.0700

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 108 | 108 | 413 | 393.50 | 1.2304 | 24.0700 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 108 | 108 | 413 | 393.50 | 1.2304 | 24.0700 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| last_pullback_low | 36 | 36 | 413 | 393.50 | 1.2304 | 24.0700 |
| signal_low | 36 | 36 | 413 | 393.50 | 1.1217 | 0.7366 |
| atr_buffer | 36 | 36 | 413 | 393.50 | 0.9674 | -39.0024 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 108 | 108 | 413 | 393.50 | 1.2304 | 24.0700 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 1.35 | 36 | 36 | 413 | 393.50 | 1.2304 | 24.0700 |
| 1.0 | 36 | 36 | 413 | 393.50 | 1.2139 | 22.6664 |
| 1.7 | 36 | 36 | 413 | 393.50 | 1.2062 | 20.5604 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 70.0 | 36 | 36 | 413 | 393.50 | 1.2304 | 24.0700 |
| 55.0 | 36 | 36 | 413 | 393.50 | 1.1503 | 19.8134 |
| 40.0 | 36 | 36 | 413 | 393.50 | 1.1217 | 12.5530 |

## pa_generic_breakout_pullback

- rows: **108** | with_trades: **0** | zero_trades: **108**
- max_trades: **0** | median(nonzero): **** | p75(nonzero): ****
- best PF row: trades=0 pf=0.0000 total_r=0.0000 dd_r=0.0000 avg_bars_held=0.00
- best row trades>=30: **NONE**
- best row trades>=15: **NONE**

### Axis hints (top by best PF)

**signal.entry_start_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 60.0 | 108 | 0 | 0 |  | 0.0000 | 0.0000 |

**signal.entry_end_minute**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 210.0 | 108 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.stop_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| atr_buffer | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| breakout_point_buffer | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| pullback_low | 36 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.target_mode**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| fixed_r | 54 | 0 | 0 |  | 0.0000 | 0.0000 |
| prior_high | 54 | 0 | 0 |  | 0.0000 | 0.0000 |

**risk.target_r**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 1.2 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| 1.55 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| 1.9 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |

**backtest.max_hold_minutes**

| value | rows | with_trades | max_trades | med_trades | best_pf | best_total_r |
|-------|------|------------|-----------|------------|---------|--------------|
| 65.0 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| 80.0 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |
| 95.0 | 36 | 0 | 0 |  | 0.0000 | 0.0000 |

