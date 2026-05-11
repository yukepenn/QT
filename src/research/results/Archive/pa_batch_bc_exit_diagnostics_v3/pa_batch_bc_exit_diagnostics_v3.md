# PA Batch B/C exit diagnostics — tuned v3 strict candidates

Window: **2023-01-01 → 2024-12-31**, QQQ. Baseline backtest slippage **0.01**; stress column **0.02**.

Full table: `pa_batch_bc_exit_diagnostics_v3.csv` (same columns as v2 export).

## Headline vs tuned v2 (representative rows)

| family | metric | tuned v2 (rank-1 style) | tuned v3 (current strict #001 / climax) |
|--------|--------|------------------------|-------------------------------------------|
| Close-trend | trades | 461 (`…_001`) | 443 (`…_001` v3) |
| Close-trend | total_r @ 0.01 | 41.56 | 37.92 |
| Close-trend | total_r @ **0.02** | 36.30 | 32.84 |
| Climax | trades | 51 | 50 |
| Climax | total_r @ 0.01 | 6.23 | 5.91 |
| Climax | total_r @ **0.02** | 1.72 | **3.03** |

**Read:** v3 climax grid moved economics slightly **down** at 0.01 but **up** at 0.02 vs v2’s 0.02 stress on the old rank-1 row — still **only one signal path** across five YAMLs (see diversity CSV).

## Max-hold share (v3 close-trend top rows)

`max_hold_count` remains material on close-trend (see CSV: 199–251 across top configs); climax remains **low avg bars held** (~8.7).
