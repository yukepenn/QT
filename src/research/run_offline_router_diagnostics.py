"""
Offline router diagnostics (v1) — research-only.

Consumes:
- offline router rule design (CSV) from playbook router cycle v1
- local-only row-level trade_context_panel.csv from local detailed replay v1

Produces:
- aggregate-only diagnostic tables (safe to commit)
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _df_to_md_table(df: pd.DataFrame, *, max_rows: int = 30) -> str:
    """Small markdown table without requiring `tabulate`."""
    if df is None or df.empty:
        return "_(empty)_"
    d = df.head(int(max_rows)).copy()
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def _max_drawdown_r_proxy(df: pd.DataFrame, *, r_col: str = "r_multiple", ts_col: str = "signal_ts_utc") -> float | None:
    if df.empty or r_col not in df.columns:
        return None
    d = df.copy()
    if ts_col in d.columns:
        d["_ts"] = pd.to_datetime(d[ts_col], utc=True, errors="coerce")
        d = d.sort_values("_ts")
    rs = pd.to_numeric(d[r_col], errors="coerce").fillna(0.0).to_numpy()
    eq = np.cumsum(rs)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    return float(dd.min()) if len(dd) else None


def _period_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    sd = pd.to_datetime(out["session_date"].astype(str), errors="coerce")
    out["period_month"] = sd.dt.strftime("%Y-%m")
    out["period_quarter"] = sd.dt.to_period("Q").astype(str)
    return out


def _summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "trades": 0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "win_rate": 0.0,
            "pf_r": None,
            "max_dd_r_proxy": None,
            "worst_month_r": None,
            "worst_quarter_r": None,
            "2025Q1_total_r": None,
            "2022Q4_total_r": None,
            "2023Q3_total_r": None,
        }
    rs = pd.to_numeric(df["r_multiple"], errors="coerce")
    wins = float(rs[rs > 0].sum())
    losses = float(rs[rs < 0].sum())
    pf = None
    if losses != 0:
        pf = float(wins / abs(losses))
    elif wins > 0:
        pf = float("inf")
    d = _period_cols(df)
    m = d.groupby("period_month", dropna=False)["r_multiple"].sum()
    q = d.groupby("period_quarter", dropna=False)["r_multiple"].sum()
    out = {
        "trades": int(len(df)),
        "total_r": float(rs.sum()),
        "avg_r": float(rs.mean()),
        "win_rate": float((rs > 0).mean()),
        "pf_r": pf,
        "max_dd_r_proxy": _max_drawdown_r_proxy(df),
        "worst_month_r": float(m.min()) if len(m) else None,
        "worst_quarter_r": float(q.min()) if len(q) else None,
        "2025Q1_total_r": float(q.get("2025Q1")) if "2025Q1" in q.index else None,
        "2022Q4_total_r": float(q.get("2022Q4")) if "2022Q4" in q.index else None,
        "2023Q3_total_r": float(q.get("2023Q3")) if "2023Q3" in q.index else None,
    }
    return out


@dataclass(frozen=True)
class Rule:
    rule_id: str
    context_bucket: str
    playbook: str
    action: str
    candidate_or_family: str


def _load_rules(path: Path) -> list[Rule]:
    df = pd.read_csv(path)
    req = {"rule_id", "context_bucket", "playbook", "action", "candidate_or_family"}
    miss = sorted(req - set(df.columns))
    if miss:
        raise ValueError(f"offline_router_rule_design missing columns: {miss}")
    rules: list[Rule] = []
    for _, r in df.iterrows():
        rules.append(
            Rule(
                rule_id=str(r["rule_id"]),
                context_bucket=str(r["context_bucket"]),
                playbook=str(r["playbook"]),
                action=str(r["action"]),
                candidate_or_family=str(r["candidate_or_family"]),
            )
        )
    return rules


def _apply_rules(df: pd.DataFrame, *, rules: list[Rule], diagnostic_id: str) -> pd.Series:
    """
    Returns boolean keep mask for a named diagnostic.
    """
    if df.empty:
        return pd.Series([], dtype=bool)
    # Baseline: keep all
    if diagnostic_id == "baseline_all_trades":
        return pd.Series([True] * len(df), index=df.index)

    # Very simple rule-based filters. These are research-only and intentionally conservative:
    # - avoid_context_removed: drop trades whose context_bucket is one of the "avoid" buckets
    # - preferred_or_neutral_only: drop trades in avoid buckets + drop explicit downweight buckets
    avoid_buckets = {"trend_short_diagnostic"}
    downweight_buckets = {"unknown_mixed", "high_chop", "late_climax"}
    ctx = df.get("context_bucket", pd.Series(["unknown_mixed"] * len(df), index=df.index)).astype(str)

    if diagnostic_id == "avoid_context_removed":
        return ~ctx.isin(sorted(avoid_buckets))
    if diagnostic_id == "preferred_or_neutral_only":
        return ~ctx.isin(sorted(avoid_buckets | downweight_buckets))
    if diagnostic_id == "gap_downweight_unknown_mixed":
        is_gap = df.get("candidate_id", pd.Series("", index=df.index)).astype(str).eq("GAP_ACCEPTANCE_FAILURE_001")
        return ~(is_gap & ctx.eq("unknown_mixed"))
    if diagnostic_id == "late_climax_trend_chase_removed":
        is_pa = df.get("candidate_id", pd.Series("", index=df.index)).astype(str).eq("PA_BUY_SELL_CLOSE_TREND_003")
        return ~(is_pa & ctx.eq("late_climax"))
    if diagnostic_id == "high_chop_trend_chase_removed":
        is_pa = df.get("candidate_id", pd.Series("", index=df.index)).astype(str).eq("PA_BUY_SELL_CLOSE_TREND_003")
        return ~(is_pa & ctx.eq("high_chop"))
    if diagnostic_id == "context_fit_preferred_only":
        # Use rule design as a whitelist for (bucket,candidate) prefer; otherwise keep if neutral.
        prefer_pairs: set[tuple[str, str]] = set()
        for ru in rules:
            if ru.action != "prefer":
                continue
            if ru.candidate_or_family in ("ALL", "all"):
                continue
            prefer_pairs.add((ru.context_bucket, ru.candidate_or_family))
        cid = df.get("candidate_id", pd.Series("", index=df.index)).astype(str)
        # keep only those explicitly preferred when bucket not unknown_mixed
        keep = []
        for b, c in zip(ctx.tolist(), cid.tolist(), strict=False):
            if b in ("unknown_mixed",):
                keep.append(True)
            else:
                keep.append((b, c) in prefer_pairs)
        return pd.Series(keep, index=df.index, dtype=bool)

    raise ValueError(f"unknown diagnostic_id: {diagnostic_id}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run offline router diagnostics v1 (aggregate-only).")
    p.add_argument("--playbook-root", required=True)
    p.add_argument("--context-replay-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--local-panel", required=True)
    p.add_argument("--aggregate-only", action="store_true", default=False)
    args = p.parse_args(argv)

    playbook_root = Path(args.playbook_root)
    replay_root = Path(args.context_replay_root)
    out = Path(args.output_root)
    panel_path = Path(args.local_panel)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    rules_path = playbook_root / "router_design_v1" / "offline_router_rule_design.csv"
    cfg_path = playbook_root / "router_design_v1" / "router_v1_config_draft.yaml"
    rules = _load_rules(rules_path)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    panel = pd.read_csv(panel_path)
    if panel.empty:
        raise RuntimeError("local panel is empty")

    diagnostics = [
        "baseline_all_trades",
        "avoid_context_removed",
        "preferred_or_neutral_only",
        "gap_downweight_unknown_mixed",
        "late_climax_trend_chase_removed",
        "high_chop_trend_chase_removed",
        "context_fit_preferred_only",
    ]

    baseline_mask = _apply_rules(panel, rules=rules, diagnostic_id="baseline_all_trades")
    base_df = panel[baseline_mask].copy()
    base_m = _summary_metrics(base_df)

    rows = []
    by_profile_parts = []
    by_window_parts = []
    by_context_parts = []
    weak_parts = []

    for did in diagnostics:
        mask = _apply_rules(panel, rules=rules, diagnostic_id=did)
        sub = panel[mask].copy()
        met = _summary_metrics(sub)
        row = {"diagnostic_id": did, **met}
        if did != "baseline_all_trades":
            row["delta_total_r_vs_baseline"] = float(row["total_r"]) - float(base_m["total_r"])
            bdd = base_m.get("max_dd_r_proxy")
            mdd = row.get("max_dd_r_proxy")
            row["delta_max_dd_r_proxy_vs_baseline"] = (float(mdd) - float(bdd)) if (bdd is not None and mdd is not None) else None
            row["trade_count_retention"] = float(row["trades"] / base_m["trades"]) if base_m["trades"] else None
        else:
            row["delta_total_r_vs_baseline"] = 0.0
            row["delta_max_dd_r_proxy_vs_baseline"] = 0.0
            row["trade_count_retention"] = 1.0
        rows.append(row)

        # Breakdowns
        if "profile_id" in sub.columns:
            g = sub.groupby("profile_id", dropna=False)
            for pid, gg in g:
                by_profile_parts.append({"diagnostic_id": did, "profile_id": pid, **_summary_metrics(gg)})
        if "window" in sub.columns:
            g = sub.groupby("window", dropna=False)
            for w, gg in g:
                by_window_parts.append({"diagnostic_id": did, "window": w, **_summary_metrics(gg)})
        if "context_bucket" in sub.columns:
            g = sub.groupby("context_bucket", dropna=False)
            for b, gg in g:
                by_context_parts.append({"diagnostic_id": did, "context_bucket": b, **_summary_metrics(gg)})
        # weak-period effects (quarter totals)
        d2 = _period_cols(sub)
        q = d2.groupby("period_quarter", dropna=False)["r_multiple"].sum().reset_index()
        q.insert(0, "diagnostic_id", did)
        weak_parts.append(q[q["period_quarter"].isin(["2025Q1", "2022Q4", "2023Q3"])].copy())

    res = pd.DataFrame(rows)
    _write_csv(res, out / "router_filter_results.csv")
    _write_csv(pd.DataFrame(by_profile_parts), out / "router_by_profile.csv")
    _write_csv(pd.DataFrame(by_window_parts), out / "router_by_window.csv")
    _write_csv(pd.DataFrame(by_context_parts), out / "router_by_context.csv")
    if weak_parts:
        _write_csv(pd.concat(weak_parts, ignore_index=True), out / "router_weak_period_effect.csv")

    # Minimal readable markdown
    top = res.sort_values("delta_total_r_vs_baseline", ascending=False).head(6)
    lines = [
        "# router_diagnostics_summary (v1)",
        "",
        f"- mode: `{cfg.get('mode')}` (draft config; `enabled: {cfg.get('enabled')}`)",
        f"- local panel: `{panel_path.as_posix()}` (local-only dependency)",
        "",
        "## Filters tested",
        "",
    ]
    for did in diagnostics:
        lines.append(f"- `{did}`")
    lines += [
        "",
        "## Top deltas vs baseline (by total_r)",
        "",
        _df_to_md_table(top, max_rows=10),
        "",
        "Notes:",
        "- `max_dd_r_proxy` is a **sequence proxy** computed from cumulative R sorted by `signal_ts_utc` (not a precise equity curve with capital constraints).",
        "- This script does **not** change combiner behavior; it only filters the already-generated trade list.",
        "",
    ]
    _write_md(out / "router_diagnostics_summary.md", lines)
    _write_md(out / "router_filter_results.md", ["# router_filter_results", "", _df_to_md_table(res, max_rows=50), ""])

    # key findings stub (filled by later bundle)
    _write_csv(
        pd.DataFrame(
            [
                {
                    "finding_id": "F001",
                    "finding": "See router_filter_results.* for baseline vs filtered deltas.",
                    "status": "DRAFT",
                }
            ]
        ),
        out / "router_key_findings.csv",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

