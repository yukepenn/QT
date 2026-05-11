# Robust-candidate overlap summary (local-only trades read)

- Overlap is computed on **entry_ts_utc** and **session_date** sets, unioned across all three windows.
- Raw trade rows are not written; only compact overlap metrics are persisted.

## Highest entry overlap pairs

```
                candidate_a                 candidate_b  jaccard_entry_ts_utc  jaccard_session_date  n_entries_a  n_entries_b  n_sessions_a  n_sessions_b  ok_a  ok_b
 GAP_ACCEPTANCE_FAILURE_001  GAP_ACCEPTANCE_FAILURE_002              1.000000              1.000000          403          403           403           403  True  True
 GAP_ACCEPTANCE_FAILURE_001  GAP_ACCEPTANCE_FAILURE_003              1.000000              1.000000          403          403           403           403  True  True
 GAP_ACCEPTANCE_FAILURE_001  GAP_ACCEPTANCE_FAILURE_004              1.000000              1.000000          403          403           403           403  True  True
 GAP_ACCEPTANCE_FAILURE_002  GAP_ACCEPTANCE_FAILURE_003              1.000000              1.000000          403          403           403           403  True  True
 GAP_ACCEPTANCE_FAILURE_002  GAP_ACCEPTANCE_FAILURE_004              1.000000              1.000000          403          403           403           403  True  True
 GAP_ACCEPTANCE_FAILURE_003  GAP_ACCEPTANCE_FAILURE_004              1.000000              1.000000          403          403           403           403  True  True
PA_BUY_SELL_CLOSE_TREND_001 PA_BUY_SELL_CLOSE_TREND_002              1.000000              1.000000         1379         1379          1379          1379  True  True
PA_BUY_SELL_CLOSE_TREND_001 PA_BUY_SELL_CLOSE_TREND_003              1.000000              1.000000         1379         1379          1379          1379  True  True
PA_BUY_SELL_CLOSE_TREND_002 PA_BUY_SELL_CLOSE_TREND_003              1.000000              1.000000         1379         1379          1379          1379  True  True
PA_BUY_SELL_CLOSE_TREND_001 PA_BUY_SELL_CLOSE_TREND_004              0.753569              0.953665         1379         1446          1379          1446  True  True
```
