# Brooks PA framework — feature smoke (2026-05-10)

## Purpose

Light **`build_features_from_config`** smoke on **QQQ 2025-01-01 → 2025-01-31** using representative PA testing YAMLs. **No** sweeps; outputs are counts only (see CSV).

## Method

- Load merged strategy config from each testing YAML (defaults + grid row 0 or equivalent path used by internal smoke script).
- Build features; count **new-style** column name prefixes/suffixes (bar primitives, swing primitives, regime router, magnets).
- Count columns whose names end with **`_LOOKAHEAD`** anywhere in the built frame (expected **3** from `levels.py` diagnostics: `full_session_*_LOOKAHEAD` — **not** required by PA strategies).

## Results table

| config | rows | new_feature_columns_count | missing_expected_columns | lookahead_columns_count | notes |
|--------|------|---------------------------|--------------------------|-------------------------|-------|
| pa_buy_sell_close_trend_tuned_v2.yaml | 200 | 30 | | 3 | `build_features_from_config` with default parameters yaml |
| pa_climax_reversal_tuned_v2.yaml | 200 | 30 | | 3 | same |
| pa_trading_range_bls_hs_tuned_v1.yaml | 200 | 30 | | 3 | same |

Full machine-readable copy: **`pa_brooks_feature_smoke.csv`**.

## Interpretation

- **`new_feature_columns_count`**: heuristic count of columns added in this Brooks-primitives phase (subset match on names); exact set is listed in `pa_brooks_feature_primitives_summary.md`.
- **`lookahead_columns_count`**: frame-wide; strategies must still avoid `*_LOOKAHEAD` in `required_features` (verified in `tests/test_pa_required_features_no_lookahead.py`).

## Explicit non-runs

No Layer 1 / Layer 2 / mini-WFO / full WFO / live.
