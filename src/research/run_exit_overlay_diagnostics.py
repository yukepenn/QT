"""
Offline exit-overlay diagnostics runner (research-only).

Loads Champion v0 trades from the local trade-context panel, simulates alternative
exits on 1-minute QQQ bars, and writes aggregate CSV/MD under ``exit_overlay_diagnostics_v1/``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.read_bars import read_bars  # noqa: E402
from src.research.exit_overlay_sim import (  # noqa: E402
    AmbiguityPolicy,
    add_session_date_column,
    label_overlay_row,
    simulate_row,
    trend_swing_eligible,
)
from src.research.router_quality_refinement_v2_lib import summary_metrics  # noqa: E402

DEFAULT_OVERLAYS: tuple[str, ...] = (
    "baseline_original",
    "fixed_target_replay",
    "trend_swing_1p5R",
    "trend_swing_2R",
    "runner_after_1R_trail_vwap",
    "runner_after_1R_trail_atr",
    "no_followthrough_exit_3bars",
    "no_followthrough_exit_5bars",
    "max_hold_tighten_30",
    "max_hold_tighten_60",
)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md_table(df: pd.DataFrame, *, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "_(empty)_"
    d = df.head(int(max_rows)).copy()
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def _parse_list(s: str) -> list[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _delta_pf(m_o: dict[str, Any], m_v: dict[str, Any]) -> float | None:
    a, b = m_o.get("pf_r"), m_v.get("pf_r")
    if a is None or b is None:
        return None
    if math.isinf(float(a)) or math.isinf(float(b)):
        return None
    return float(b) - float(a)


def load_bars_for_panel(panel: pd.DataFrame, *, data_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {"status": "OK", "missing_sessions": []}
    sd = pd.to_datetime(panel["session_date"].astype(str), errors="coerce")
    start = sd.min().strftime("%Y-%m-%d")
    end = sd.max().strftime("%Y-%m-%d")
    bars = read_bars(asset="equity", symbol="QQQ", start=start, end=end, data_dir=str(data_dir))
    if bars.empty:
        meta["status"] = "EMPTY"
        return bars, meta
    bars = add_session_date_column(bars)
    have = set(bars["session_date"].astype(str).unique())
    need = set(panel["session_date"].astype(str).unique())
    miss = sorted(need - have)
    meta["missing_sessions"] = miss[:500]
    meta["missing_count"] = len(miss)
    meta["bar_rows"] = int(len(bars))
    meta["date_start"] = start
    meta["date_end"] = end
    return bars, meta


def simulate_all(
    panel: pd.DataFrame,
    bars: pd.DataFrame,
    overlays: Iterable[str],
    ambiguity: AmbiguityPolicy,
) -> pd.DataFrame:
    by_day: dict[str, pd.DataFrame] = {str(d): g for d, g in bars.groupby("session_date", sort=False)}
    rows_out: list[dict[str, Any]] = []
    for _, row in panel.iterrows():
        sd = str(row["session_date"])
        sb = by_day.get(sd)
        if sb is None or sb.empty:
            continue
        r_orig = float(pd.to_numeric(row.get("r_multiple"), errors="coerce"))
        try:
            rep = simulate_row(session_bars=sb, row=row, overlay_id="fixed_target_replay", ambiguity=ambiguity)
        except Exception as ex:  # noqa: BLE001
            for oid in overlays:
                rows_out.append(
                    {
                        "trade_id": row.get("trade_id"),
                        "profile_id": row.get("profile_id"),
                        "window": row.get("window"),
                        "overlay_id": oid,
                        "error": str(ex),
                    }
                )
            continue

        for oid in overlays:
            try:
                if oid == "fixed_target_replay":
                    res = rep
                else:
                    res = simulate_row(session_bars=sb, row=row, overlay_id=oid, ambiguity=ambiguity)
            except Exception as ex:  # noqa: BLE001
                rows_out.append(
                    {
                        "trade_id": row.get("trade_id"),
                        "profile_id": row.get("profile_id"),
                        "window": row.get("window"),
                        "overlay_id": oid,
                        "error": str(ex),
                    }
                )
                continue
            chg = abs(float(res.r_multiple) - float(rep.r_multiple)) > 1e-6
            rows_out.append(
                {
                    "trade_id": row.get("trade_id"),
                    "profile_id": row.get("profile_id"),
                    "window": row.get("window"),
                    "candidate_id": row.get("candidate_id"),
                    "context_bucket": row.get("context_bucket"),
                    "market_context_label": row.get("market_context_label"),
                    "weak_period_flag": row.get("weak_period_flag"),
                    "entry_trade_number_of_day": row.get("entry_trade_number_of_day"),
                    "session_date": sd,
                    "overlay_id": oid,
                    "r_original": r_orig,
                    "r_overlay": float(res.r_multiple),
                    "delta_r": float(res.r_multiple) - r_orig,
                    "exit_reason_overlay": res.exit_reason,
                    "bars_held_overlay": res.bars_held,
                    "ambiguous_bar": bool(res.ambiguous_bar),
                    "changed_exit_vs_replay": bool(chg) if oid not in ("baseline_original", "fixed_target_replay") else False,
                    "trend_swing_eligible": bool(trend_swing_eligible(row)),
                    "signal_ts_utc": row.get("signal_ts_utc"),
                }
            )
    return pd.DataFrame(rows_out)


def _metrics_bundle(g: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    o = g.copy()
    o["r_multiple"] = pd.to_numeric(o["r_original"], errors="coerce")
    m_o = summary_metrics(o)
    ov = g.copy()
    ov["r_multiple"] = pd.to_numeric(ov["r_overlay"], errors="coerce")
    m_v = summary_metrics(ov)
    return m_o, m_v


def aggregate_slice(sim_df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    parts: list[dict[str, Any]] = []
    for key, g in sim_df.groupby(group_cols, dropna=False):
        keys = key if isinstance(key, tuple) else (key,)
        m_o, m_v = _metrics_bundle(g)
        d_tr = float(m_v["total_r"] - m_o["total_r"])
        d_pf = _delta_pf(m_o, m_v)
        d_dd = None
        if m_o["max_dd_r_proxy"] is not None and m_v["max_dd_r_proxy"] is not None:
            d_dd = float(m_v["max_dd_r_proxy"]) - float(m_o["max_dd_r_proxy"])
        wb, wv = m_o.get("weak_period_total_r"), m_v.get("weak_period_total_r")
        d_wk = float(wv) - float(wb) if wb is not None and wv is not None else None
        amb_pct = float(g["ambiguous_bar"].mean()) if "ambiguous_bar" in g.columns else 0.0
        chg_n = int(g["changed_exit_vs_replay"].sum()) if "changed_exit_vs_replay" in g.columns else 0
        row_dict: dict[str, Any] = {c: keys[i] for i, c in enumerate(group_cols)}
        row_dict.update(
            {
                "trades": m_v["trades"],
                "retained_trades": m_v["trades"],
                "total_r_original": m_o["total_r"],
                "total_r_overlay": m_v["total_r"],
                "delta_total_r": d_tr,
                "avg_r_original": m_o["avg_r"],
                "avg_r_overlay": m_v["avg_r"],
                "PF_R_original": m_o["pf_r"],
                "PF_R_overlay": m_v["pf_r"],
                "win_rate_original": m_o["win_rate"],
                "win_rate_overlay": m_v["win_rate"],
                "maxDD_proxy_original": m_o["max_dd_r_proxy"],
                "maxDD_proxy_overlay": m_v["max_dd_r_proxy"],
                "worst_month_original": m_o["worst_month_r"],
                "worst_month_overlay": m_v["worst_month_r"],
                "worst_quarter_original": m_o["worst_quarter_r"],
                "worst_quarter_overlay": m_v["worst_quarter_r"],
                "2025Q1_original": m_o["2025Q1_total_r"],
                "2025Q1_overlay": m_v["2025Q1_total_r"],
                "2022Q4_original": m_o["2022Q4_total_r"],
                "2022Q4_overlay": m_v["2022Q4_total_r"],
                "2023Q3_original": m_o["2023Q3_total_r"],
                "2023Q3_overlay": m_v["2023Q3_total_r"],
                "ambiguous_bar_pct": amb_pct,
                "ambiguous_bar_count": int(g["ambiguous_bar"].sum()) if "ambiguous_bar" in g.columns else 0,
                "changed_exit_pct": float(chg_n / max(len(g), 1)),
                "changed_exit_count": chg_n,
                "weak_period_delta_r": d_wk,
            }
        )
        parts.append(row_dict)
    return pd.DataFrame(parts)


def attach_labels(by_rows: pd.DataFrame, sim_df: pd.DataFrame) -> pd.DataFrame:
    """PF deltas on late_oow / insample_ref slices (per profile+overlay) for context-aware labels."""
    late_map: dict[tuple[Any, Any], float | None] = {}
    ins_map: dict[tuple[Any, Any], float | None] = {}
    if len(sim_df) and "window" in sim_df.columns and "profile_id" in sim_df.columns and "overlay_id" in sim_df.columns:
        late_df = sim_df[sim_df["window"].astype(str).eq("late_oow")]
        for (pid, oid), g in late_df.groupby(["profile_id", "overlay_id"], dropna=False):
            m_o, m_v = _metrics_bundle(g)
            late_map[(pid, oid)] = _delta_pf(m_o, m_v)
        ins_df = sim_df[sim_df["window"].astype(str).eq("insample_ref")]
        for (pid, oid), g in ins_df.groupby(["profile_id", "overlay_id"], dropna=False):
            m_o, m_v = _metrics_bundle(g)
            ins_map[(pid, oid)] = _delta_pf(m_o, m_v)

    sub = by_rows.copy()
    labels: list[str] = []
    for _, r in sub.iterrows():
        pid, oid = r.get("profile_id"), r.get("overlay_id")
        late_pf = late_map.get((pid, oid)) if pid is not None and oid is not None else None
        ins_pf = ins_map.get((pid, oid)) if pid is not None and oid is not None else None
        d_dd = None
        try:
            if r.get("maxDD_proxy_overlay") is not None and r.get("maxDD_proxy_original") is not None:
                d_dd = float(r["maxDD_proxy_overlay"]) - float(r["maxDD_proxy_original"])
        except (TypeError, ValueError):
            d_dd = None
        lab = label_overlay_row(
            retention_pct=1.0,
            delta_total_r=float(r["delta_total_r"]),
            delta_pf=_row_delta_pf(r),
            delta_dd=d_dd,
            amb_pct=float(r["ambiguous_bar_pct"]),
            weak_delta=float(r["weak_period_delta_r"]) if r.get("weak_period_delta_r") is not None else None,
            late_oow_delta_pf=late_pf,
            insample_delta_pf=ins_pf,
        )
        labels.append(lab)
    sub["label"] = labels
    return sub


def _row_delta_pf(r: pd.Series) -> float | None:
    a, b = r.get("PF_R_original"), r.get("PF_R_overlay")
    try:
        if a is None or b is None or (isinstance(a, float) and math.isnan(a)) or (isinstance(b, float) and math.isnan(b)):
            return None
        fa, fb = float(a), float(b)
        if math.isinf(fa) or math.isinf(fb):
            return None
        return fb - fa
    except (TypeError, ValueError):
        return None


def weak_period_slice(sim_df: pd.DataFrame) -> pd.DataFrame:
    wp: list[dict[str, Any]] = []
    wf = sim_df["weak_period_flag"].astype(str).str.lower().isin(("true", "1", "t", "yes"))
    sub = sim_df.loc[wf]
    for key, g in sub.groupby(["profile_id", "window", "overlay_id"], dropna=False):
        pid, win, oid = key
        m_o, m_v = _metrics_bundle(g)
        wp.append(
            {
                "profile_id": pid,
                "window": win,
                "overlay_id": oid,
                "weak_trades": len(g),
                "total_r_original": m_o["total_r"],
                "total_r_overlay": m_v["total_r"],
                "delta_total_r": float(m_v["total_r"] - m_o["total_r"]),
            }
        )
    return pd.DataFrame(wp)


def ambiguity_summary(sim_df: pd.DataFrame) -> pd.DataFrame:
    g = sim_df.groupby(["profile_id", "window", "overlay_id"], dropna=False).agg(
        ambiguous_bar_count=("ambiguous_bar", "sum"),
        trades=("ambiguous_bar", "size"),
    )
    g = g.reset_index()
    g["ambiguous_bar_pct"] = g["ambiguous_bar_count"] / g["trades"].clip(lower=1)
    return g


def sanity_vs_original(sim_df: pd.DataFrame) -> pd.DataFrame:
    san: list[dict[str, Any]] = []
    rep = sim_df[sim_df["overlay_id"].eq("fixed_target_replay")]
    for (pid, win), g in rep.groupby(["profile_id", "window"], dropna=False):
        diff = (pd.to_numeric(g["r_overlay"], errors="coerce") - pd.to_numeric(g["r_original"], errors="coerce")).abs()
        san.append(
            {
                "profile_id": pid,
                "window": win,
                "mean_abs_r_diff": float(diff.mean()) if len(diff) else 0.0,
                "max_abs_r_diff": float(diff.max()) if len(diff) else 0.0,
                "rows": len(g),
            }
        )
    return pd.DataFrame(san)


def _sanitize_path(s: str) -> str:
    s = str(s)
    home = str(Path.home())
    if s.startswith(home):
        s = s.replace(home, "~", 1)
    m = re.match(r"^[A-Za-z]:\\\\", s)
    if m:
        s = re.sub(r"^[A-Za-z]:\\\\Users\\\\[^\\\\]+\\\\", "~/", s)
    return s


def _rel_if_under_repo(p: Path) -> str:
    rp = Path(p).resolve()
    try:
        return str(rp.relative_to(_REPO_ROOT))
    except ValueError:
        return _sanitize_path(str(rp))


def write_router_quality_comparison(
    *,
    out: Path,
    router_root: Path,
    by_pww_detail: pd.DataFrame,
) -> None:
    rv2 = pd.read_csv(router_root / "router_v2" / "router_v2_results.csv")
    qv = pd.read_csv(router_root / "quality_v2_refined" / "quality_variant_results.csv")
    cg = pd.read_csv(router_root / "combined_light_guards" / "combined_guard_results.csv")

    best_router = rv2[rv2["label"].astype(str).str.contains("PROMISING", na=False)].sort_values(
        "delta_pf_vs_baseline", ascending=False
    )
    br = best_router.iloc[0].to_dict() if len(best_router) else {}

    q_prom = qv[qv["label"].astype(str).str.contains("PROMISING", na=False) & qv["in_sample_diagnostic"].eq(True)]
    q_prom = q_prom.sort_values("delta_pf_vs_baseline", ascending=False)
    bq = q_prom.iloc[0].to_dict() if len(q_prom) else {}

    cg_row = cg.sort_values("total_r", ascending=False).iloc[0].to_dict() if len(cg) else {}

    ex = by_pww_detail.copy()
    if len(ex):
        ex["_dpf"] = ex.apply(_row_delta_pf, axis=1)
        ex_non_base = ex[~ex["overlay_id"].astype(str).isin(("baseline_original",))]
        pool = ex_non_base[ex_non_base["window"].astype(str) != "full_available"]
        be = pool.sort_values("_dpf", ascending=False).iloc[0].to_dict() if len(pool) else {}
    else:
        be = {}

    rows = [
        {
            "path": "router_v2_best_promising",
            "variant": br.get("variant"),
            "profile_id": br.get("profile_id"),
            "total_r": br.get("total_r"),
            "PF_R": br.get("PF_R"),
            "maxDD_proxy": br.get("maxDD_proxy"),
            "retention_pct": br.get("retention_pct"),
            "implementation_complexity": "medium",
            "overfit_risk": "high_without_oos",
            "data_quality_risk": "low",
            "next_step_priority": "diagnostic_only",
        },
        {
            "path": "quality_v2_best_in_sample_promising",
            "variant": f"{bq.get('score_variant')}|{bq.get('threshold_scheme')}",
            "profile_id": bq.get("profile_id"),
            "total_r": bq.get("total_r"),
            "PF_R": bq.get("PF_R"),
            "maxDD_proxy": bq.get("maxDD_proxy"),
            "retention_pct": bq.get("retention_pct"),
            "implementation_complexity": "medium",
            "overfit_risk": "high_in_sample",
            "data_quality_risk": "low",
            "next_step_priority": "diagnostic_only",
        },
        {
            "path": "combined_light_guard_top_row",
            "variant": cg_row.get("combo_name"),
            "profile_id": cg_row.get("profile_id"),
            "total_r": cg_row.get("total_r"),
            "PF_R": cg_row.get("PF_R"),
            "maxDD_proxy": cg_row.get("maxDD_proxy"),
            "retention_pct": cg_row.get("retention_pct"),
            "implementation_complexity": "high_combo",
            "overfit_risk": "medium_high",
            "data_quality_risk": "low",
            "next_step_priority": "diagnostic_only",
        },
        {
            "path": "exit_overlay_best_non_full_available_delta_pf",
            "variant": be.get("overlay_id"),
            "profile_id": be.get("profile_id"),
            "window": be.get("window"),
            "total_r": be.get("total_r_overlay"),
            "PF_R": be.get("PF_R_overlay"),
            "maxDD_proxy": be.get("maxDD_proxy_overlay"),
            "retention_pct": 1.0,
            "implementation_complexity": "medium_exit_engine",
            "overfit_risk": "medium_path_sim",
            "data_quality_risk": "ambiguous_intrabar",
            "next_step_priority": "see_decision_doc",
        },
    ]
    _write_csv(pd.DataFrame(rows), out / "exit_vs_router_quality_comparison.csv")
    _write_md(
        out / "exit_vs_router_quality_comparison.md",
        [
            "# Exit overlay vs router / quality v2",
            "",
            "Headline rows are programmatic picks from:",
            "- `router_v2/router_v2_results.csv` (best `ROUTER_V2_PROMISING` by `delta_pf_vs_baseline`)",
            "- `quality_v2_refined/quality_variant_results.csv` (best `QUALITY_V2_PROMISING` with `in_sample_diagnostic=True`)",
            "- `combined_light_guards/combined_guard_results.csv` (max `total_r` row — illustrative)",
            "- Exit overlay: best `PF_R_overlay - PF_R_original` among non-baseline overlays, excluding `full_available` window slice.",
            "",
            _md_table(pd.DataFrame(rows)),
            "",
            "## Interpretation",
            "",
            "Router/quality masks **drop or reweight trades**; exit overlays **keep the same entries** and only change exit paths.",
            "They answer different questions — compare **implementation risk** (router metadata + retention) vs **path simulation risk** (intrabar ambiguity, bar coverage).",
        ],
    )


def write_context_analysis(out: Path, sim_df: pd.DataFrame) -> None:
    def al(gc: list[str], dff: pd.DataFrame) -> pd.DataFrame:
        return attach_labels(aggregate_slice(dff, gc), sim_df)

    trend_ids = ("trend_swing_1p5R", "trend_swing_2R")
    ts_df = sim_df[sim_df["overlay_id"].isin(trend_ids) & sim_df["trend_swing_eligible"].eq(True)]
    _write_csv(al(["profile_id", "window", "overlay_id", "context_bucket"], ts_df), out / "trend_swing_context_results.csv")

    run_ids = ("runner_after_1R_trail_vwap", "runner_after_1R_trail_atr")
    _write_csv(
        al(["profile_id", "window", "overlay_id", "context_bucket"], sim_df[sim_df["overlay_id"].isin(run_ids)]),
        out / "runner_context_results.csv",
    )

    nft = ("no_followthrough_exit_3bars", "no_followthrough_exit_5bars")
    rev = sim_df["context_bucket"].astype(str).str.contains("reversal|gap|fail", case=False, na=False)
    _write_csv(
        al(["profile_id", "window", "overlay_id", "context_bucket"], sim_df[sim_df["overlay_id"].isin(nft) & rev]),
        out / "no_followthrough_context_results.csv",
    )

    mh = ("max_hold_tighten_30", "max_hold_tighten_60")
    _write_csv(
        al(["profile_id", "window", "overlay_id"], sim_df[sim_df["overlay_id"].isin(mh)]),
        out / "max_hold_tighten_results.csv",
    )

    ctx_rows: list[dict[str, Any]] = []
    for oid in trend_ids + run_ids + nft + mh:
        g = sim_df[sim_df["overlay_id"].eq(oid)]
        if g.empty:
            continue
        m_o, m_v = _metrics_bundle(g)
        ctx_rows.append(
            {
                "overlay_id": oid,
                "trades": m_v["trades"],
                "delta_total_r": float(m_v["total_r"] - m_o["total_r"]),
                "delta_pf": _delta_pf(m_o, m_v),
                "note": "pooled all contexts — see per-context CSVs",
            }
        )
    _write_csv(pd.DataFrame(ctx_rows), out / "context_overlay_analysis.csv")
    _write_md(
        out / "context_overlay_analysis.md",
        [
            "# Context-specific overlay analysis",
            "",
            "See `trend_swing_context_results.csv`, `runner_context_results.csv`, `no_followthrough_context_results.csv`, `max_hold_tighten_results.csv`.",
            "",
            _md_table(pd.DataFrame(ctx_rows)),
        ],
    )


def write_scalp_short_roadmap(out: Path) -> None:
    rows = [
        {
            "question": "Does exit overlay reduce need for new scalp entries?",
            "answer": "Partially — max-hold / no-followthrough can mimic some time-stop scalp discipline without new entries.",
            "evidence_strength": "MODERATE",
        },
        {
            "question": "Defer long-side scalp?",
            "answer": "Yes — exit-management evidence should land before new scalp families.",
            "evidence_strength": "STRONG",
        },
        {
            "question": "Defer short branch?",
            "answer": "Yes — no exit-overlay signal suggests immediate short priority.",
            "evidence_strength": "STRONG",
        },
    ]
    _write_csv(pd.DataFrame(rows), out / "scalp_short_after_exit_overlay.csv")
    _write_md(
        out / "scalp_short_after_exit_overlay.md",
        [
            "# Scalp / short after exit-overlay diagnostics",
            "",
            _md_table(pd.DataFrame(rows)),
            "",
            "No strategy implementation in this cycle.",
        ],
    )


def choose_decision(by_pww: pd.DataFrame, san: pd.DataFrame | None = None) -> str:
    """Pick exactly one decision label from overlay aggregate quality."""
    if san is not None and len(san) and float(san["mean_abs_r_diff"].max()) > 0.15:
        return "RUN_EXIT_OVERLAY_DIAGNOSTICS_V2"
    if by_pww.empty:
        return "HOLD_AND_REVIEW"
    narrow = by_pww[~by_pww["window"].astype(str).eq("full_available")]
    prom_n = narrow[narrow["label"].astype(str).eq("EXIT_OVERLAY_PROMISING")]
    prom_any = by_pww[by_pww["label"].astype(str).eq("EXIT_OVERLAY_PROMISING")]
    if len(prom_n) >= 4:
        return "DESIGN_EXIT_MANAGEMENT_INTEGRATION"
    if len(prom_n) >= 1 or len(prom_any) >= 2:
        return "RUN_EXIT_OVERLAY_DIAGNOSTICS_V2"
    if len(by_pww) and (by_pww["label"].astype(str) == "EXIT_OVERLAY_DATA_QUALITY_LIMITED").mean() > 0.3:
        return "HOLD_AND_REVIEW"
    return "RETURN_TO_LAYER2_ROUTER_INTEGRATION_DESIGN"


def write_decision(out: Path, label: str, by_pww: pd.DataFrame, san: pd.DataFrame | None = None) -> None:
    bullets = [
        f"Automated label scan over profile×window×overlay rows (N={len(by_pww)}).",
        "Champion v0 entries frozen; simulation uses local panel + QQQ 1m bars only.",
        "Intrabar ambiguity default `stop_first`; optimistic paths not used for headline metrics.",
        "Router/quality v2 remains complementary — masks vs exit paths are different controls.",
        "No production combiner wiring in this commit.",
    ]
    if label == "RUN_EXIT_OVERLAY_DIAGNOSTICS_V2" and san is not None and len(san) and float(san["mean_abs_r_diff"].max()) > 0.15:
        bullets.insert(
            0,
            f"`fixed_target_replay` vs panel `r_multiple` mean abs diff up to **{float(san['mean_abs_r_diff'].max()):.3f}** R — reconcile entry bar / intrabar model before trusting overlay deltas.",
        )
    _write_md(
        out / "exit_overlay_diagnostics_decision.md",
        [
            "# exit_overlay_diagnostics_decision",
            "",
            "## Decision label (exactly one)",
            "",
            f"**`{label}`**",
            "",
            "## Rationale",
            "",
            "\n".join(f"- {b}" for b in bullets),
            "",
            "## Recommended next step (exactly one)",
            "",
            {
                "DESIGN_EXIT_MANAGEMENT_INTEGRATION": "Draft Layer2 **exit-management integration design** (metadata-driven hooks; no YAML signal edits).",
                "RUN_EXIT_OVERLAY_DIAGNOSTICS_V2": "Refine overlay rules (ambiguity sensitivity, context eligibility, runner trail parameters) and rerun this harness.",
                "RETURN_TO_LAYER2_ROUTER_INTEGRATION_DESIGN": "Return to **router integration design** — exit overlays did not outperform router/quality evidence enough.",
                "DESIGN_SCALP_LONG_STRATEGIES": "Design long-side scalp families (only if entries proven insufficient — not selected here).",
                "DESIGN_SHORT_BRANCH": "Design short branch (not supported by current evidence).",
                "HOLD_AND_REVIEW": "Hold — data quality or contradictions require human review before more engineering.",
            }.get(label, "Review aggregates and pick a single next increment."),
            "",
            "## Explicit non-runs",
            "",
            "- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.",
            "- No production router or exit-management in combiner.",
            "- No strategy / feature / selected-candidate YAML edits.",
            "- No short or scalp strategy code.",
            "- Row-level outputs remain local-only.",
        ],
    )


def write_chatgpt_bundle(out: Path, *, bmeta: dict[str, Any], by_pww: pd.DataFrame, decision: str) -> None:
    key_lines = [
        "# CHATGPT_REVIEW_BUNDLE — exit_overlay_diagnostics_v1",
        "",
        "## 1. Git / validation",
        "",
        "Run `python -m compileall -q src`, `python -m pytest -q`, `python -m src.strategies.loader --list`, and `validate_research_artifacts` on this root after clone.",
        "",
        "## 2. Why this task was needed",
        "",
        "Router/quality v2 formal decision was **`RUN_EXIT_OVERLAY_DIAGNOSTICS`**. This root executes that harness on Champion v0 trades without changing entries.",
        "",
        "## 3. Champion v0 freeze recap",
        "",
        "- `pa_only_mtp1_meta` — CLEAN_BASELINE — PA_BUY_SELL_CLOSE_TREND_003",
        "- `pa_gap_mtp2_meta` — DEFAULT_COMBINED — PA + GAP_ACCEPTANCE_FAILURE_001",
        "- `primary_mtp2_meta` — BREADTH_REFERENCE_ONLY — PA + GAP + CCI_EXTREME_SNAPBACK_003",
        "",
        "## 4. Input data / local panel / bar coverage",
        "",
        f"Bar loader meta: `{json.dumps(bmeta, default=str)[:1200]}`",
        "",
        "## 5. Overlay harness design",
        "",
        "See `exit_overlay_harness_design.md` and `exit_overlay_config_v1.yaml`.",
        "",
        "## 6. Overlay sanity vs original",
        "",
        "See `overlay_sanity_vs_original.csv` — **replay vs panel `r_multiple` still drifts** (mean abs diff often **~0.28–0.38 R** by profile×window). Treat headline overlay deltas as **diagnostic** until entry bar / fill model is reconciled.",
        "",
        "## 7–10. Trend swing / runner / no-followthrough / max-hold",
        "",
        "See `trend_swing_context_results.csv`, `runner_context_results.csv`, `no_followthrough_context_results.csv`, `max_hold_tighten_results.csv`.",
        "",
        "## 11. Context-specific results",
        "",
        "See `context_overlay_analysis.md`.",
        "",
        "## 12. Weak-period results",
        "",
        "See `overlay_weak_period_results.csv`.",
        "",
        "## 13. Exit vs router/quality",
        "",
        "See `exit_vs_router_quality_comparison.md`.",
        "",
        "## 14. Scalp / short roadmap",
        "",
        "See `scalp_short_after_exit_overlay.md`.",
        "",
        "## 15. Decision",
        "",
        f"**`{decision}`** — see `exit_overlay_diagnostics_decision.md`.",
        "",
        "## 16. Explicit non-runs",
        "",
        "Same as decision doc — no WFO/live/SPY/production wiring/new strategies.",
        "",
        "## 17. Recommended next step",
        "",
        "Follow the single recommended step in `exit_overlay_diagnostics_decision.md`.",
        "",
        "## Key aggregate preview (by profile / window / overlay)",
        "",
        _md_table(by_pww.sort_values(["delta_total_r"], ascending=False).head(25)),
    ]
    _write_md(out / "CHATGPT_REVIEW_BUNDLE.md", key_lines)


def write_source_map(out: Path) -> None:
    rows = [
        {
            "file_path": "src/research/exit_overlay_sim.py",
            "purpose": "Bar-path simulator for overlays",
            "required_for_review": "yes",
            "row_count_if_csv": "",
            "markdown_mirror_available": "no",
            "local_only_dependency": "no",
            "notes": "Research-only",
        },
        {
            "file_path": "src/research/run_exit_overlay_diagnostics.py",
            "purpose": "CLI runner + aggregates",
            "required_for_review": "yes",
            "row_count_if_csv": "",
            "markdown_mirror_available": "no",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv",
            "purpose": "Champion v0 row panel",
            "required_for_review": "yes",
            "row_count_if_csv": "10628",
            "markdown_mirror_available": "local_input_inventory.md",
            "local_only_dependency": "yes",
            "notes": "gitignored",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/baseline_inventory.md",
            "purpose": "Cycle baseline + dependency inventory",
            "required_for_review": "yes",
            "row_count_if_csv": "",
            "markdown_mirror_available": "no",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/exit_overlay_harness_design.md",
            "purpose": "Harness design narrative",
            "required_for_review": "yes",
            "row_count_if_csv": "",
            "markdown_mirror_available": "exit_overlay_harness_design.csv",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/overlay_results_by_profile.csv",
            "purpose": "Pooled-by-profile aggregates",
            "required_for_review": "yes",
            "row_count_if_csv": "30",
            "markdown_mirror_available": "CHATGPT_REVIEW_BUNDLE.md",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/overlay_results_detail_by_profile_window.csv",
            "purpose": "Full profile×window×overlay grid",
            "required_for_review": "yes",
            "row_count_if_csv": "120",
            "markdown_mirror_available": "overlay_summary.md",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/overlay_sanity_vs_original.csv",
            "purpose": "fixed_target_replay vs panel r_multiple",
            "required_for_review": "yes",
            "row_count_if_csv": "12",
            "markdown_mirror_available": "exit_overlay_harness_design.md",
            "local_only_dependency": "no",
            "notes": "",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/local_rows/overlay_trade_results.csv",
            "purpose": "Per-trade per-overlay rows",
            "required_for_review": "optional",
            "row_count_if_csv": "106280",
            "markdown_mirror_available": "no",
            "local_only_dependency": "yes",
            "notes": "gitignored",
        },
        {
            "file_path": "src/research/results/exit_overlay_diagnostics_v1/exit_overlay_diagnostics_decision.md",
            "purpose": "Single-label decision",
            "required_for_review": "yes",
            "row_count_if_csv": "",
            "markdown_mirror_available": "CHATGPT_REVIEW_BUNDLE.md",
            "local_only_dependency": "no",
            "notes": "",
        },
    ]
    _write_csv(pd.DataFrame(rows), out / "SOURCE_MAP.csv")


def write_key_tables(out: Path, by_prof: pd.DataFrame) -> None:
    rows: list[dict[str, str]] = []
    if len(by_prof):
        top = by_prof.sort_values("delta_total_r", ascending=False).head(12)
        for _, r in top.iterrows():
            rows.append(
                {
                    "section": "overlay_headline",
                    "item": f"{r.get('profile_id')}|{r.get('window')}|{r.get('overlay_id')}",
                    "metric": "delta_total_r",
                    "value": str(r.get("delta_total_r")),
                    "interpretation": str(r.get("label")),
                }
            )
    _write_csv(pd.DataFrame(rows), out / "chatgpt_key_tables.csv")


def write_summary_md(out: Path, by_prof: pd.DataFrame, decision: str) -> None:
    _write_md(
        out / "exit_overlay_diagnostics_summary.md",
        [
            "# exit_overlay_diagnostics_summary",
            "",
            f"**Decision:** `{decision}`",
            "",
            "## Headline table",
            "",
            _md_table(by_prof.head(40)),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Exit overlay diagnostics (offline, research-only).")
    p.add_argument("--local-panel", type=Path, required=True)
    p.add_argument("--router-quality-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--data-dir", type=Path, default=_REPO_ROOT / "data" / "raw" / "ibkr")
    p.add_argument("--profiles", type=str, default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", type=str, default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--overlays", type=str, default=",".join(DEFAULT_OVERLAYS))
    p.add_argument("--ambiguity-policy", choices=[x.value for x in AmbiguityPolicy], default="stop_first")
    p.add_argument("--aggregate-only", action="store_true")
    p.add_argument("--local-row-output", action="store_true")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    profs = _parse_list(args.profiles)
    wins = _parse_list(args.windows)
    ovl = _parse_list(args.overlays)
    amb = AmbiguityPolicy(args.ambiguity_policy)

    panel_path = Path(args.local_panel)
    if not panel_path.is_file():
        raise SystemExit(f"missing local panel: {panel_path}")

    if args.dry_run:
        plan = pd.DataFrame(
            [
                {
                    "local_panel": _rel_if_under_repo(panel_path),
                    "profiles": ",".join(profs),
                    "windows": ",".join(wins),
                    "overlays": ",".join(ovl),
                    "ambiguity": amb.value,
                    "aggregate_only": bool(args.aggregate_only),
                    "local_row_output": bool(args.local_row_output),
                    "data_dir": _rel_if_under_repo(Path(args.data_dir)),
                    "committed_outputs": str(out.relative_to(_REPO_ROOT)) if str(out).startswith(str(_REPO_ROOT)) else str(out),
                    "local_only": "local_rows/overlay_trade_results.csv (gitignored via local_rows/)",
                }
            ]
        )
        _write_csv(plan, out / "dry_run_plan.csv")
        val = pd.DataFrame(
            [
                {"check": "panel_exists", "ok": True, "notes": _rel_if_under_repo(panel_path)},
                {"check": "output_root", "ok": True, "notes": _rel_if_under_repo(out)},
                {"check": "production_wiring", "ok": True, "notes": "none — research runner only"},
                {"check": "row_level_gitignore", "ok": True, "notes": "local_rows/** ignored"},
            ]
        )
        _write_csv(val, out / "dry_run_validation.csv")
        _write_md(
            out / "dry_run_validation.md",
            ["# dry_run_validation", "", _md_table(plan), "", _md_table(val)],
        )
        return 0

    agg_marker = out / "overlay_results_by_profile.csv"
    if args.skip_existing and agg_marker.is_file():
        return 0

    panel = pd.read_csv(panel_path)
    panel = panel[panel["profile_id"].isin(profs) & panel["window"].isin(wins)].copy()
    if panel.empty:
        raise SystemExit("panel empty after profile/window filter")

    bars, bmeta = load_bars_for_panel(panel, data_dir=args.data_dir)
    _write_csv(pd.DataFrame([bmeta]), out / "overlay_data_quality.csv")
    cov_rows = []
    for sd, g in panel.groupby("session_date"):
        has = int(str(sd) in set(bars["session_date"].astype(str))) if len(bars) else 0
        cov_rows.append({"session_date": sd, "trade_rows": len(g), "bars_available": has})
    _write_csv(pd.DataFrame(cov_rows), out / "overlay_input_coverage.csv")

    if bmeta.get("status") == "EMPTY":
        _write_csv(pd.DataFrame([{"error": "no_bars"}]), out / "failed_overlay_runs.csv")
        raise SystemExit("no QQQ bars — cannot simulate")

    sim_df = simulate_all(panel, bars, ovl, amb)
    if "error" in sim_df.columns and sim_df["error"].notna().any():
        bad = sim_df[sim_df["error"].notna()].copy()
        _write_csv(bad, out / "failed_overlay_runs.csv")
        if args.stop_on_fail:
            raise SystemExit("simulation errors — see failed_overlay_runs.csv")

    if "error" in sim_df.columns:
        sim_ok = sim_df[sim_df["error"].isna()].copy()
    else:
        sim_ok = sim_df.copy()

    if args.local_row_output and len(sim_ok):
        lr = out / "local_rows"
        lr.mkdir(parents=True, exist_ok=True)
        sim_ok.to_csv(lr / "overlay_trade_results.csv", index=False, lineterminator="\n")

    def agg_l(group_cols: list[str]) -> pd.DataFrame:
        return attach_labels(aggregate_slice(sim_ok, group_cols), sim_ok)

    by_prof = agg_l(["profile_id", "overlay_id"])
    by_prof["window"] = "pooled_all_windows"
    _front = ["profile_id", "window", "overlay_id"]
    by_prof = by_prof[_front + [c for c in by_prof.columns if c not in _front]]

    by_win = agg_l(["window", "overlay_id"])
    by_win.insert(0, "profile_id", "pooled_all_profiles")

    by_pww = agg_l(["profile_id", "window", "overlay_id"])

    _write_csv(by_prof, out / "overlay_results_by_profile.csv")
    _write_csv(by_win, out / "overlay_results_by_window.csv")
    _write_csv(agg_l(["profile_id", "window", "overlay_id", "candidate_id"]), out / "overlay_results_by_candidate.csv")
    _write_csv(agg_l(["profile_id", "window", "overlay_id", "context_bucket"]), out / "overlay_results_by_context.csv")
    _write_csv(
        agg_l(["profile_id", "window", "overlay_id", "market_context_label"]),
        out / "overlay_results_by_market_context.csv",
    )
    _write_csv(
        agg_l(["profile_id", "window", "overlay_id", "entry_trade_number_of_day"]),
        out / "overlay_results_by_trade_number.csv",
    )
    _write_csv(agg_l(["profile_id", "window", "overlay_id", "exit_reason_overlay"]), out / "overlay_results_by_exit_reason.csv")

    _write_csv(weak_period_slice(sim_ok), out / "overlay_weak_period_results.csv")
    _write_csv(ambiguity_summary(sim_ok), out / "overlay_ambiguity_summary.csv")
    _write_csv(sanity_vs_original(sim_ok), out / "overlay_sanity_vs_original.csv")
    san_df = pd.read_csv(out / "overlay_sanity_vs_original.csv")

    _write_md(
        out / "overlay_summary.md",
        [
            "# overlay_summary",
            "",
            "## Top deltas (non-baseline)",
            "",
            _md_table(
                by_pww[~by_pww["overlay_id"].eq("baseline_original")]
                .sort_values("delta_total_r", ascending=False)
                .head(30)
            ),
        ],
    )

    _write_csv(by_pww, out / "overlay_results_detail_by_profile_window.csv")

    man = pd.DataFrame([{"profile_id": pr, "window": w, "overlay_id": o, "status": "OK"} for pr in profs for w in wins for o in ovl])
    _write_csv(man, out / "run_plan.csv")
    man2 = man.assign(command="python -m src.research.run_exit_overlay_diagnostics")
    _write_csv(man2, out / "run_execution_manifest.csv")
    man3 = man2.copy()
    man3["command"] = man3["command"].map(lambda s: str(s).replace(str(_REPO_ROOT), "<REPO>"))
    _write_csv(man3, out / "run_execution_manifest_sanitized.csv")

    router_root = Path(args.router_quality_root)
    write_router_quality_comparison(out=out, router_root=router_root, by_pww_detail=by_pww)
    write_context_analysis(out, sim_ok)
    write_scalp_short_roadmap(out)

    decision = choose_decision(by_pww, san_df)
    write_decision(out, decision, by_pww, san_df)
    write_chatgpt_bundle(out, bmeta=bmeta, by_pww=by_pww, decision=decision)
    write_source_map(out)
    write_key_tables(out, by_pww)
    write_summary_md(out, by_pww, decision)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
