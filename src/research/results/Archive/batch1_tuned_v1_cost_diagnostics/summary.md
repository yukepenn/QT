# Batch 1 tuned v1 — cost diagnostics (winner path)

- **runs_root:** `D:\OneDrive - Washington University in St. Louis\QT\src\combiner\results\layer2_qqq_v2_batch1_tuned_2023_2024_v1_diagnostics_local`
- **trades merged:** 376
- **total R:** 35.4175
- **Bollinger ΣR:** 35.4175
- **RSI ΣR:** 0.0000

## Answers (Phase 1 questions)

1. **PF@0.02 weak — wins too small vs costs, losses not rare enough:** `tuned_v1_winner_trade_quality.csv` — mean R on wins **~+1.38**, on losses **~−0.99**; **~0.46** win rate; gross R ratio (wins / |losses|) **~1.17**. Doubling slip consumes a large fraction of average win R → **PF → ~1.008** at 0.02 on the combiner leader.
2. **exit_reason:** `cost_by_exit_reason.csv` — **stop** 194 trades **ΣR ≈ −199.6**; **target** 152 **ΣR ≈ +223.5**; **max_hold** 30 **ΣR ≈ +11.6**. Stops are the main R sink; targets carry gross edge.
3. **Winner YAML params:** See prior `BOLLINGER_SQUEEZE_BREAKOUT_001` (tuned_v1): `bb_mid` stop, `target_r=1.5`, `max_hold_minutes=45`, `min_risk_per_share=0.03`.
4. **Entry window:** Use `cost_by_entry_minute_bucket.csv` (UTC hour proxy from `entry_ts_utc`).
5. **cost_as_R:** Tighter stops → smaller `risk_per_share` → higher `approx_round_trip_cost_r` at fixed slip.
6. **RSI vs squeeze:** If this merge includes strict_batch1, compare ΣR by `strategy`; squeeze usually **crowds out** RSI under priority.
7. **Top squeeze YAMLs:** Overlap matrix from Layer2 diagnostics still shows **near-duplicate** grids; tuned_v1 sweep leader is a **single** ID.

See `candidate_overlap_notes.md` and CSVs for bucket tables.
