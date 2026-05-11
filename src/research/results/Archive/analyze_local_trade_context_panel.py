"""
Analyze local-only trade context panel (v1) and emit commit-safe aggregates.

This script must NOT require row-level artifacts to be committed; it only reads the local panel.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _agg(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(group_cols, dropna=False)
    rs = pd.to_numeric(df["r_multiple"], errors="coerce")
    out = g["r_multiple"].agg(trades="count", total_r="sum", avg_r="mean", median_r="median").reset_index()
    out["win_rate"] = g["r_multiple"].apply(lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean()) if len(s) else 0.0).values
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Emit additional aggregates from local trade context panel (v1).")
    p.add_argument("--context-replay-root", required=True)
    p.add_argument("--local-panel", required=True)
    args = p.parse_args(argv)

    root = Path(args.context_replay_root)
    if not root.is_absolute():
        root = Path.cwd() / root

    panel = pd.read_csv(Path(args.local_panel))
    if panel.empty:
        raise RuntimeError("local panel is empty")

    # Attribution
    att = root / "attribution_v1"
    if "candidate_id" in panel.columns:
        _write_csv(_agg(panel, ["candidate_id"]), att / "candidate_contribution_overall.csv")
    if "candidate_id" in panel.columns and "context_bucket" in panel.columns:
        _write_csv(_agg(panel, ["context_bucket", "candidate_id"]), att / "candidate_contribution_by_context_bucket.csv")
    if "candidate_id" in panel.columns and "market_context_label" in panel.columns:
        _write_csv(_agg(panel, ["market_context_label", "candidate_id"]), att / "candidate_contribution_by_market_context.csv")
    if "candidate_id" in panel.columns and "period_quarter" in panel.columns:
        _write_csv(_agg(panel, ["period_quarter", "candidate_id"]), att / "candidate_contribution_by_weak_period.csv")
    if "decision_pa_regime_label_20_label" in panel.columns and "candidate_id" in panel.columns:
        _write_csv(_agg(panel, ["decision_pa_regime_label_20_label", "candidate_id"]), att / "candidate_contribution_by_regime.csv")
    _write_md(
        att / "attribution_summary.md",
        [
            "# attribution_summary (v1)",
            "",
            "These tables attribute realized R to `candidate_id` across context groupings.",
            "They do **not** attempt counterfactual attribution when candidates conflict on the same bar.",
            "",
        ],
    )

    # Freshness / trade-number
    fr = root / "freshness_v1"
    if "entry_trade_number_of_day" in panel.columns:
        _write_csv(_agg(panel, ["profile_id", "entry_trade_number_of_day"]), fr / "trade_number_by_profile.csv")
        if "context_bucket" in panel.columns:
            _write_csv(_agg(panel, ["context_bucket", "entry_trade_number_of_day"]), fr / "trade_number_by_context.csv")
    if "entry_prior_trade_same_family" in panel.columns:
        tmp = panel.copy()
        tmp["same_family_repeat_flag"] = tmp["entry_prior_trade_same_family"].astype("bool", errors="ignore")
        _write_csv(_agg(tmp, ["profile_id", "same_family_repeat_flag"]), fr / "same_family_repeat_results.csv")
    if "entry_prior_trade_was_loss" in panel.columns:
        tmp = panel.copy()
        _write_csv(_agg(tmp, ["profile_id", "entry_prior_trade_was_loss"]), fr / "prior_loss_followup_results.csv")
    _write_md(
        fr / "freshness_router_implications.md",
        [
            "# freshness_router_implications (v1)",
            "",
            "- Use `trade_number_by_*` to test whether trade #2 behaves differently by context.",
            "- Use prior-loss and repeat tables to evaluate downweight/block ideas (diagnostic only).",
            "",
        ],
    )

    # Exit overlay readiness (feasibility only)
    ex = root / "exit_overlay_readiness_v1"
    t = panel.copy()
    bh = pd.to_numeric(t.get("bars_held", pd.Series(np.nan, index=t.index)), errors="coerce")
    ctx = t.get("context_bucket", pd.Series("unknown_mixed", index=t.index)).astype(str)
    mode = pd.Series(["trend_swing"] * len(t), index=t.index, dtype="string")
    mode = mode.mask((bh <= 5) & ctx.isin(["trading_range", "unknown_mixed"]), "scalp")
    mode = mode.mask((bh >= 30) & ctx.eq("trend_long"), "runner")
    mode = mode.mask(ctx.eq("late_climax"), "reversal")
    t["exit_mode_preview"] = mode
    _write_csv(_agg(t, ["exit_mode_preview"]), ex / "exit_mode_assignment_preview.csv")
    _write_csv(
        pd.DataFrame(
            [
                {
                    "rows": int(len(t)),
                    "rows_with_bars_held": int(bh.notna().sum()),
                    "note": "exit_mode_preview is heuristic; no exit simulation performed.",
                }
            ]
        ),
        ex / "exit_overlay_data_coverage.csv",
    )
    _write_md(
        ex / "exit_overlay_readiness_summary.md",
        [
            "# exit_overlay_readiness_summary (v1)",
            "",
            "This is a feasibility pass only (no engine changes, no trailing-stop simulation).",
            "",
        ],
    )

    # Roadmap evidence update (very lightweight)
    rd = root / "roadmap_update_v1"
    rows: list[dict[str, Any]] = []
    if "context_bucket" in panel.columns:
        g = panel.groupby("context_bucket", dropna=False)["r_multiple"].agg(["count", "sum"]).reset_index()
        for _, r in g.iterrows():
            strength = "WEAK"
            if int(r["count"]) >= 300 and float(r["sum"]) > 20:
                strength = "MODERATE"
            if int(r["count"]) >= 600 and float(r["sum"]) > 50:
                strength = "STRONG"
            rows.append(
                {
                    "context_bucket": str(r["context_bucket"]),
                    "trades": int(r["count"]),
                    "total_r": float(r["sum"]),
                    "evidence_strength": strength,
                    "notes": "Evidence is from Champion v0 only; does not imply new strategy implementation.",
                }
            )
    _write_csv(pd.DataFrame(rows), rd / "scalp_roadmap_evidence_update.csv")
    _write_csv(pd.DataFrame(rows), rd / "short_roadmap_evidence_update.csv")
    _write_csv(
        pd.DataFrame(
            [
                {"priority": 1, "item": "router/quality integration", "reason": "offline diagnostics exist"},
                {"priority": 2, "item": "exit overlay diagnostics", "reason": "mode preview available"},
                {"priority": 3, "item": "scalp long design", "reason": "requires isolated Layer1"},
                {"priority": 4, "item": "short branch design", "reason": "requires short-only Layer1/OOW"},
            ]
        ),
        rd / "strategy_library_v3_priority.csv",
    )
    _write_md(rd / "roadmap_update_summary.md", ["# roadmap_update_summary (v1)", "", "See CSVs for evidence strength by context bucket.", ""])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

