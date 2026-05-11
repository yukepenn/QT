# Expected outputs — future `layer3_expanded_stability_v1/`

This schema defines what a **future execution** should materialize. Nothing in this list is required to exist until the expanded stability task runs.

## ChatGPT-first

- **`CHATGPT_REVIEW_BUNDLE.md`** and **`SOURCE_MAP.csv`** are **mandatory** for any executed expanded stability root so reviewers can follow the story without opening dozens of CSVs.

## Derivation

| Output | Mostly from existing complete smoke? |
|--------|--------------------------------------|
| `profile_monthly_stability.csv` | **Yes** (copy/slice) |
| `profile_quarterly_stability.csv` | **Yes** |
| `rolling_3month_summary.csv` | **Yes** (derived) |
| `weak_period_context.csv` | **No** — needs QQQ daily series |
| `weak_period_profile_pnl.csv` | **Partial** — coarse from monthly; fine from trades |
| `weak_period_exit_reason.csv` / contribution / cost-by-period | **No** unless trade tape available |

## CSV

See **`expanded_stability_expected_outputs.csv`**.
