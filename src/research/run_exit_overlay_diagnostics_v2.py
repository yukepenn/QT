"""
Exit overlay diagnostics v2 — combiner-aligned clone replay + contextual overlays (research-only).

Modes:
  ``alignment`` — grid search over ``CloneReplayConfig`` vs panel ``r_multiple``.
  ``overlay``   — overlays vs headline ``combiner_clone_replay`` (stop_first on clone).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.read_bars import read_bars  # noqa: E402
from src.research.exit_overlay_alignment import (  # noqa: E402
    CloneReplayConfig,
    aggregate_alignment_per_config_slice,
    combiner_clone_long_walk,
    iter_default_alignment_grid,
    normalize_exit_reason,
    pick_best_config,
)
from src.research.exit_overlay_sim import (  # noqa: E402
    AmbiguityPolicy,
    add_session_date_column,
    no_followthrough_5bars_contextual_eligible,
    runner_contextual_eligible,
    simulate_row,
    trend_swing_2R_contextual_eligible,
)
from src.research.router_quality_refinement_v2_lib import summary_metrics  # noqa: E402
from src.research.run_exit_overlay_diagnostics import load_bars_for_panel  # noqa: E402


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


def _delta_pf(m_o: dict[str, Any], m_v: dict[str, Any]) -> float | None:
    a, b = m_o.get("pf_r"), m_v.get("pf_r")
    if a is None or b is None:
        return None
    if math.isinf(float(a)) or math.isinf(float(b)):
        return None
    return float(b) - float(a)


def _metrics_bundle_from_r(df: pd.DataFrame, r_col: str) -> dict[str, Any]:
    t = df.copy()
    t["r_multiple"] = pd.to_numeric(t[r_col], errors="coerce")
    return summary_metrics(t)


def _metrics_bundle_clone_overlay(g: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    c = g.copy()
    c["r_multiple"] = pd.to_numeric(c["r_clone"], errors="coerce")
    o = g.copy()
    o["r_multiple"] = pd.to_numeric(o["r_overlay"], errors="coerce")
    return summary_metrics(c), summary_metrics(o)


def overlay_aggregate_slice(sim_df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    parts: list[dict[str, Any]] = []
    for key, g in sim_df.groupby(group_cols, dropna=False):
        keys = key if isinstance(key, tuple) else (key,)
        m_c, m_o = _metrics_bundle_clone_overlay(g)
        d_tr = float(m_o["total_r"] - m_c["total_r"])
        d_pf = _delta_pf(m_c, m_o)
        d_dd = None
        if m_c["max_dd_r_proxy"] is not None and m_o["max_dd_r_proxy"] is not None:
            d_dd = float(m_o["max_dd_r_proxy"]) - float(m_c["max_dd_r_proxy"])
        wb, wv = m_c.get("weak_period_total_r"), m_o.get("weak_period_total_r")
        d_wk = float(wv) - float(wb) if wb is not None and wv is not None else None
        amb_pct = float(g["ambiguous_bar"].mean()) if "ambiguous_bar" in g.columns else 0.0
        chg_n = int(g["changed_exit_vs_clone"].sum()) if "changed_exit_vs_clone" in g.columns else 0
        elig = int(g["eligible_trade"].sum()) if "eligible_trade" in g.columns else int(len(g))
        row_dict: dict[str, Any] = {c: keys[i] for i, c in enumerate(group_cols)}
        row_dict.update(
            {
                "trades": m_o["trades"],
                "eligible_trades": elig,
                "changed_exit_count": chg_n,
                "changed_exit_pct": float(chg_n / max(len(g), 1)),
                "total_r_clone": m_c["total_r"],
                "total_r_overlay": m_o["total_r"],
                "delta_total_r_vs_clone": d_tr,
                "PF_R_clone": m_c["pf_r"],
                "PF_R_overlay": m_o["pf_r"],
                "maxDD_proxy_clone": m_c["max_dd_r_proxy"],
                "maxDD_proxy_overlay": m_o["max_dd_r_proxy"],
                "worst_month_clone": m_c["worst_month_r"],
                "worst_month_overlay": m_o["worst_month_r"],
                "worst_quarter_clone": m_c["worst_quarter_r"],
                "worst_quarter_overlay": m_o["worst_quarter_r"],
                "2025Q1_clone": m_c["2025Q1_total_r"],
                "2025Q1_overlay": m_o["2025Q1_total_r"],
                "2022Q4_clone": m_c["2022Q4_total_r"],
                "2022Q4_overlay": m_o["2022Q4_total_r"],
                "2023Q3_clone": m_c["2023Q3_total_r"],
                "2023Q3_overlay": m_o["2023Q3_total_r"],
                "ambiguous_count": int(g["ambiguous_bar"].sum()) if "ambiguous_bar" in g.columns else 0,
                "ambiguous_pct": amb_pct * 100.0,
                "weak_period_delta_r": d_wk,
            }
        )
        row_dict["label"] = label_overlay_v2_row(
            delta_total_r=float(row_dict["delta_total_r_vs_clone"]),
            delta_pf=d_pf,
            delta_dd=d_dd,
            amb_pct=float(row_dict["ambiguous_pct"]) / 100.0,
            weak_delta=d_wk,
        )
        parts.append(row_dict)
    return pd.DataFrame(parts)


def label_overlay_v2_row(
    *,
    delta_total_r: float,
    delta_pf: float | None,
    delta_dd: float | None,
    amb_pct: float,
    weak_delta: float | None,
) -> str:
    if amb_pct > 0.12:
        return "OVERLAY_V2_AMBIGUITY_SENSITIVE"
    if amb_pct > 0.08:
        return "OVERLAY_V2_ALIGNMENT_LIMITED"
    if delta_pf is None or (abs(delta_pf or 0) < 0.01 and (delta_dd is None or abs(delta_dd or 0) < 0.5)):
        return "OVERLAY_V2_NO_IMPROVEMENT"
    improved = (delta_pf is not None and delta_pf > 0.02) or (delta_dd is not None and delta_dd > 2.0)
    if not improved:
        return "OVERLAY_V2_NO_IMPROVEMENT"
    if weak_delta is not None and weak_delta < -25:
        return "OVERLAY_V2_REJECT"
    if delta_total_r < -30:
        return "OVERLAY_V2_TOO_AGGRESSIVE"
    if delta_pf is not None and delta_pf > 0.02 and delta_total_r < -10:
        return "OVERLAY_V2_CONTEXT_SPECIFIC"
    return "OVERLAY_V2_PROMISING"


def attach_labels_v2(by_rows: pd.DataFrame, sim_df: pd.DataFrame) -> pd.DataFrame:
    del sim_df  # reserved for late_oow sensitivity hooks
    sub = by_rows.copy()
    labels: list[str] = []
    for _, r in sub.iterrows():
        d_dd = None
        try:
            if r.get("maxDD_proxy_overlay") is not None and r.get("maxDD_proxy_clone") is not None:
                d_dd = float(r["maxDD_proxy_overlay"]) - float(r["maxDD_proxy_clone"])
        except (TypeError, ValueError):
            d_dd = None
        labels.append(
            label_overlay_v2_row(
                delta_total_r=float(r["delta_total_r_vs_clone"]),
                delta_pf=_row_delta_pf_v2(r),
                delta_dd=d_dd,
                amb_pct=float(r["ambiguous_pct"]) / 100.0,
                weak_delta=float(r["weak_period_delta_r"]) if r.get("weak_period_delta_r") is not None else None,
            )
        )
    sub["label"] = labels
    return sub


def weak_period_slice_v2(sim_df: pd.DataFrame) -> pd.DataFrame:
    if sim_df.empty or "weak_period_flag" not in sim_df.columns:
        return pd.DataFrame()
    wf = sim_df["weak_period_flag"].astype(str).str.lower().isin(("true", "1", "t", "yes"))
    sub = sim_df.loc[wf]
    wp: list[dict[str, Any]] = []
    for key, g in sub.groupby(["profile_id", "window", "overlay_id", "ambiguity_policy"], dropna=False):
        pid, win, oid, amb = key
        m_c, m_o = _metrics_bundle_clone_overlay(g)
        wp.append(
            {
                "profile_id": pid,
                "window": win,
                "overlay_id": oid,
                "ambiguity_policy": amb,
                "weak_trades": len(g),
                "total_r_clone": m_c["total_r"],
                "total_r_overlay": m_o["total_r"],
                "delta_total_r_vs_clone": float(m_o["total_r"] - m_c["total_r"]),
            }
        )
    return pd.DataFrame(wp)


def _row_delta_pf_v2(r: pd.Series) -> float | None:
    a, b = r.get("PF_R_clone"), r.get("PF_R_overlay")
    try:
        if a is None or b is None or (isinstance(a, float) and math.isnan(a)) or (isinstance(b, float) and math.isnan(b)):
            return None
        fa, fb = float(a), float(b)
        if math.isinf(fa) or math.isinf(fb):
            return None
        return fb - fa
    except (TypeError, ValueError):
        return None


def _eligible_flag(overlay_id: str, row: pd.Series) -> bool:
    oid = str(overlay_id)
    if "contextual" in oid:
        if "trend_swing_2R" in oid:
            return trend_swing_2R_contextual_eligible(row)
        if "runner_after" in oid and "vwap" in oid:
            return runner_contextual_eligible(row)
        if "runner_after" in oid and "atr" in oid:
            return runner_contextual_eligible(row)
        if "no_followthrough" in oid:
            return no_followthrough_5bars_contextual_eligible(row)
    return True


def run_alignment_grid(
    panel: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    configs: Iterable[CloneReplayConfig] | None = None,
) -> pd.DataFrame:
    by_day: dict[str, pd.DataFrame] = {str(d): g for d, g in bars.groupby("session_date", sort=False)}
    cfgs = list(configs) if configs is not None else list(iter_default_alignment_grid())
    rows_out: list[dict[str, Any]] = []
    for cfg in cfgs:
        meta = cfg.to_dict()
        for _, row in panel.iterrows():
            sd = str(row["session_date"])
            sb = by_day.get(sd)
            if sb is None or sb.empty:
                continue
            try:
                res = combiner_clone_long_walk(session_bars=sb, row=row, cfg=cfg)
            except Exception as ex:  # noqa: BLE001
                rows_out.append({**meta, "session_date": sd, "error": str(ex)})
                continue
            orig = float(pd.to_numeric(row.get("r_multiple"), errors="coerce"))
            rep = float(res.r_multiple)
            match_ex = 1.0 if normalize_exit_reason(row.get("exit_reason")) == normalize_exit_reason(res.exit_reason) else 0.0
            rows_out.append(
                {
                    **meta,
                    "trade_id": row.get("trade_id"),
                    "profile_id": row.get("profile_id"),
                    "window": row.get("window"),
                    "session_date": sd,
                    "r_original": orig,
                    "r_replay": rep,
                    "abs_r_diff": abs(rep - orig),
                    "exit_reason_replay": res.exit_reason,
                    "exit_reason_match": match_ex,
                    "ambiguous_bar": bool(res.ambiguous_bar),
                }
            )
    return pd.DataFrame(rows_out)


def run_overlay_simulate(
    panel: pd.DataFrame,
    bars: pd.DataFrame,
    overlays: list[str],
    ambiguity: AmbiguityPolicy,
    clone_cfg: CloneReplayConfig,
) -> pd.DataFrame:
    headline_clone = dataclasses.replace(clone_cfg, same_bar_policy="stop_first")
    by_day = {str(d): g for d, g in bars.groupby("session_date", sort=False)}
    rows_out: list[dict[str, Any]] = []
    for _, row in panel.iterrows():
        sd = str(row["session_date"])
        sb = by_day.get(sd)
        if sb is None or sb.empty:
            continue
        try:
            cres = simulate_row(
                session_bars=sb,
                row=row,
                overlay_id="combiner_clone_replay",
                ambiguity=ambiguity,
                clone_replay_cfg=headline_clone,
            )
            r_clone = float(cres.r_multiple)
        except Exception as ex:  # noqa: BLE001
            for oid in overlays:
                rows_out.append(
                    {
                        "trade_id": row.get("trade_id"),
                        "profile_id": row.get("profile_id"),
                        "window": row.get("window"),
                        "overlay_id": oid,
                        "ambiguity_policy": ambiguity.value,
                        "error": str(ex),
                    }
                )
            continue

        for oid in overlays:
            try:
                if oid == "combiner_clone_replay":
                    res = cres
                elif oid == "baseline_original":
                    res = simulate_row(session_bars=sb, row=row, overlay_id=oid, ambiguity=ambiguity)
                else:
                    res = simulate_row(session_bars=sb, row=row, overlay_id=oid, ambiguity=ambiguity)
            except Exception as ex:  # noqa: BLE001
                rows_out.append(
                    {
                        "trade_id": row.get("trade_id"),
                        "profile_id": row.get("profile_id"),
                        "window": row.get("window"),
                        "overlay_id": oid,
                        "ambiguity_policy": ambiguity.value,
                        "error": str(ex),
                    }
                )
                continue
            r_orig = float(pd.to_numeric(row.get("r_multiple"), errors="coerce"))
            r_ov = float(res.r_multiple)
            chg = oid not in ("baseline_original", "combiner_clone_replay") and abs(r_ov - r_clone) > 1e-6
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
                    "ambiguity_policy": ambiguity.value,
                    "r_panel_original": r_orig,
                    "r_clone": r_clone,
                    "r_overlay": r_ov,
                    "delta_r_vs_clone": r_ov - r_clone,
                    "exit_reason_overlay": res.exit_reason,
                    "bars_held_overlay": res.bars_held,
                    "ambiguous_bar": bool(res.ambiguous_bar),
                    "changed_exit_vs_clone": bool(chg),
                    "eligible_trade": bool(_eligible_flag(oid, row)),
                }
            )
    return pd.DataFrame(rows_out)


def _write_alignment_bundle(
    *,
    out_root: Path,
    detail: pd.DataFrame,
    profiles: list[str],
    windows: list[str],
) -> CloneReplayConfig | None:
    aln = out_root / "alignment"
    aln.mkdir(parents=True, exist_ok=True)
    cfg_cols = [
        "config_id",
        "start_bar_policy",
        "entry_price_source",
        "exit_price_source",
        "slippage_policy",
        "risk_policy",
        "same_bar_policy",
        "forced_exit_policy",
        "target_policy",
    ]
    if detail.empty:
        _write_csv(pd.DataFrame([{"note": "no_alignment_rows"}]), aln / "alignment_grid_results.csv")
        return None

    if "error" in detail.columns and bool(detail["error"].notna().all()):
        _write_csv(pd.DataFrame([{"note": "all_rows_failed"}]), aln / "alignment_grid_results.csv")
        return None

    ok = detail[detail["error"].isna()].copy() if "error" in detail.columns else detail.copy()
    if ok.empty:
        _write_csv(pd.DataFrame([{"note": "all_errors"}]), aln / "alignment_grid_results.csv")
        return None

    gcols = cfg_cols
    agg_all = aggregate_alignment_per_config_slice(ok, gcols)
    _write_csv(agg_all, aln / "alignment_grid_results.csv")
    parts_pw = []
    for (pid, win), chunk in ok.groupby(["profile_id", "window"], dropna=False):
        a = aggregate_alignment_per_config_slice(chunk, gcols)
        for _, r in a.iterrows():
            d = r.to_dict()
            d["profile_id"], d["window"] = pid, win
            parts_pw.append(d)
    by_pw = pd.DataFrame(parts_pw)
    _write_csv(by_pw, aln / "alignment_by_profile_window.csv")

    best = pick_best_config(agg_all)
    if best is None:
        return None
    best_rows = ok[ok["config_id"].astype(str) == str(best.config_id)].copy()
    best_rows["abs_r_diff"] = (pd.to_numeric(best_rows["r_replay"], errors="coerce") - pd.to_numeric(best_rows["r_original"], errors="coerce")).abs()
    dist = best_rows["abs_r_diff"].describe(percentiles=[0.5, 0.9, 0.99])
    _write_csv(dist.to_frame("value").reset_index().rename(columns={"index": "stat"}), aln / "alignment_error_distribution.csv")

    worst = best_rows.nlargest(min(50, len(best_rows)), "abs_r_diff")[
        ["trade_id", "profile_id", "window", "r_original", "r_replay", "abs_r_diff", "exit_reason_replay", "ambiguous_bar"]
    ]
    _write_csv(worst, aln / "alignment_failure_examples.csv")

    with (aln / "alignment_best_config.yaml").open("w", encoding="utf-8") as fh:
        yaml.safe_dump(best.to_dict(), fh, sort_keys=True, allow_unicode=True)

    row0 = agg_all[agg_all["config_id"].astype(str) == str(best.config_id)].iloc[0].to_dict()
    overall_label = str(row0.get("label", "ALIGNMENT_DATA_LIMITED"))
    _write_md(
        aln / "alignment_best_config_summary.md",
        [
            "# alignment_best_config_summary",
            "",
            f"**config_id:** `{best.config_id}`",
            "",
            "## Switches",
            "",
            "\n".join(f"- **{k}:** `{v}`" for k, v in best.to_dict().items() if k != "config_id"),
            "",
            "## Headline metrics (all trades in run)",
            "",
            _md_table(pd.DataFrame([row0])),
            "",
            f"**Alignment label:** `{overall_label}`",
        ],
    )
    _write_md(
        aln / "alignment_grid_results.md",
        [
            "# alignment_grid_results",
            "",
            "Sorted by `mean_abs_r_diff` (lowest first).",
            "",
            _md_table(agg_all.sort_values("mean_abs_r_diff").head(40)),
        ],
    )

    dec = "REFINE_REPLAY_ALIGNMENT"
    if overall_label == "ALIGNMENT_PASS":
        dec = "RUN_EXIT_OVERLAY_DIAGNOSTICS_V3"
    elif overall_label == "ALIGNMENT_PASS_WITH_WARNINGS":
        dec = "RUN_EXIT_OVERLAY_DIAGNOSTICS_V3"
    elif overall_label == "ALIGNMENT_DATA_LIMITED":
        dec = "HOLD_AND_REVIEW"
    _write_md(
        aln / "alignment_decision.md",
        [
            "# alignment_decision",
            "",
            f"**Label:** `{overall_label}`",
            "",
            f"**Recommended gate outcome:** `{dec}`",
            "",
            "- If `ALIGNMENT_FAIL` persists after best grid row, treat overlay deltas as **non-actionable** until replay model improves.",
            "",
        ],
    )
    return best


def _load_clone_cfg(path: Path) -> CloneReplayConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CloneReplayConfig.from_mapping(raw)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Exit overlay diagnostics v2 (combiner-aligned replay).")
    p.add_argument("--local-panel", type=Path, required=True)
    p.add_argument("--v1-root", type=Path, default=_REPO_ROOT / "src/research/results/exit_overlay_diagnostics_v1")
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--data-dir", type=Path, default=_REPO_ROOT / "data" / "raw" / "ibkr")
    p.add_argument("--mode", choices=("alignment", "overlay"), required=True)
    p.add_argument("--profiles", type=str, default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", type=str, default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--overlays", type=str, default="")
    p.add_argument("--ambiguity-policies", type=str, default="stop_first")
    p.add_argument("--alignment-config", type=Path, default=None)
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
    amb_policies = _parse_list(args.ambiguity_policies)

    panel_path = Path(args.local_panel)
    if not panel_path.is_file():
        raise SystemExit(f"missing local panel: {panel_path}")

    if args.dry_run:
        cfgs = list(iter_default_alignment_grid())
        plan = pd.DataFrame(
            [
                {
                    "mode": args.mode,
                    "local_panel": _rel_if_under_repo(panel_path),
                    "v1_root": _rel_if_under_repo(Path(args.v1_root)),
                    "profiles": ",".join(profs),
                    "windows": ",".join(wins),
                    "alignment_configs": len(cfgs),
                    "config_ids_sample": ",".join(c.config_id for c in cfgs[:8]),
                    "overlays": args.overlays or "(overlay mode default)",
                    "ambiguity_policies": ",".join(amb_policies),
                    "aggregate_only": bool(args.aggregate_only),
                    "local_row_output": bool(args.local_row_output),
                    "local_only_note": "local_rows/** not committed",
                }
            ]
        )
        if args.mode == "alignment":
            _write_csv(plan, out / "alignment_dry_run_plan.csv")
            val_path, val_md = out / "alignment_dry_run_validation.csv", out / "alignment_dry_run_validation.md"
        else:
            _write_csv(plan, out / "overlay_v2" / "overlay_dry_run_plan.csv")
            val_path, val_md = out / "overlay_v2" / "overlay_dry_run_validation.csv", out / "overlay_v2" / "overlay_dry_run_validation.md"
        val_path.parent.mkdir(parents=True, exist_ok=True)
        val = pd.DataFrame(
            [
                {"check": "panel_exists", "ok": True, "notes": _rel_if_under_repo(panel_path)},
                {"check": "output_root", "ok": True, "notes": _rel_if_under_repo(out)},
                {"check": "research_only", "ok": True, "notes": "no combiner production edits"},
            ]
        )
        _write_csv(val, val_path)
        _write_md(val_md, ["# dry_run_validation", "", _md_table(plan), "", _md_table(val)])
        return 0

    marker = out / ("alignment/alignment_grid_results.csv" if args.mode == "alignment" else "overlay_v2/overlay_v2_results_by_profile.csv")
    if args.skip_existing and marker.is_file():
        return 0

    panel = pd.read_csv(panel_path)
    panel = panel[panel["profile_id"].isin(profs) & panel["window"].isin(wins)].copy()
    if panel.empty:
        raise SystemExit("panel empty after profile/window filter")

    bars, bmeta = load_bars_for_panel(panel, data_dir=args.data_dir)
    _write_csv(pd.DataFrame([bmeta]), out / "bar_load_meta.csv")

    if args.mode == "alignment":
        aln = out / "alignment"
        aln.mkdir(parents=True, exist_ok=True)
        if bmeta.get("status") == "EMPTY" or bars.empty:
            _write_csv(pd.DataFrame([{"error": "no_bars", "detail": json.dumps(bmeta, default=str)}]), aln / "alignment_failure.csv")
            _write_md(
                aln / "alignment_decision.md",
                [
                    "# alignment_decision",
                    "",
                    "**Label:** `ALIGNMENT_DATA_LIMITED`",
                    "",
                    "No QQQ parquet bars under `data/raw/ibkr` — cannot evaluate replay alignment in this checkout.",
                    "",
                    "**Next:** obtain local IBKR 1-minute QQQ partitions, rerun `--mode alignment`.",
                ],
            )
            if args.stop_on_fail:
                raise SystemExit("no QQQ bars")
            return 1
        detail = run_alignment_grid(panel, bars)
        if args.local_row_output and len(detail):
            lr = out / "local_rows"
            lr.mkdir(parents=True, exist_ok=True)
            detail.to_csv(lr / "alignment_trade_detail.csv", index=False, lineterminator="\n")
        best = _write_alignment_bundle(out_root=out, detail=detail, profiles=profs, windows=wins)
        man = pd.DataFrame([c.to_dict() for c in iter_default_alignment_grid()])
        _write_csv(man, out / "alignment/alignment_config_manifest.csv")
        if best is None:
            _write_md(
                out / "alignment/alignment_decision.md",
                [
                    "# alignment_decision",
                    "",
                    "**Label:** `ALIGNMENT_DATA_LIMITED`",
                    "",
                    "Alignment detail frame was empty after filtering — no per-trade rows to score.",
                ],
            )
        return 0

    # overlay mode
    cfg_path = args.alignment_config or (out / "alignment" / "alignment_best_config.yaml")
    if not cfg_path.is_file():
        raise SystemExit(f"missing alignment config: {cfg_path} — run --mode alignment first")
    clone_cfg = _load_clone_cfg(cfg_path)

    if bmeta.get("status") == "EMPTY" or bars.empty:
        ov = out / "overlay_v2"
        ov.mkdir(parents=True, exist_ok=True)
        _write_csv(pd.DataFrame([{"error": "no_bars"}]), ov / "overlay_v2_failure.csv")
        if args.stop_on_fail:
            raise SystemExit("no QQQ bars")
        return 1

    ovl = _parse_list(args.overlays) if args.overlays else [
        "baseline_original",
        "combiner_clone_replay",
        "max_hold_tighten_60",
        "trend_swing_2R_contextual",
        "runner_after_1R_trail_vwap_contextual",
        "runner_after_1R_trail_atr_contextual",
        "no_followthrough_exit_5bars_contextual",
    ]

    sim_parts: list[pd.DataFrame] = []
    for amb_s in amb_policies:
        amb = AmbiguityPolicy(amb_s)
        part = run_overlay_simulate(panel, bars, ovl, amb, clone_cfg)
        sim_parts.append(part)
    sim_df = pd.concat(sim_parts, ignore_index=True) if sim_parts else pd.DataFrame()

    if "error" in sim_df.columns and sim_df["error"].notna().any():
        bad = sim_df[sim_df["error"].notna()].copy()
        _write_csv(bad, out / "overlay_v2/overlay_v2_failed_runs.csv")
        if args.stop_on_fail:
            raise SystemExit("simulation errors — see overlay_v2_failed_runs.csv")

    sim_ok = sim_df[sim_df["error"].isna()].copy() if "error" in sim_df.columns else sim_df.copy()
    if args.local_row_output and len(sim_ok):
        lr = out / "local_rows"
        lr.mkdir(parents=True, exist_ok=True)
        sim_ok.to_csv(lr / "overlay_trade_results_v2.csv", index=False, lineterminator="\n")

    ov = out / "overlay_v2"
    ov.mkdir(parents=True, exist_ok=True)

    if sim_ok.empty:
        empty = pd.DataFrame()
        for name in (
            "overlay_v2_results_by_profile.csv",
            "overlay_v2_results_by_window.csv",
            "overlay_v2_results_by_profile_window.csv",
            "overlay_v2_results_by_candidate.csv",
            "overlay_v2_results_by_context.csv",
            "overlay_v2_results_by_market_context.csv",
            "overlay_v2_results_by_trade_number.csv",
            "overlay_v2_weak_period_results.csv",
            "overlay_v2_ambiguity_sensitivity.csv",
            "overlay_v2_sanity_vs_clone.csv",
        ):
            _write_csv(empty, ov / name)
        _write_md(ov / "overlay_v2_summary.md", ["# overlay_v2_summary", "", "_(empty — no simulation rows)_"])
        return 0

    def agg_v2(gc: list[str]) -> pd.DataFrame:
        return attach_labels_v2(overlay_aggregate_slice(sim_ok, gc), sim_ok)

    _write_csv(agg_v2(["profile_id", "overlay_id", "ambiguity_policy"]), ov / "overlay_v2_results_by_profile.csv")
    _write_csv(agg_v2(["window", "overlay_id", "ambiguity_policy"]), ov / "overlay_v2_results_by_window.csv")
    _write_csv(agg_v2(["profile_id", "window", "overlay_id", "ambiguity_policy"]), ov / "overlay_v2_results_by_profile_window.csv")
    _write_csv(agg_v2(["profile_id", "window", "overlay_id", "candidate_id", "ambiguity_policy"]), ov / "overlay_v2_results_by_candidate.csv")
    _write_csv(agg_v2(["profile_id", "window", "overlay_id", "context_bucket", "ambiguity_policy"]), ov / "overlay_v2_results_by_context.csv")
    _write_csv(
        agg_v2(["profile_id", "window", "overlay_id", "market_context_label", "ambiguity_policy"]),
        ov / "overlay_v2_results_by_market_context.csv",
    )
    _write_csv(
        agg_v2(["profile_id", "window", "overlay_id", "entry_trade_number_of_day", "ambiguity_policy"]),
        ov / "overlay_v2_results_by_trade_number.csv",
    )

    _write_csv(weak_period_slice_v2(sim_ok), ov / "overlay_v2_weak_period_results.csv")

    amb_rows: list[dict[str, Any]] = []
    for (pid, win, oid), g in sim_ok.groupby(["profile_id", "window", "overlay_id"], dropna=False):
        for amb_s in amb_policies:
            sub = g[g["ambiguity_policy"].astype(str) == amb_s]
            if sub.empty:
                continue
            amb_rows.append(
                {
                    "profile_id": pid,
                    "window": win,
                    "overlay_id": oid,
                    "ambiguity_policy": amb_s,
                    "ambiguous_pct": float(sub["ambiguous_bar"].mean()) * 100.0,
                    "trades": len(sub),
                }
            )
    _write_csv(pd.DataFrame(amb_rows), ov / "overlay_v2_ambiguity_sensitivity.csv")

    san: list[dict[str, Any]] = []
    for (pid, win, amb), g in sim_ok[sim_ok["overlay_id"].eq("combiner_clone_replay")].groupby(
        ["profile_id", "window", "ambiguity_policy"], dropna=False
    ):
        d = (pd.to_numeric(g["r_overlay"], errors="coerce") - pd.to_numeric(g["r_panel_original"], errors="coerce")).abs()
        san.append(
            {
                "profile_id": pid,
                "window": win,
                "ambiguity_policy": amb,
                "mean_abs_r_diff_clone_vs_panel": float(d.mean()) if len(d) else 0.0,
                "rows": len(g),
            }
        )
    _write_csv(pd.DataFrame(san), ov / "overlay_v2_sanity_vs_clone.csv")

    _write_md(
        ov / "overlay_v2_summary.md",
        [
            "# overlay_v2_summary",
            "",
            "## By profile × window (stop_first on headline clone in runner; ambiguity column varies per policy)",
            "",
            _md_table(agg_v2(["profile_id", "window", "overlay_id", "ambiguity_policy"]).head(40)),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
