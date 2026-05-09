# Reduced Layer 2 — Strategy Library v2 Batch 1 (design only)

**Status:** design document only. **No** Layer 2 sweep was executed. **No** mini-WFO v4/v5.

## Rationale

Layer 1 2023–2024 (capped where noted in `sweep_manifest.csv`) produced **strict** candidates for:

- `rsi_failure_swing`
- `bollinger_squeeze_breakout`

and **relaxed** candidates for:

- `bollinger_band_fade_chop`
- `consecutive_bar_exhaustion`

That is **≥2** independent mechanism families with exportable YAMLs → a reduced Layer 2 pass is **defensible as a next research step** (still subject to human review and cost-stress policy).

## Proposed candidate buckets (YAML IDs from `selected_candidates/`)

### indicator_trend

- `intraday_ma_crossover` — *Layer 1 produced no passing rows; include only after grid retune or new Layer 1 sweep.*

### oscillator_reversal

- `rsi_failure_swing`: `RSI_FAILURE_SWING_001` … `_005`

### volatility_breakout

- `bollinger_squeeze_breakout`: `BOLLINGER_SQUEEZE_BREAKOUT_001` … `_005`

### range_mean_reversion

- `bollinger_band_fade_chop`: `BOLLINGER_BAND_FADE_CHOP_001` … `_005` (note `relaxed_filter` on all)

### price_action_exhaustion

- `consecutive_bar_exhaustion`: `CONSECUTIVE_BAR_EXHAUSTION_001` … `_005` (relaxed)

### rolling_channel_breakout

- `donchian_channel_breakout` — *defer until Layer 1 shows any stable edge; 2023–2024 run was negative on best-PF row.*

### strict_core_v2 (conceptual)

- Existing **refined failed / gap** core candidates (from mini-WFO v3 track) **plus** only the Batch 1 YAMLs above that survive **cost stress** and **behavior dedupe** in Layer 2 preflight.

## Suggested Layer 2 grid discipline

- Cap `max_open_positions=1` (current default).
- Run **cost stress** on any system that includes high-trade-count Batch 1 legs (`bollinger_squeeze_breakout` ~479 trades / window).
- Keep Batch 1 families **separate** from ORB/VWAP/gap/trap **conflict groups** until overlap diagnostics are reviewed.

## Explicit non-goals

- No full rolling WFO.
- No live / paper trading.
- No automatic promotion of relaxed-filter rows without manual review.
