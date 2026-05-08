"""Compare multiple mini-WFO run roots and write a compact summary table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def _md_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc if isinstance(doc, dict) else {}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def _monthly_stats(monthly_csv: Path) -> dict[str, Any]:
    if not monthly_csv.is_file():
        return {}
    df = pd.read_csv(monthly_csv)
    if df.empty or "total_r" not in df.columns:
        return {}
    df = df.copy()
    df["total_r"] = df["total_r"].astype(float)
    worst = df.sort_values("total_r", ascending=True).iloc[0]
    pos_ratio = float((df["total_r"] > 0).mean())
    abs_sum = float(df["total_r"].abs().sum()) or 1.0
    conc = float(df["total_r"].abs().max()) / abs_sum
    return {
        "worst_month": str(worst.get("period", "")),
        "worst_month_r": float(worst["total_r"]),
        "positive_month_ratio": pos_ratio,
        "monthly_concentration_ratio": conc,
    }


def _decision_from_summary(summary_md: Path) -> str:
    if not summary_md.is_file():
        return ""
    txt = summary_md.read_text(encoding="utf-8", errors="replace")
    for key in ("PASS", "CAUTION", "FAIL"):
        if f"**{key}**" in txt:
            return key
    return ""


def _cost_lookup(cost_csv: Path, slip: float) -> float | None:
    if not cost_csv.is_file():
        return None
    df = pd.read_csv(cost_csv)
    if df.empty or "slippage_per_share" not in df.columns or "total_r" not in df.columns:
        return None
    m = (df["slippage_per_share"].astype(float) - float(slip)).abs() < 1e-9
    sub = df[m]
    if len(sub) == 0:
        return None
    return float(sub.iloc[0]["total_r"])


def _extract_selected_candidate_set_from_decision(decision_md: Path) -> str:
    """Parse selection_decision.md for '- Selected candidate_set: **X**'."""
    if not decision_md.is_file():
        return ""
    txt = decision_md.read_text(encoding="utf-8", errors="replace")
    marker = "- Selected candidate_set:"
    for line in txt.splitlines():
        if marker in line:
            # e.g. "- Selected candidate_set: **failed_gap**"
            if "**" in line:
                parts = line.split("**")
                if len(parts) >= 3:
                    return str(parts[1]).strip()
            return line.split(marker, 1)[1].strip().strip("*").strip()
    return ""


def _infer_candidate_set_from_ids(candidate_ids: list[str]) -> str:
    """Infer a best-effort candidate_set label from candidate IDs (fallback only)."""
    ids = [str(x) for x in candidate_ids if str(x).strip()]
    has_failed = any("FAILED_ORB" in x for x in ids)
    has_gap = any("GAP_ACCEPTANCE_FAILURE" in x for x in ids)
    has_prior = any("PRIOR_DAY_LEVEL_TRAP" in x for x in ids)

    if has_failed and has_gap and not has_prior:
        return "failed_gap"
    if has_gap and not has_failed and not has_prior:
        return "gap_only"
    if has_failed and not has_gap and not has_prior:
        return "failed_only"
    if has_prior and not has_failed and not has_gap:
        return "prior_day_only"
    if has_failed and has_gap and has_prior:
        return "trap_trio"
    return ""


def validate_selected_system_consistency(*, candidate_set: str, candidate_ids: list[str]) -> str:
    """Return warning string if candidate_set and candidate_ids appear inconsistent."""
    inf = _infer_candidate_set_from_ids(candidate_ids)
    # Treat refined_* candidate sets as aliases of the base labels.
    cset = str(candidate_set or "")
    if cset.startswith("refined_"):
        if cset.endswith("_gap_only"):
            cset = "gap_only"
        elif cset.endswith("_failed_only"):
            cset = "failed_only"
        elif cset.endswith("_failed_gap"):
            cset = "failed_gap"
    else:
        cset = candidate_set
    if not candidate_set:
        return "missing_selected_candidate_set"
    if inf and cset and inf != cset:
        return f"mismatch_ids_vs_set inferred={inf}"
    return ""


def summarize_root(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen = _read_yaml(root / "frozen_system" / "selected_frozen_system.yaml")
    src = frozen.get("source") or {}
    train = {"start": src.get("train_start"), "end": src.get("train_end")}
    cand_ids = list(frozen.get("candidate_ids") or [])

    test_metrics = _read_json(root / "test" / "metrics.json")
    test_cost = root / "test" / "cost_stress.csv"
    test_monthly = root / "test" / "test_monthly_breakdown.csv"
    if not test_monthly.is_file():
        test_monthly = root / "test" / "monthly_breakdown.csv"

    # Candidate-set extraction order:
    # 1) selection_decision.md (authoritative for what was selected)
    # 2) selection_audit.json (explicit selected_candidate_set)
    # 3) fallback inference from candidate_ids
    decision_set = _extract_selected_candidate_set_from_decision(root / "frozen_system" / "selection_decision.md")
    sel_audit = _read_json(root / "selection_audit.json")
    audit_set = str(sel_audit.get("selected_candidate_set") or "").strip()
    inferred_set = _infer_candidate_set_from_ids(cand_ids)
    selected_candidate_set = decision_set or audit_set or inferred_set

    # Report what the top train behavior row is (for debugging / mismatch warnings).
    train_bh = _read_csv(root / "train_layer2_behavior_unique.csv")
    top_behavior_set = (
        str(train_bh.iloc[0]["candidate_set"]) if len(train_bh) and "candidate_set" in train_bh.columns else ""
    )

    # Train cost stress @ 0.02 (first unique_rank if available).
    train_cost002 = None
    train_cs = _read_csv(root / "train_layer2_cost_stress.csv")
    if len(train_cs) and "slippage_per_share" in train_cs.columns and "total_r" in train_cs.columns:
        m = (train_cs["slippage_per_share"].astype(float) - 0.02).abs() < 1e-9
        if m.any():
            train_cost002 = float(train_cs[m].iloc[0]["total_r"])

    md_stats = _monthly_stats(test_monthly)

    strat_primary = sel_audit.get("strategy_universe_layer1") or []
    strat_diag = sel_audit.get("optional_diagnostics_layer1") or []
    strategies_used = ",".join([*map(str, strat_primary), *map(str, strat_diag)])

    warning = validate_selected_system_consistency(candidate_set=selected_candidate_set, candidate_ids=cand_ids)
    if top_behavior_set and selected_candidate_set and top_behavior_set != selected_candidate_set:
        warning = (warning + "; " if warning else "") + f"top_behavior_set={top_behavior_set}"

    return {
        "run_id": root.name,
        "train_start": train["start"],
        "train_end": train["end"],
        "test_start": "2025-01-01",
        "test_end": "2026-04-30",
        "strategies_used": strategies_used,
        "selected_candidate_set": selected_candidate_set,
        "selected_candidate_ids": ",".join(cand_ids),
        "train_total_r": (frozen.get("selection_metrics_train") or {}).get("total_r"),
        "train_pf_r": (frozen.get("selection_metrics_train") or {}).get("profit_factor_r")
        or (frozen.get("selection_metrics_train") or {}).get("profit_factor"),
        "train_maxdd_r": (frozen.get("selection_metrics_train") or {}).get("max_drawdown_r"),
        "train_0_02_total_r": train_cost002,
        "test_trades": test_metrics.get("trades"),
        "test_total_r": test_metrics.get("total_r"),
        "test_pf": test_metrics.get("profit_factor"),
        "test_pf_r": test_metrics.get("profit_factor_r"),
        "test_maxdd_r": test_metrics.get("max_drawdown_r"),
        "test_0_02_total_r": _cost_lookup(test_cost, 0.02),
        "test_0_03_total_r": _cost_lookup(test_cost, 0.03),
        **md_stats,
        "decision": _decision_from_summary(root / "mini_wfo_summary.md"),
        "warnings": warning,
    }


def write_outputs(roots: list[Path], output_md: Path) -> tuple[Path, Path]:
    rows = [summarize_root(r) for r in roots]
    df = pd.DataFrame(rows)
    out_csv = output_md.with_suffix(".csv")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Simple aggregate interpretation for the comparison report.
    def _fmt(x: Any) -> str:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        if isinstance(x, float):
            return f"{x:.4f}"
        return str(x)

    lines = ["## Summary", ""]
    for _, r in df.iterrows():
        lines.append(
            f"- **{r['run_id']}**: set=`{r['selected_candidate_set']}` "
            f"test_total_r={_fmt(r.get('test_total_r'))} PF_R={_fmt(r.get('test_pf_r'))} "
            f"slip0.02={_fmt(r.get('test_0_02_total_r'))} decision={r.get('decision')}"
            + (f" (warnings: {r.get('warnings')})" if str(r.get("warnings") or "").strip() else "")
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- v2A did **not** improve robustness vs v1 (it still selects `gap_only`).",
            "- v2B selected `failed_gap` but failed forward (PF_R < 1 and negative R).",
            "- If all variants are cost-fragile or negative, full WFO remains **blocked**; next step is strategy-family refinement.",
            "",
        ]
    )

    md = [
        "# Mini-WFO comparison (v1 / v2A / v2B)",
        "",
        _md_table(df),
        "",
        *lines,
        "## Interpretation prompts",
        "",
        "1. Did broader opening/trap (v2A) improve robustness vs v1?",
        "2. Did longer training (v2B) improve robustness vs v1?",
        "3. Did the selected candidate_set change?",
        "4. Did any variant survive 0.02 slippage on test?",
        "",
    ]
    output_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_csv, output_md


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare mini-WFO results roots.")
    p.add_argument("--roots", nargs="+", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)

    roots = [Path(x) for x in args.roots]
    out_md = Path(args.output)
    if not out_md.is_absolute():
        out_md = Path.cwd() / out_md
    write_outputs(roots, out_md)
    print(f"Wrote {out_md} and {out_md.with_suffix('.csv')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

