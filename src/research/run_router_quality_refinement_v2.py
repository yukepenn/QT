"""
Offline router + quality refinement v2 — research-only aggregate diagnostics.

Reads local-only `trade_context_panel.csv`, writes aggregate CSV/MD under
`router_quality_refinement_v2/` (safe to commit). Does not touch combiner production code.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.router_quality_refinement_v2_lib import (  # noqa: E402
    QUALITY_THRESHOLD_SCHEMES,
    ROUTER_VARIANTS,
    SCORE_VARIANT_COLUMNS,
    add_quality_variants,
    label_quality_row,
    label_router_row,
    retention_pct,
    router_keep_mask,
    summary_metrics,
    threshold_keep_mask,
)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md_table(df: pd.DataFrame, *, max_rows: int = 40) -> str:
    if df is None or df.empty:
        return "_(empty)_"
    d = df.head(int(max_rows)).copy()
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def _router_baseline_by_profile(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pid, g in df.groupby("profile_id", dropna=False):
        out[str(pid)] = summary_metrics(g)
    return out


def run_router_mode(df: pd.DataFrame, out_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    scored = add_quality_variants(df)
    baselines = _router_baseline_by_profile(df)
    rows: list[dict[str, Any]] = []
    by_win: list[dict[str, Any]] = []
    by_ctx: list[dict[str, Any]] = []
    weak_rows: list[dict[str, Any]] = []
    ret_rows: list[dict[str, Any]] = []

    for variant in ROUTER_VARIANTS:
        try:
            mask = router_keep_mask(df, variant, scored_for_proxy=scored)
        except KeyError:
            continue
        filt = df.loc[mask].copy()
        for pid, g in filt.groupby("profile_id", dropna=False):
            pid_s = str(pid)
            base = baselines.get(pid_s, summary_metrics(pd.DataFrame()))
            m = summary_metrics(g)
            base_n = int(base["trades"])
            ret = retention_pct(int(m["trades"]), base_n) if base_n else 0.0
            d_pf2: float | None = None
            if m["pf_r"] is not None and base["pf_r"] is not None:
                if not math.isinf(float(m["pf_r"])) and not math.isinf(float(base["pf_r"])):
                    d_pf2 = float(m["pf_r"]) - float(base["pf_r"])

            d_dd = None
            if m["max_dd_r_proxy"] is not None and base["max_dd_r_proxy"] is not None:
                d_dd = float(m["max_dd_r_proxy"]) - float(base["max_dd_r_proxy"])
            d_tr = float(m["total_r"] - base["total_r"])
            wb = base.get("weak_period_total_r")
            wv = m.get("weak_period_total_r")
            d_wk = None
            if wb is not None and wv is not None:
                d_wk = float(wv) - float(wb)
            lab = label_router_row(
                retention=ret,
                delta_pf=d_pf2,
                delta_dd=d_dd,
                delta_weak_r=d_wk,
                delta_total_r=d_tr,
                profile_id=pid_s,
            )
            rows.append(
                {
                    "profile_id": pid_s,
                    "variant": variant,
                    "total_r": m["total_r"],
                    "trades": m["trades"],
                    "retention_pct": ret,
                    "avg_r": m["avg_r"],
                    "PF_R": m["pf_r"],
                    "win_rate": m["win_rate"],
                    "maxDD_proxy": m["max_dd_r_proxy"],
                    "worst_month": m["worst_month_r"],
                    "worst_quarter": m["worst_quarter_r"],
                    "2025Q1_total_r": m["2025Q1_total_r"],
                    "2022Q4_total_r": m["2022Q4_total_r"],
                    "2023Q3_total_r": m["2023Q3_total_r"],
                    "delta_total_r_vs_baseline": d_tr,
                    "delta_pf_vs_baseline": d_pf2,
                    "delta_maxDD_proxy_vs_baseline": d_dd,
                    "weak_period_delta_r": d_wk,
                    "label": lab,
                }
            )
            ret_rows.append({"profile_id": pid_s, "variant": variant, "retention_pct": ret, "trades_kept": m["trades"], "trades_baseline": base_n})
            weak_rows.append(
                {
                    "profile_id": pid_s,
                    "variant": variant,
                    "weak_period_baseline_r": wb,
                    "weak_period_variant_r": wv,
                    "weak_period_delta_r": d_wk,
                }
            )
            if "window" in g.columns:
                for wn, gw in g.groupby("window", dropna=False):
                    sm = summary_metrics(gw)
                    by_win.append({"profile_id": pid_s, "variant": variant, "window": str(wn), **{k: sm[k] for k in sm if k != "weak_period_trades"}})
            if "context_bucket" in g.columns:
                for cx, gc in g.groupby("context_bucket", dropna=False):
                    sm = summary_metrics(gc)
                    by_ctx.append({"profile_id": pid_s, "variant": variant, "context_bucket": str(cx), **{k: sm[k] for k in sm if k != "weak_period_trades"}})

    res = pd.DataFrame(rows)
    _write_csv(res, out_root / "router_v2" / "router_v2_results.csv")
    _write_csv(pd.DataFrame(by_win), out_root / "router_v2" / "router_v2_by_window.csv")
    _write_csv(pd.DataFrame(by_ctx), out_root / "router_v2" / "router_v2_by_context.csv")
    _write_csv(pd.DataFrame(weak_rows), out_root / "router_v2" / "router_v2_weak_period_effect.csv")
    _write_csv(pd.DataFrame(ret_rows), out_root / "router_v2" / "router_v2_trade_retention.csv")

    promising = int((res["label"] == "ROUTER_V2_PROMISING").sum()) if len(res) else 0
    prom = res[res["label"] == "ROUTER_V2_PROMISING"].copy()
    for c in ("delta_pf_vs_baseline", "delta_maxDD_proxy_vs_baseline"):
        if c in prom.columns:
            prom[c] = prom[c].fillna(0.0)
    best = prom.sort_values(["delta_pf_vs_baseline", "delta_maxDD_proxy_vs_baseline"], ascending=[False, False]).head(3)
    lines = [
        "# router_v2_summary",
        "",
        "## Top promising rows",
        "",
        _md_table(best),
        "",
        "## Counts by label",
        "",
        _md_table(res.groupby("label", dropna=False).size().reset_index(name="n")),
    ]
    _write_md(out_root / "router_v2" / "router_v2_summary.md", lines)
    _write_md(
        out_root / "router_v2" / "router_v2_results.md",
        ["# router_v2_results", "", _md_table(res.head(50)), "", f"_Total rows: {len(res)}_"],
    )
    _write_csv(res, out_root / "router_v2" / "router_v2_by_profile.csv")
    meta = {"promising_router_rows": promising}
    return res, meta


def run_quality_mode(df: pd.DataFrame, out_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    scored = add_quality_variants(df)
    baselines = _router_baseline_by_profile(df)
    rows: list[dict[str, Any]] = []
    by_win: list[dict[str, Any]] = []
    by_ctx: list[dict[str, Any]] = []
    weak_rows: list[dict[str, Any]] = []
    cov_rows: list[dict[str, Any]] = []

    for sv, col in SCORE_VARIANT_COLUMNS.items():
        if col not in scored.columns:
            continue
        cov_rows.append({"score_variant": sv, "score_column": col, "non_null_rows": int(scored[col].notna().sum())})
        for scheme in QUALITY_THRESHOLD_SCHEMES:
            try:
                km = threshold_keep_mask(scored, col, scheme)
            except KeyError:
                continue
            sub = scored.loc[km].copy()
            diag = scheme.startswith("percentile") or scheme.startswith("bottom_cut")
            for pid, g in sub.groupby("profile_id", dropna=False):
                pid_s = str(pid)
                base = baselines.get(pid_s, summary_metrics(pd.DataFrame()))
                base_n = int(base["trades"])
                m = summary_metrics(g)
                ret = retention_pct(int(m["trades"]), base_n) if base_n else 0.0
                d_pf2: float | None = None
                if m["pf_r"] is not None and base["pf_r"] is not None:
                    if not math.isinf(float(m["pf_r"])) and not math.isinf(float(base["pf_r"])):
                        d_pf2 = float(m["pf_r"]) - float(base["pf_r"])
                d_dd = None
                if m["max_dd_r_proxy"] is not None and base["max_dd_r_proxy"] is not None:
                    d_dd = float(m["max_dd_r_proxy"]) - float(base["max_dd_r_proxy"])
                d_tr = float(m["total_r"] - base["total_r"])
                wb = base.get("weak_period_total_r")
                wv = m.get("weak_period_total_r")
                d_wk = None
                if wb is not None and wv is not None:
                    d_wk = float(wv) - float(wb)
                lab = label_quality_row(
                    retention=ret,
                    delta_pf=d_pf2,
                    delta_dd=d_dd,
                    delta_weak_r=d_wk,
                    delta_total_r=d_tr,
                    scheme=scheme,
                )
                rows.append(
                    {
                        "score_variant": sv,
                        "threshold_scheme": scheme,
                        "in_sample_diagnostic": bool(diag),
                        "profile_id": pid_s,
                        "total_r": m["total_r"],
                        "trades": m["trades"],
                        "retention_pct": ret,
                        "avg_r": m["avg_r"],
                        "PF_R": m["pf_r"],
                        "win_rate": m["win_rate"],
                        "maxDD_proxy": m["max_dd_r_proxy"],
                        "worst_month": m["worst_month_r"],
                        "worst_quarter": m["worst_quarter_r"],
                        "2025Q1": m["2025Q1_total_r"],
                        "2022Q4": m["2022Q4_total_r"],
                        "2023Q3": m["2023Q3_total_r"],
                        "delta_vs_baseline": d_tr,
                        "delta_pf_vs_baseline": d_pf2,
                        "delta_maxDD_proxy_vs_baseline": d_dd,
                        "weak_period_delta_r": d_wk,
                        "label": lab,
                    }
                )
                weak_rows.append(
                    {
                        "score_variant": sv,
                        "threshold_scheme": scheme,
                        "profile_id": pid_s,
                        "weak_period_delta_r": d_wk,
                    }
                )
                if "window" in g.columns:
                    for wn, gw in g.groupby("window", dropna=False):
                        sm = summary_metrics(gw)
                        by_win.append(
                            {
                                "score_variant": sv,
                                "threshold_scheme": scheme,
                                "profile_id": pid_s,
                                "window": str(wn),
                                **{k: sm[k] for k in sm if k not in ("weak_period_total_r", "weak_period_trades")},
                            }
                        )
                if "context_bucket" in g.columns:
                    for cx, gc in g.groupby("context_bucket", dropna=False):
                        sm = summary_metrics(gc)
                        by_ctx.append(
                            {
                                "score_variant": sv,
                                "threshold_scheme": scheme,
                                "profile_id": pid_s,
                                "context_bucket": str(cx),
                                **{k: sm[k] for k in sm if k not in ("weak_period_total_r", "weak_period_trades")},
                            }
                        )

    res = pd.DataFrame(rows)
    qdir = out_root / "quality_v2_refined"
    _write_csv(res, qdir / "quality_variant_results.csv")
    _write_csv(res, qdir / "quality_threshold_results.csv")
    _write_csv(pd.DataFrame(by_win), qdir / "quality_by_window.csv")
    _write_csv(pd.DataFrame(by_ctx), qdir / "quality_by_context.csv")
    _write_csv(pd.DataFrame(weak_rows), qdir / "quality_weak_period_effect.csv")
    _write_csv(pd.DataFrame(cov_rows), qdir / "quality_component_coverage.csv")

    promising = int((res["label"] == "QUALITY_V2_PROMISING").sum()) if len(res) else 0
    promq = res[res["label"] == "QUALITY_V2_PROMISING"].copy()
    if len(promq) and "delta_pf_vs_baseline" in promq.columns:
        promq["delta_pf_vs_baseline"] = promq["delta_pf_vs_baseline"].fillna(0.0)
    best = promq.sort_values(["delta_pf_vs_baseline", "retention_pct"], ascending=[False, False]).head(8)
    lines = [
        "# quality_refinement_summary",
        "",
        "Percentile and bottom-cut schemes are labeled `in_sample_diagnostic=True` (thresholds derived on the same panel used for scoring).",
        "",
        "## Top promising rows",
        "",
        _md_table(best),
        "",
        "## Counts by label",
        "",
        _md_table(res.groupby("label", dropna=False).size().reset_index(name="n")),
    ]
    _write_md(qdir / "quality_refinement_summary.md", lines)
    _write_md(qdir / "quality_variant_results.md", ["# quality_variant_results", "", _md_table(res.head(40)), "", f"_Total rows: {len(res)}_"])
    _write_csv(res, qdir / "quality_by_profile.csv")
    meta = {"promising_quality_rows": promising}
    return res, meta


def _combined_masks(df: pd.DataFrame, scored: pd.DataFrame, router_variant: str, qcol: str, qscheme: str) -> pd.Series:
    rm = router_keep_mask(df, router_variant, scored_for_proxy=scored)
    qm = threshold_keep_mask(scored, qcol, qscheme)
    return rm & qm


def run_combined_mode(df: pd.DataFrame, out_root: Path, router_res: pd.DataFrame, quality_res: pd.DataFrame) -> None:
    cg = out_root / "combined_light_guards"
    r_ok = router_res[router_res["label"] == "ROUTER_V2_PROMISING"]
    q_ok = quality_res[quality_res["label"] == "QUALITY_V2_PROMISING"]
    if r_ok.empty and q_ok.empty:
        _write_md(cg / "not_run_reason.md", ["# combined_light_guards", "", "No `ROUTER_V2_PROMISING` or `QUALITY_V2_PROMISING` rows in v2 aggregate pass — combined tests not forced."])
        return

    scored = add_quality_variants(df)
    baselines = _router_baseline_by_profile(df)

    def best_router() -> str:
        if r_ok.empty:
            return "baseline_all"
        t = r_ok.sort_values(["delta_pf_vs_baseline", "retention_pct"], ascending=[False, False]).iloc[0]
        return str(t["variant"])

    rv = best_router()
    if rv == "baseline_all":
        rv = "gap_context_guard"

    tests = [
        ("best_router_v2 + bottom_20_quality_cut", rv, "original_v2_score", "bottom_cut_20"),
        ("best_router_v2 + relaxed_A_B", rv, "original_v2_score", "relaxed_AB"),
        ("repeat_after_loss_guard + bottom_20_quality_cut", "repeat_after_loss_guard", "original_v2_score", "bottom_cut_20"),
        ("gap_context_guard + repeat_after_loss_guard", "gap_context_guard", "original_v2_score", "relaxed_AB"),
        ("late_climax_guard + relaxed_A_B", "late_climax_guard", "original_v2_score", "relaxed_AB"),
    ]
    rows: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    for name, rvar, sv, th in tests:
        qcol = SCORE_VARIANT_COLUMNS.get(sv, "quality_score_v2")
        mask = _combined_masks(df, scored, rvar, qcol, th)
        filt = scored.loc[mask].copy()
        for pid, g in filt.groupby("profile_id", dropna=False):
            pid_s = str(pid)
            base = baselines.get(pid_s, summary_metrics(pd.DataFrame()))
            m = summary_metrics(g)
            base_n = int(base["trades"])
            ret = retention_pct(int(m["trades"]), base_n) if base_n else 0.0
            d_pf2 = None
            if m["pf_r"] is not None and base["pf_r"] is not None:
                if not math.isinf(float(m["pf_r"])) and not math.isinf(float(base["pf_r"])):
                    d_pf2 = float(m["pf_r"]) - float(base["pf_r"])
            d_dd = None
            if m["max_dd_r_proxy"] is not None and base["max_dd_r_proxy"] is not None:
                d_dd = float(m["max_dd_r_proxy"]) - float(base["max_dd_r_proxy"])
            d_tr = float(m["total_r"] - base["total_r"])
            wb = base.get("weak_period_total_r")
            wv = m.get("weak_period_total_r")
            d_wk = float(wv) - float(wb) if wb is not None and wv is not None else None
            rows.append(
                {
                    "combo_name": name,
                    "router_variant": rvar,
                    "quality_variant": sv,
                    "threshold_scheme": th,
                    "profile_id": pid_s,
                    "total_r": m["total_r"],
                    "trades": m["trades"],
                    "retention_pct": ret,
                    "PF_R": m["pf_r"],
                    "maxDD_proxy": m["max_dd_r_proxy"],
                    "delta_total_r_vs_baseline": d_tr,
                    "delta_pf_vs_baseline": d_pf2,
                    "delta_maxDD_proxy_vs_baseline": d_dd,
                }
            )
            weak.append({"combo_name": name, "profile_id": pid_s, "weak_period_delta_r": d_wk})

    _write_csv(pd.DataFrame(rows), cg / "combined_guard_results.csv")
    _write_csv(pd.DataFrame(rows), cg / "combined_guard_by_profile.csv")
    _write_csv(pd.DataFrame(weak), cg / "combined_guard_weak_period_effect.csv")
    _write_md(cg / "combined_guard_results.md", ["# combined_guard_results", "", _md_table(pd.DataFrame(rows))])
    _write_md(cg / "combined_guard_summary.md", ["# combined_guard_summary", "", "- Combined masks = router keep AND quality threshold keep.", "", _md_table(pd.DataFrame(rows).head(20))])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Router + quality refinement v2 (offline aggregates).")
    p.add_argument("--local-panel", required=True, type=Path)
    p.add_argument("--playbook-root", required=True, type=Path)
    p.add_argument("--v1-root", required=True, type=Path)
    p.add_argument("--output-root", required=True, type=Path)
    p.add_argument("--mode", choices=["router", "quality", "both"], default="both")
    p.add_argument("--aggregate-only", action="store_true", help="Ignored compatibility flag (always aggregate-only).")
    args = p.parse_args(argv)

    panel_path = args.local_panel
    if not panel_path.is_file():
        raise SystemExit(f"local panel not found: {panel_path}")

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(panel_path)
    if df.empty:
        raise SystemExit("panel empty")

    router_res = pd.DataFrame()
    q_res = pd.DataFrame()
    r_meta: dict[str, Any] = {}
    q_meta: dict[str, Any] = {}

    if args.mode in ("router", "both"):
        router_res, r_meta = run_router_mode(df, out_root)
    if args.mode in ("quality", "both"):
        q_res, q_meta = run_quality_mode(df, out_root)
    if args.mode == "both" and len(router_res) and len(q_res):
        run_combined_mode(df, out_root, router_res, q_res)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
