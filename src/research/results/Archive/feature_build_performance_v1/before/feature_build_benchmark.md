# Feature build benchmark

- asset=equity symbol=QQQ window=2025-01-01..2025-01-31
- repeat=3

| config | rows | cols | mean_s | min_s | max_s | warns | frag |
|--------|------|------|--------|-------|-------|-------|------|
| `failed_orb.yaml` | 7800 | 381 | 0.5919 | 0.3632 | 1.0416 | 2 | 2 |
| `pa_buy_sell_close_trend.yaml` | 7800 | 391 | 0.393 | 0.3761 | 0.4213 | 0 | 0 |
| `pa_climax_reversal.yaml` | 7800 | 391 | 0.3787 | 0.3764 | 0.3807 | 0 | 0 |
| `afternoon_continuation.yaml` | 7800 | 381 | 0.3761 | 0.3683 | 0.3869 | 2 | 2 |
