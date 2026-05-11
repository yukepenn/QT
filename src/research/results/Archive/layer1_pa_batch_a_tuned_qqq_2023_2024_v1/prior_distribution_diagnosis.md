# Prior Layer 1 sweep — distribution diagnosis

**Limitation:** Per-bar `results.csv` trees under `src/strategies/testing_parameters_results/**` are **not present** in this workspace clone (gitignored / not synced). Row-level grouping by `stop_mode`, `confirm_mode`, etc. **cannot** be recomputed locally.

## Aggregate metrics (from committed `layer1_pa_batch_a_qqq_2023_2024`)

Source: `sweep_manifest.csv`, `signal_rate_diagnosis.csv`, `layer1_pa_batch_a_summary.md`.

| strategy | result_rows | combos_w_trades | max_trades | median_trades | p75_trades | best_total_r | best_PF | best_maxDD_r |
|----------|-------------|-----------------|------------|---------------|------------|--------------|---------|--------------|
| pa_trading_range_bls_hs | 18 | 18 | 409 | 426 | 443 | -6.93 | 1.095 | -37.84 |
| pa_failed_range_breakout_trap | 18 | 18 | 331 | 331 | 331 | +2.84 | 1.135 | -47.19 |
| pa_tight_channel_pullback | 18 | 18 | 14 | 14 | 14 | -3.04 | 0.943 | -5.87 |
| pa_mtr_reversal | 18 | 18 | 1 | 1 | 1 | +1.98 | inf (1 trade) | 0.0 |

## Interpretation without CSV columns

- **Trading range:** High trade counts with **negative best total R** suggests **fee/slippage drag** or **weak expectancy** on the **highest-PF** fingerprint — tightening **score / range width / confirm** is the primary lever (matches tuning v1 YAML).
- **Failed trap:** **DD ~ -47** vs strict **-50** gate — quality tuning (`fail_window_bars`, `require_tr_regime`, stops/targets) is appropriate.
- **Tight channel:** **14 max trades** — thresholds **`tight_bull_score_min`** / **`max_pullback_depth_atr`** likely binding; loosen for discovery.
- **MTR:** **Single-trade max** — **`bear_channel_score_min`** and **`require_wedge_proxy`** are strong filters; loosen cautiously.

## Row-level claims

**Not available** without `results.csv`. Re-run this diagnosis against local sweep outputs if needed.
