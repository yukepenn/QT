# PA Batch B — implementation summary (2026-05-10)

## Scope

Four long-only fast-path strategies: **pa_broad_channel_zone**, **pa_climax_reversal**, **pa_second_entry_pullback**, **pa_wedge_reversal**.

## Feature additions (shared)

- `regime.py`: `pa_broad_bull_channel_score_N`, `pa_broad_bear_channel_score_N`, `pa_bar_range_expansion_N`, `pa_distance_from_vwap_atr`.
- `pa_swings.py`: `pa_higher_low_proxy_N` (coarse vs prior-exclusive range low).
- `pa_batch_a_utils.py`: stop/target helpers (`vwap` target, `channel_low`, climax/wedge/second-entry lows as signal-low aliases, `breakout_point_buffer` reserved for Batch C, `last_pullback_low` → range low).

## Loader

**33** strategies (29 + 4).

## Validation

- `pytest` including PA registration, no-lookahead, synthetic signal tests.
- Jan 2025 parity smokes: see `pa_batch_b_parity_smoke.*`.
- Jan 2025 capped sweeps: see `pa_batch_b_jan2025_smoke.*`.

## Explicit non-runs

No Layer 1/2, mini-WFO, full WFO, or live/paper for Batch B in this phase.
