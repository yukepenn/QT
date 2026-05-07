"""Markdown reports for Layer 3 smoke (documentation only)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _df_to_md(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "(empty)"
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def interpretation_sections_markdown(
    system_summary: pd.DataFrame,
    fold_summary: pd.DataFrame,
) -> str:
    """Sections 7–12 for `layer3_smoke_summary.md` (narrative + values from aggregated CSVs)."""
    lines: list[str] = []

    lines.append("## 7. Cost stress (0.02 / 0.03 slippage per share)")
    lines.append("")
    lines.append(
        "Stress rows use the same frozen candidates and combiner rules as the base run; only "
        "`slippage_per_share` changes. See per-fold `cost_stress.csv` and rollup `cost_stress_by_fold.csv`."
    )
    lines.append("")
    if system_summary is not None and len(system_summary):
        sub = system_summary[
            [
                "system_id",
                "slip_0_02_total_r_mean",
                "slip_0_02_pf_mean",
                "slip_0_03_total_r_mean",
                "slip_0_03_pf_mean",
                "cost_0_02_survives",
                "cost_0_03_survives",
            ]
        ].copy()
        lines.append(_df_to_md(sub))
    lines.append("")
    if system_summary is not None and len(system_summary) and "cost_0_03_survives" in system_summary.columns:
        all_false = bool(~system_summary["cost_0_03_survives"].any())
        if all_false:
            lines.append(
                "**Read:** At the stitched level, `cost_0_03_survives` is **False** for every system in this run — "
                "treat 0.03/share as a harsh lens, not an automatic veto on further research."
            )
        else:
            lines.append(
                "**Read:** Check which rows pass `cost_0_03_survives` — stitched cost stress is an engineering lens, "
                "not a profitability claim."
            )
    lines.append("")

    lines.append("## 8. Monthly / quarterly concentration")
    lines.append("")
    lines.append(
        "Detailed cadence is in `monthly_breakdown_all.csv` (concatenated per-fold monthly breakdowns). "
        "Use it to see whether positive stitched R is concentrated in a small number of months."
    )
    lines.append("")

    lines.append("## 9. Daily trade number profile (trade #1 vs trade #2)")
    lines.append("")
    lines.append(
        "Where `max_trades_per_day` allows a second trade, fold-level columns `trade_1_total_r` and "
        "`trade_2_total_r` split contribution. See `daily_trade_number_by_fold.csv` and each fold’s "
        "`daily_trade_number_breakdown.csv`."
    )
    lines.append("")
    if fold_summary is not None and len(fold_summary):
        t2 = fold_summary[fold_summary["system_id"].isin(["trap_recent_top1", "opening_recent_top1"])][
            ["system_id", "fold_id", "trade_1_total_r", "trade_2_total_r", "trade_2_positive"]
        ].copy()
        lines.append(_df_to_md(t2))
    lines.append("")
    lines.append(_trade2_narrative_paragraph(fold_summary))
    lines.append("")

    lines.append("## 10. Interpretation flags (system rollup)")
    lines.append("")
    flag_cols = [
        "system_id",
        "positive_total_r",
        "pf_above_1",
        "pf_r_above_1",
        "cost_0_02_survives",
        "cost_0_03_survives",
        "drawdown_exceeds_insample",
        "single_fold_dependency",
        "trade_2_positive",
        "positive_fold_rate",
        "fold_concentration",
    ]
    if system_summary is not None and len(system_summary):
        have = [c for c in flag_cols if c in system_summary.columns]
        lines.append(_df_to_md(system_summary[have]))
    lines.append("")

    lines.append("## 11. Decision gate (smoke only)")
    lines.append("")
    gate = _classify_smoke_gate(system_summary, fold_summary)
    lines.append(f"**Overall:** {gate['overall']}")
    lines.append("")
    for sid, label in gate["per_system"].items():
        lines.append(f"- `{sid}`: **{label}**")
    lines.append("")
    lines.append(_gate_criteria_paragraph())
    lines.append("")

    lines.append("## 12. Recommended next step")
    lines.append("")
    if gate["overall"].startswith("Caution") or gate["overall"].startswith("Fail"):
        lines.append(
            "- **Do not** jump to a full rolling walk-forward or broaden grids based on this smoke alone."
        )
        lines.append(
            "- Prefer **strategy-family diagnosis** (why 2023/2024 differ from the recent segment) unless "
            "you explicitly approve a narrow **causal mini-WFO** (e.g. train 2023-01-01→2024-12-31, "
            "test 2025-01-01→2026-04-30) as a separate, labeled experiment."
        )
    else:
        lines.append(
            "- If team agrees, propose a **causal mini-WFO** with frozen methodology — still not live-ready."
        )
    lines.append("")
    return "\n".join(lines)


def _trade2_narrative_paragraph(fold_summary: pd.DataFrame) -> str:
    """Short data-aware note on trade #2 vs max_trades_per_day=1 systems."""
    parts = []
    if fold_summary is None or len(fold_summary) == 0:
        return "**Read:** (no fold rows)"

    sub = fold_summary[
        (fold_summary["system_id"] == "trap_recent_top1") & (fold_summary["fold_id"] == "y2023")
    ]
    if len(sub):
        t1 = float(sub.iloc[0].get("trade_1_total_r") or 0.0)
        t2 = float(sub.iloc[0].get("trade_2_total_r") or 0.0)
        if t2 < min(0.0, t1):
            parts.append(
                f"**Read:** **trap_recent_top1** / **y2023** shows trade #2 total R ({t2:.4f}) far below trade #1 ({t1:.4f}) — "
                "the second intraday slot can dominate negatively in hostile regimes."
            )
    if not parts:
        parts.append(
            "**Read:** Compare `trade_1_total_r` vs `trade_2_total_r` where both apply; "
            "**full_history_opening_pair** uses `max_trades_per_day: 1`, so trade #2 columns are absent there."
        )
    else:
        parts.append(
            "**full_history_opening_pair** uses `max_trades_per_day: 1` only — no trade #2 bucket."
        )
    return " ".join(parts)


def _classify_smoke_gate(
    system_summary: pd.DataFrame,
    fold_summary: pd.DataFrame,
) -> dict[str, Any]:
    """Return overall + per-system labels: Pass / Caution / Fail (heuristic for smoke reporting)."""
    per: dict[str, str] = {}
    if system_summary is None or len(system_summary) == 0:
        return {"overall": "Caution (no system rows)", "per_system": per}

    scores: list[int] = []  # fail=-1, caution=0, pass=1

    for _, row in system_summary.iterrows():
        sid = str(row.get("system_id", ""))
        pfr = float(row.get("positive_fold_rate", 0.0))
        sfd = bool(row.get("single_fold_dependency", False))
        c02 = bool(row.get("cost_0_02_survives", False))
        pfr_ok = bool(row.get("pf_r_above_1", False))
        pfc = int(row.get("positive_fold_count", 0))

        label = "Caution"
        score = 0
        # Fail tier: only one fold contributes positively *and* concentration heuristic fires
        if pfc <= 1 and sfd:
            label = "Fail"
            score = -1
        elif pfr_ok and pfr >= (2.0 / 3.0) and not sfd and c02:
            label = "Pass"
            score = 1
        elif pfr < (2.0 / 3.0) or sfd or not c02:
            label = "Caution"
            score = 0

        per[sid] = label
        scores.append(score)

    any_fail = any(s == -1 for s in scores)
    all_pass = all(s == 1 for s in scores)

    if any_fail:
        overall = "Caution — at least one system is **Fail**-tier on this smoke heuristic (often single-fold reliance)."
    elif all_pass:
        overall = "Pass — smoke heuristics satisfied on all systems (still not live-ready)."
    else:
        overall = (
            "Caution — mixed folds, concentration, or cost stress; **2025–2026** overlaps the recent "
            "Layer 2 source window for Systems A/B; interpret stitched positives skeptically."
        )

    return {"overall": overall, "per_system": per}


def _gate_criteria_paragraph() -> str:
    return (
        "**Heuristic (not a trading signal):** **Fail**-like behavior includes mostly negative folds plus "
        "clear reliance on one segment. **Caution** covers mixed years, single-fold dominance "
        "(`single_fold_dependency`), or failure of stitched 0.03 stress (`cost_0_03_survives`). "
        "**Pass** would require most folds positive or near-flat, `pf_r_above_1`, 0.02 survival, and "
        "no extreme concentration — rarely met on first smoke."
    )
