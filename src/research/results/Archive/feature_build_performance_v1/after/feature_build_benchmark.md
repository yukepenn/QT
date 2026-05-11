# Feature build benchmark

- asset=equity symbol=QQQ window=2025-01-01..2025-01-31
- repeat=3

| config | rows | cols | mean_s | min_s | max_s | warns | frag |
|--------|------|------|--------|-------|-------|-------|------|
| `failed_orb.yaml` | 7800 | 381 | 0.4504 | 0.3653 | 0.6166 | 0 | 0 |
| `pa_buy_sell_close_trend.yaml` | 7800 | 391 | 0.3788 | 0.3765 | 0.381 | 0 | 0 |
| `pa_climax_reversal.yaml` | 7800 | 391 | 0.3888 | 0.3792 | 0.4042 | 0 | 0 |
| `afternoon_continuation.yaml` | 7800 | 381 | 0.3693 | 0.3662 | 0.3749 | 0 | 0 |
