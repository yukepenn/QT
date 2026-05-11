# Quality score v1.5 (offline, diagnostic)

## Rule changes (vs v1)

Documented in `score_rule_changes_v15.md` (JSON). Highlights:

- **`regime_unknown`:** **neutral** — no bonus/penalty from `entry_regime_label_summary` tables (still allows non-regime tweaks such as VWAP-cross churn).
- **Unknown early minute:** small **+2** hypothesis bonus when `entry_minute_from_open <= 60` (documented as weak prior).
- **Indicator repeat penalty:** applied **only if** `indicator_mtp_comparison.csv` shows **mtp=2** with **trade #2 total R < 0**. In this v1.5 run, trade #2 is **positive**, so the penalty is **off**.

## Outputs

| File | Content |
|------|---------|
| `vwap_threshold_holdout_v15.csv` | 2023 train / 2024 test rows with **`trade_quality_score_v15`** — train all, test all, test top80 with **train** threshold |
| `indicator_threshold_diagnostics_v15.csv` | Threshold table for **indicator_completion_mtp1** using v15 scores |

## Did v1.5 “fix” VWAP holdout?

On the **2023→2024** diagnostic slice in `vwap_threshold_holdout_v15.csv`, **test top80 (train threshold)** still has **lower total R** than **test all**. So **no**: v1.5 does **not** establish robust score separation on that split.

## Did v1.5 help indicator?

`indicator_threshold_diagnostics_v15.csv`: **top80pct_score** remains **worse** than **all** on total R at mtp=1. **No** material improvement from v1 rules in this pass.

## Router prototype?

**Not yet** — see `../router_readiness_decision_v15.md` (**`NEED_MORE_TRADE_ENRICHMENT`**).
