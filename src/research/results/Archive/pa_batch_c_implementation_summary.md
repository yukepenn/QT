# PA Batch C — implementation summary (2026-05-10)

## Plugins

- **pa_buy_sell_close_trend** — strong close near high, body / consecutive bull closes, trend score; optional VWAP side; blocks high climax score. Fast backtest fills **next bar open** (see `src/backtest/fast.py`). **target_mode:** `fixed_r` only (MVP).
- **pa_generic_breakout_pullback** — recent `pa_breakout_up` + follow-through, pullback to `pa_prior_high`, overlap cap, bull reversal. Stops include **`breakout_point_buffer`** (ATR buffer below breakout level). **No** `measured_move` target (omitted by design).

## Loader

**35** strategies (33 + 2).

## Smokes

- Parity: `pa_batch_c_parity_smoke.*`
- Jan 2025 capped sweep: `pa_batch_c_jan2025_smoke.*`

## Non-runs

No formal Layer 1/2, mini-WFO, full WFO, live/paper for Batch C in this phase.
