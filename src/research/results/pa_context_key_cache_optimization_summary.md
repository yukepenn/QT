# PA `context_key` cache optimization — summary (2026-05-10)

## 1. Purpose

Tighten **`context_key`** on all ten PA strategies so Layer 1 / Layer 2 **context caches** key only on **`prepare_signal_context`** outputs (which feature windows / columns are loaded), not on signal thresholds or risk parameters applied later in **`generate_signal_arrays_from_context`** / **`finalize_long_signals_df`**.

## 2. Performance-only

This is a **cache partitioning** change. **`normalized_param_key`** still encodes fields that change final signals, so sweep dedupe and candidate identity semantics stay intact.

## 3. Strategies audited

PA Batch A: `pa_trading_range_bls_hs`, `pa_failed_range_breakout_trap`, `pa_tight_channel_pullback`, `pa_mtr_reversal`  
PA Batch B: `pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`  
PA Batch C: `pa_buy_sell_close_trend`, `pa_generic_breakout_pullback`

## 4. Fields removed from `context_key` (by strategy)

See **`pa_context_key_cache_scope_audit.md`** table. Typical removals: entry/score thresholds, VWAP bool gates, `stop_mode` / `target_*` (never belonged in context), `fail_window_bars` / `require_tr_regime` where unused in prepare, `recent_breakout_lookback` / `pullback_test_atr` where only post-load logic uses them.

## 5. Fields retained in `normalized_param_key`

No reductions. Removed context fields were **already** present in each strategy’s **`normalized_param_key`** (or are feature-axis fields covered by **`feature_key`** where relevant).

## 6. Tests added

- **`tests/test_pa_context_key_scope.py`** — per-strategy checks: threshold-only overrides → stable `context_key`, changed `normalized_param_key`; window / `atr_column` overrides → changed `context_key`. Special cases: `pa_regime_window` without prepare use (`pa_climax_reversal`, `pa_broad_channel_zone`, `pa_second_entry_pullback`, `pa_wedge_reversal`); **`fail_window_bars`** unused in `pa_failed_range_breakout_trap` signal path.

## 7. Validation

- `python -m pytest -q` — full suite green after changes.
- `check_strategy_fast_parity.py` — `failed_orb` + representative PA YAMLs (see **`pa_context_key_signal_fingerprint_check.md`**).
- `python -m compileall -q src` — OK.

## 8. Cache reuse smoke

See **`pa_context_key_cache_reuse_smoke.md`** (unique `context_key` counts over expanded tuned grids; no Layer 1 execution).

## 9. Explicit non-runs

- No Layer 1 rerun  
- No Layer 2 run  
- No mini-WFO / full WFO  
- No live / paper  
- No new strategies  
- No deletion of curated `selected_candidates` or results trees  

## 10. Next recommended step

**PA Batch B/C reduced Layer 2** using tuned v2 candidate YAMLs, with cost stress and behavior dedupe gates — unchanged planning priority.
