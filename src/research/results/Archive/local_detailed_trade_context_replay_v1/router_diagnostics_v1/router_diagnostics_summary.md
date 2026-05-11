# router_diagnostics_summary (v1)

- mode: `offline_diagnostic` (draft config; `enabled: False`)
- local panel: `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` (local-only dependency)

## Filters tested

- `baseline_all_trades`
- `avoid_context_removed`
- `preferred_or_neutral_only`
- `gap_downweight_unknown_mixed`
- `late_climax_trend_chase_removed`
- `high_chop_trend_chase_removed`
- `context_fit_preferred_only`

## Top deltas vs baseline (by total_r)

| diagnostic_id | trades | total_r | avg_r | win_rate | pf_r | max_dd_r_proxy | worst_month_r | worst_quarter_r | 2025Q1_total_r | 2022Q4_total_r | 2023Q3_total_r | delta_total_r_vs_baseline | delta_max_dd_r_proxy_vs_baseline | trade_count_retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_all_trades | 10628 | 744.950005896781 | 0.07009315072419844 | 0.508468197214904 | 1.1803407157159396 | -115.33119804241164 | -53.15217595781322 | -53.74524378935653 | -53.74524378935653 | -40.291149207570776 | -19.20764451379972 | 0.0 | 0.0 | 1.0 |
| high_chop_trend_chase_removed | 10628 | 744.950005896781 | 0.07009315072419844 | 0.508468197214904 | 1.1803407157159396 | -115.33119804241164 | -53.15217595781322 | -53.74524378935653 | -53.74524378935653 | -40.291149207570776 | -19.20764451379972 | 0.0 | 0.0 | 1.0 |
| avoid_context_removed | 10616 | 737.1269003269751 | 0.0694354653661431 | 0.5081009796533534 | 1.178466011671564 | -115.33119804241164 | -53.15217595781322 | -53.74524378935653 | -53.74524378935653 | -40.291149207570776 | -19.20764451379972 | -7.823105569805875 | 0.0 | 0.9988709070380128 |
| gap_downweight_unknown_mixed | 9200 | 621.2253256539116 | 0.06752449191890343 | 0.5095652173913043 | 1.1798364170799034 | -107.62025253292649 | -56.1834167172236 | -61.26425715710742 | -61.26425715710742 | -11.396880007297266 | -6.80316298296447 | -123.72468024286945 | 7.710945509485157 | 0.8656379375235228 |
| late_climax_trend_chase_removed | 5008 | 527.2156922944667 | 0.10527469894058841 | 0.5251597444089456 | 1.283744378186971 | -68.87637586672884 | -44.77620085540717 | -38.365128523212014 | -13.196712155121553 | -5.577889620361595 | -24.081544585272017 | -217.73431360231427 | 46.45482217568281 | 0.47120812946932633 |
| context_fit_preferred_only | 3628 | 379.0764618539738 | 0.10448634560473369 | 0.5242557883131201 | 1.2832305645647513 | -60.34158353359305 | -44.32115911026176 | -40.26775062074748 | -13.176346096420072 | -21.55620513541758 | -12.945125545720177 | -365.8735440428072 | 54.98961450881859 | 0.34136243884079787 |

Notes:
- `max_dd_r_proxy` is a **sequence proxy** computed from cumulative R sorted by `signal_ts_utc` (not a precise equity curve with capital constraints).
- This script does **not** change combiner behavior; it only filters the already-generated trade list.

