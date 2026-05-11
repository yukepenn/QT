# PA strategies — Brooks compatibility audit (2026-05-10)

Engineering-only phase: **no** signal logic edits in strategy plugins; this document maps each plugin to Brooks concepts and new shared primitives.

## Classification (research)

| Strategy | Tier | Brooks concept owner |
|----------|------|----------------------|
| `pa_buy_sell_close_trend` | Core / near-core | Always-in / strong-close trend legs |
| `pa_climax_reversal` | Core / near-core | Climax / exhaustion fade |
| `pa_trading_range_bls_hs` | Core / near-core | Trading range, failed breakouts, magnets |
| `pa_failed_range_breakout_trap` | Core / near-core | Failed breakout trap, range context |
| `pa_second_entry_pullback` | Core / near-core | Pullback / second-entry structure |
| `pa_broad_channel_zone` | Diagnostic / cautious | Broad channel, buy zone |
| `pa_tight_channel_pullback` | Diagnostic / cautious | Tight channel pullback |
| `pa_wedge_reversal` | Diagnostic / cautious | Wedge / MTR wedge proxy |
| `pa_mtr_reversal` | Diagnostic / cautious | Major trend reversal proxy |
| `pa_generic_breakout_pullback` | **Deferred** until gate logic improves | Breakout pullback (often zero-signal in baseline economics) |

## Per-strategy notes

Columns named are **current** `required_features` / prepare context — not an exhaustive list of every optional column on the frame.

### `pa_buy_sell_close_trend`

- **Family:** Batch C — strong close / trend continuation.
- **Features used:** Session VWAP / ORB context, trend scores, body / reversal bars, PA range and regime windows as configured.
- **New primitives available:** `strong_*_close`, micro-channels, `pa_always_in_side_*`, `pa_regime_label_*`, magnet proximity.
- **Role:** Remains **core**; future tuned YAML may layer regime gates — **not** in this phase.
- **Code change this phase:** None.
- **ORB/VWAP overlap:** Uses shared VWAP / ORB **known** columns only (no trap/gap edits).

### `pa_climax_reversal`

- **Family:** Batch B — climax fade.
- **Features used:** Climax / overlap / channel scores, reversal bars, ATR column.
- **New primitives:** `pa_late_trend_score_*`, `pa_trade_mode_*`, bar signal / failed-signal columns.
- **Role:** **Core**; diagnostics benefit from explicit climax + transition scores.
- **Code change:** None.

### `pa_trading_range_bls_hs`

- **Family:** Batch A — trading range BLS/HS style long MVP.
- **Features used:** Range high/low/mid, failed breakout, close back inside, TR scores.
- **New primitives:** `pa_mm_range_*`, trapped scores, regime router.
- **Role:** **Core**.
- **Code change:** None.

### `pa_failed_range_breakout_trap`

- **Family:** Batch A — failed range breakout trap.
- **Features used:** Failed breakout down, close back inside, bull reversal, follow-through down, rolling range geometry, **`pa_trading_range_score_{rw}`** when `require_tr_regime` is enabled.
- **New primitives:** Same as TR family + explicit `pa_regime_label_*` for future gating.
- **Role:** **Core**.
- **Code change:** None.

#### Special audit: `require_tr_regime` / `tr_regime_max`

Implementation (`generate_signal_arrays_from_context`): when `require_tr_regime` is true, a bar is **skipped** if `pa_trading_range_score` is **non-finite** or **`pa_tr > tr_regime_max`**.

Given the definition of `pa_trading_range_score_{N}` in `regime.py` (higher when **weak trend** / range-like structure dominates), **`tr_regime_max` acts as an upper bound on that score** — i.e. it **filters out** bars where the TR score is **too high** relative to the threshold, not a literal “minimum TR-ness” floor.

**Conclusion (documentation option A):** Current behavior is **internally consistent** as a **cap on extreme range/chop score** for the optional gate, but the pair of YAML names **`require_tr_regime`** + **`tr_regime_max`** is **easy to misread** (sounds like “require at least X trading-range”). **No silent semantic change** in this phase.

**Backlog (option B):** Add YAML aliases such as `tr_regime_score_max` / `max_pa_trading_range_score` and non-breaking synonyms in validation only, with tests, in a future cleanup PR — **not** done here.

### `pa_second_entry_pullback`

- **Family:** Batch B — second entry after pullback.
- **Features used:** Higher-low proxy, wedge push, pullback / channel context.
- **New primitives:** `pa_second_entry_buy_proxy_*`, two-leg pullback columns (aligned naming; strategy still uses existing columns until a future grid).
- **Role:** **Core / near-core**.
- **Code change:** None.

### `pa_broad_channel_zone`

- **Family:** Batch B — broad channel zone entries.
- **Features used:** Broad channel scores, VWAP distance, zone caps.
- **New primitives:** `pa_broad_*` regime labels already related; new router columns for diagnostics.
- **Role:** **Diagnostic / cautious** (economics historically weak at full grid).
- **Code change:** None.

### `pa_tight_channel_pullback`

- **Family:** Batch A/B — tight channel pullback.
- **Features used:** Tight channel scores, pullback depth vs ATR.
- **New primitives:** Micro-channels, tight regime labels.
- **Role:** **Diagnostic / cautious**.
- **Code change:** None.

### `pa_wedge_reversal` / `pa_mtr_reversal`

- **Family:** Structure / reversal proxies.
- **Features used:** Wedge push counts, climax / overlap, MTR-specific thresholds.
- **New primitives:** Second-entry proxies, trapped scores for future refinement.
- **Role:** **Diagnostic / cautious**.
- **Code change:** None.

### `pa_generic_breakout_pullback`

- **Family:** Batch C — generic breakout pullback.
- **Status:** **Deferred** until shared gates / grids improve (baseline Layer 1 often zero-signal).
- **Code change:** None.

## Overlap warning

All PA plugins are **long-only MVP** and must keep **ORB / VWAP / gap / trap** shared columns read-only: this phase **did not** modify non-PA strategy code or ORB/VWAP/gap/trap formulas.
