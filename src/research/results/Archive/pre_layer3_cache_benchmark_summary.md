# Pre‑Layer‑3 cache benchmark — summary

Conclusion: **PASS** (top_unique first-row equality vs cache_off, tol=1e-6)

## Runtime (wall clock)

| mode | sweep_sec | postprocess_sec | signal_cache_hits | signal_cache_misses | feature_requests | feature_hits | feature_misses |
|---|---:|---:|---:|---:|---:|---:|---:|
| cache_off | 483.2509187 | 33.2704816 |  | 40 | 40 | 36 | 4 |
| cache_on_cold | 331.8139967 | 17.0693613 |  | 40 | 40 | 36 | 4 |
| cache_on_warm | 232.82338 | 16.9474118 | 40 |  | 1 |  | 1 |

## Top unique first row (cache_off reference)

cache_off:
```
{
  "candidate_set": "trap_family",
  "cooldown_after_loss_minutes": "0",
  "daily_max_loss_r": -1.5,
  "max_drawdown_r": -12.08248671106061,
  "max_trades_per_day": "2",
  "priority_policy": "metadata_priority",
  "profit_factor": 1.5163060854737551,
  "top_per_strategy": "1",
  "total_r": 69.05727748217748,
  "trades": "323"
}
```

cache_on_cold:
```
{
  "candidate_set": "trap_family",
  "cooldown_after_loss_minutes": "0",
  "daily_max_loss_r": -1.5,
  "max_drawdown_r": -12.08248671106061,
  "max_trades_per_day": "2",
  "priority_policy": "metadata_priority",
  "profit_factor": 1.5163060854737551,
  "top_per_strategy": "1",
  "total_r": 69.05727748217748,
  "trades": "323"
}
```

cache_on_warm:
```
{
  "candidate_set": "trap_family",
  "cooldown_after_loss_minutes": "0",
  "daily_max_loss_r": -1.5,
  "max_drawdown_r": -12.08248671106061,
  "max_trades_per_day": "2",
  "priority_policy": "metadata_priority",
  "profit_factor": 1.5163060854737551,
  "top_per_strategy": "1",
  "total_r": 69.05727748217748,
  "trades": "323"
}
```

## Differences vs cache_off (if any)

cache_off vs cache_on_cold:
```
(none)
```

cache_off vs cache_on_warm:
```
(none)
```