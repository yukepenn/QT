# Weak-period diagnostic design (Layer3 expanded stability v1)

## Goal

Explain **why** specific calendar slices (e.g. quarters flagged in `complete_risk_flags.csv`) hurt PnL **without** naming them as fixed narrative regimes (“global down”, “chop”). Instead:

1. **Measure** QQQ context in each slice from data (return, vol, trend efficiency, range proxies).
2. **Measure** profile behavior in the same slice (PnL, trade count, exit mix, candidate contribution).
3. **Classify** outcomes into a small decision vocabulary (see `weak_period_interpretation.md` contract in future run).

## Anchor slices (starting set — not pre-labeled regimes)

| Slice type | Examples | Source |
|------------|----------|--------|
| Calendar quarters flagged in smoke risk register | 2025Q1, 2022Q4 | `complete_risk_flags.csv` (`R_2025Q1`, `R_2022Q4`) |
| Additional candidate weak quarter | e.g. 2023Q3 for `primary_mtp2_meta` (negative in `complete_quarterly_summary`) | Worst quarters per profile from **data** |
| Worst months | From `worst_month_r` / monthly CSV minima | `complete_profile_window_summary.csv`, `complete_monthly_summary.csv` |

**Rule:** Slice list is **discovered from smoke outputs + quarterly/monthly tables**, then frozen for the expanded stability run plan. Labels applied **after** metrics exist.

## Three-way attribution (per slice)

For each `(profile_id, slice)`:

1. **Market-context failure:** profile underperforms **and** context metrics show hostile conditions **vs** profile’s own historical distribution (e.g. bottom-decile context score with documented thresholds).
2. **Profile-specific failure:** profile underperforms **while** context is benign or mixed **and** attribution points to one candidate or exit path (e.g. GAP negative in slice while PA flat).
3. **Normal drawdown:** losses within expected dispersion given trade count and cost stress — **no** single dominant failure mode; document as variance.

## Outputs (future run)

| File | Role |
|------|------|
| `weak_period_context.csv` | QQQ + context metrics per slice |
| `weak_period_profile_pnl.csv` | Profile PnL / trades in slice |
| `weak_period_exit_reason.csv` | Exit mix in slice |
| `weak_period_candidate_contribution.csv` | PA / GAP / CCI slice R |
| `weak_period_interpretation.md` | Rules + narrative |

## Machine-readable plan

See **`weak_period_diagnostic_design.csv`** for diagnostic groups, inputs, outputs, and `pass_fail_use` / `notes`.
