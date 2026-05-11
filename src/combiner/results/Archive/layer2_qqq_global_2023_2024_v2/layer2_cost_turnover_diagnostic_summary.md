# Layer 2 cost / turnover diagnostic summary (existing Global L2 v2 exports)

- **result_root**: `D:/OneDrive - Washington University in St. Louis/QT/src/combiner/results/layer2_qqq_global_2023_2024_v2`
- **top_unique rows**: 50
- **cost stress join**: yes

## 1) Why VWAP dominates ``combiner_score``

Production score (``src/combiner/metrics.py``) is roughly:

```
PF + 0.015*total_r - 0.03*|maxDD| - 0.001*avg_bars_held
  - 0.02*max_hold_count - 0.05*(eod + end_of_session + end_of_data) - 2.0[trades<50]
```

Multi-strategy buckets with similar ``total_r`` can lose versus ``vwap_core`` when:

- **max_hold_count** / exit-mix penalties are larger (not always present in ``top_unique`` export — see ``residual_reported_minus_implied`` in ``layer2_score_decomposition.csv``).
- **Drawdown** is deeper (``-0.03*|maxDD|`` term).
- **avg_bars_held** is higher (``-0.001`` per bar).
- **PF** is lower — PF enters with unit weight, while ``total_r`` only scales by **0.015**.

Example from this pack: **indicator_completion_core** near rank ~49 has **higher total_r** than the VWAP headline but **lower combiner_score** — decomposition shows the **drawdown + bars-held + PF tradeoff** vs VWAP; residual column captures missing **max_hold / exit counts** not exported in ``top_unique_systems.csv``.

## 2) Top 20 unique systems (baseline 0.01 slip from sweep)

 unique_rank candidate_set  trades   total_r  profit_factor  max_drawdown_r  avg_bars_held  combiner_score
           1     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           2     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           3     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           4     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           5     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           6     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           7     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           8     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
           9     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
          10     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
          11     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
          12     vwap_core     337 42.203127       1.210320      -10.498071       7.451039        1.320974
          13     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          14     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          15     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          16     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          17     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          18     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          19     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333
          20     vwap_core     346 40.423770       1.188357       -9.363475       7.476879        1.286333

## 3) Cost robustness (joined stress ladder where available)

Per-row PASS/FAIL uses **total_r > 0** and **PF > 1** at each stress slip. **THIN_EDGE** flags **>65%** decay in total_r from baseline → 0.02 when baseline > 0.

See ``layer2_cost_adjusted_ranking.csv`` for post-hoc objective and retention metrics.

## 4) Turnover / edge thickness

See ``layer2_turnover_summary.csv`` (``avg_r_per_trade = total_r / trades``).

## 5) Family dominance (top 30 by unique_rank)

candidate_set  rows_in_top_n family_label
    vwap_core             30    vwap_core

- **vwap_core rows in top 30**: 30

## 6) Decision from exports only

- Confirms **`TUNE_LAYER2_COST_TURNOVER`**: headline systems are **high trade count**, **cost fragile at +0.03 slip**, and **behavior-dedupe** (see committed behavior pack) is still **VWAP-pair variants**.
- Does **not** justify Layer 3 yet: need tightened turnover/session grids and non-VWAP diagnostics from new sweeps.

## Outputs

- `layer2_score_decomposition.csv`
- `layer2_cost_adjusted_ranking.csv`
- `layer2_turnover_summary.csv`
- `layer2_family_dominance_summary.csv`
