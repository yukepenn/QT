# Feature build benchmark

- asset=equity symbol=QQQ window=2025-01-01..2025-01-31
- repeat=3

| config | rows | cols | mean_s | min_s | max_s | warns | frag |
|--------|------|------|--------|-------|-------|-------|------|
| `failed_orb.yaml` | 7800 | 381 | 0.4736 | 0.3823 | 0.6483 | 0 | 0 |
| `afternoon_continuation.yaml` | 7800 | 381 | 0.3883 | 0.3858 | 0.3925 | 0 | 0 |
| `pa_buy_sell_close_trend.yaml` | 7800 | 391 | 0.3922 | 0.3861 | 0.3964 | 0 | 0 |
| `pa_climax_reversal.yaml` | 7800 | 391 | 0.4059 | 0.3963 | 0.4203 | 0 | 0 |
