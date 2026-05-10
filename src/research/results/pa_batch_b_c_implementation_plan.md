# PA Batch B / C — implementation plan (2026-05-10)

## Strategy files

| Batch | File |
|-------|------|
| B | `src/strategies/strategy/pa_broad_channel_zone.py` |
| B | `src/strategies/strategy/pa_climax_reversal.py` |
| B | `src/strategies/strategy/pa_second_entry_pullback.py` |
| B | `src/strategies/strategy/pa_wedge_reversal.py` |
| C | `src/strategies/strategy/pa_buy_sell_close_trend.py` |
| C | `src/strategies/strategy/pa_generic_breakout_pullback.py` |

## Feature columns

### Batch B

- Broad channel: `pa_broad_bull_channel_score_N`, `pa_broad_bear_channel_score_N` — **added** in `regime.py` (width/efficiency/trend, no future bars).
- Buy zone: existing `pa_range_lower_third_N`, `pa_prior_high/low`, `pa_pullback_depth_atr_N`.
- Climax: existing `pa_climax_score_N`; expansion proxy: `pa_bar_range_expansion_N` — **added** in `regime.py` (current `bar_range` vs prior rolling mean of `bar_range`, shift inside rolling).
- VWAP distance (signed): `pa_distance_from_vwap_atr` — **added** in `regime.py` as `(close - vwap) / atr`.
- Second entry / wedge: `pa_wedge_push_count_N`, `pa_higher_low_proxy_N` — proxy **added** in `pa_swings.py` as `(low > pa_prior_low_N)`; wedge count unchanged (prior-shifted rising-low streak).
- Follow-through / back-inside: existing `pa_followthrough_*`, `pa_close_back_inside_*`.
- Reversal / wicks: existing `bull_reversal_bar`, wick columns.

### Batch C

- Strong close / trend: existing `close_near_high`, `consecutive_bull_closes_*`, `trend_score_*` (regime), `body_pct`, `pa_climax_score_*`.
- Breakout pullback: existing `pa_breakout_up_N`, `pa_prior_high_N`, `pa_pullback_depth_atr_N`, `pa_followthrough_up_N`.

## No-lookahead proof

- Swing/range columns remain prior-exclusive (`rolling(...).shift(1)` on highs/lows).
- New regime columns use only current bar OHLC/VWAP/ATR, session-scoped rolling with `shift(1)` where means are used (`pa_bar_range_expansion`).
- Broad channel scores compose existing same-bar-safe series (`rw_atr`, `reff`, `trend_norm`, `narrow`).
- `pa_higher_low_proxy` compares current `low` to prior-exclusive range low `rl` only.

## Overlap vs existing ~29 strategies

- No new ORB, VWAP-only, gap, or multi-day trap plugins.
- `pa_generic_breakout_pullback` uses rolling prior range, not `orb_*`.
- `pa_buy_sell_close_trend` is continuation after strong close; distinct from ORB failed / VWAP reclaim strategies but cost-sensitive (documented in metadata).

## Refinements

- Brooks-overlap items: **documentation-only** in `pa_overlap_refinements_backlog.md` unless a zero-default alias is trivial; this phase **no** behavior changes to `failed_orb`, `orb_*`, `vwap_*`, `gap_*`, `prior_close_reclaim`, `multi_day_level_trap`.

## Explicit non-runs

- No formal Layer 1 / Layer 2 for Batch B/C.
- No mini-WFO, full WFO, live/paper.
- Only Jan 2025 QQQ smokes (capped combos), parity, unit tests.
