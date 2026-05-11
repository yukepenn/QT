# Market context label design (data-derived)

## Rules

- **No** label row may equate a calendar period (e.g. `2025Q1`) to a semantic regime name. Calendar slices are **inputs** to metric computation; **labels** are outputs of thresholds applied to metrics.
- Prefer metrics computable from **existing** QQQ OHLC / returns in the research data path. If a metric would require **new** feature primitives, mark **`future_optional`** in the CSV and exclude from hard gates for v1.

## Label set (v1 contract)

| label_name | Intuition |
|------------|------------|
| `uptrend_low_vol` | Positive drift + calm |
| `uptrend_high_vol` | Positive drift + stress vol |
| `downtrend_low_vol` | Negative drift + calm |
| `downtrend_high_vol` | Negative drift + stress vol |
| `range_chop` | Low trend efficiency + high range / VWAP churn |
| `high_gap_environment` | Elevated gap activity vs ATR |
| `late_trend_climax_like` | **Heuristic** strong quarter with late vol spike + intra-quarter reversal |
| `unknown_mixed` | Fallback |

## Thresholds (set ex ante in expanded stability runner — not in this design doc)

- Store rolling lookback `L`, vol percentiles, trend/range efficiency cutoffs in a **single YAML or CSV** shipped with `layer3_expanded_stability_v1/` so ChatGPT can read thresholds without parsing code.

## CSV

See `market_context_label_design.csv` for definitions, inputs, availability, fallbacks, and misclassification risks.
