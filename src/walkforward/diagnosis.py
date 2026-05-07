"""Layer 3 smoke component diagnosis tables and narrative (research only, not live-ready)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_FOLD_RECENT = "recent_2025_202604"

_COMPONENT_SINGLE = [
    "recent_failed_only",
    "recent_gap_only",
    "recent_prior_day_only",
    "fullhist_failed_only",
    "fullhist_gap_only",
]

_INCREMENTAL_PAIRS: list[tuple[str, str, str]] = [
    ("recent_failed_only", "recent_failed_gap_mtd1", "add gap to failed ORB (pair, mtd1)"),
    ("recent_gap_only", "recent_failed_gap_mtd1", "add failed ORB to gap (pair, mtd1)"),
    ("recent_failed_gap_mtd1", "recent_trap_trio_mtd1", "add PRIOR_DAY_LEVEL_TRAP to pair"),
    ("recent_trap_trio_mtd1", "recent_trap_trio_mtd2", "allow 2nd trade per day (trio)"),
    ("recent_trap_trio_mtd2", "recent_opening_full_mtd2", "add ORB continuation + retest (full opening)"),
    ("fullhist_failed_only", "fullhist_failed_gap_mtd1", "add gap to failed ORB (full-hist)"),
    ("fullhist_gap_only", "fullhist_failed_gap_mtd1", "add failed ORB to gap (full-hist)"),
    ("fullhist_failed_gap_mtd1", "fullhist_failed_gap_mtd2", "allow 2nd trade (full-hist pair)"),
]

_MTD_PAIRS: list[tuple[str, str, str]] = [
    ("recent_failed_gap_mtd1", "recent_failed_gap_mtd2", "failed+gap recent"),
    ("recent_trap_trio_mtd1", "recent_trap_trio_mtd2", "trap trio recent"),
    ("recent_opening_full_mtd1", "recent_opening_full_mtd2", "full opening recent"),
    ("fullhist_failed_gap_mtd1", "fullhist_failed_gap_mtd2", "failed+gap full-hist"),
]

_RECENT_VS_FULL: list[tuple[str, str]] = [
    ("recent_failed_only", "fullhist_failed_only"),
    ("recent_gap_only", "fullhist_gap_only"),
    ("recent_failed_gap_mtd1", "fullhist_failed_gap_mtd1"),
    ("recent_failed_gap_mtd2", "fullhist_failed_gap_mtd2"),
]


def _safe_float(x: Any) -> float:
    try:
        v = float(x)
        return v if np.isfinite(v) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _row(sys_df: pd.DataFrame, system_id: str) -> pd.Series | None:
    if sys_df is None or sys_df.empty or "system_id" not in sys_df.columns:
        return None
    m = sys_df[sys_df["system_id"] == system_id]
    if m.empty:
        return None
    return m.iloc[0]


def _mf_pf(row: pd.Series) -> float:
    if "mean_fold_pf" in row.index and pd.notna(row.get("mean_fold_pf")):
        return _safe_float(row["mean_fold_pf"])
    return _safe_float(row.get("stitched_pf"))


def _mf_pf_r(row: pd.Series) -> float:
    if "mean_fold_pf_r" in row.index and pd.notna(row.get("mean_fold_pf_r")):
        return _safe_float(row["mean_fold_pf_r"])
    return _safe_float(row.get("stitched_pf_r"))


def build_component_diagnosis_tables(
    fold_summary: pd.DataFrame,
    system_summary: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build diagnosis tables (keys: component_table, incremental_table, ...)."""
    out: dict[str, pd.DataFrame] = {}

    # 1. Component singles
    rows = []
    for sid in _COMPONENT_SINGLE:
        r = _row(system_summary, sid)
        if r is None:
            rows.append(
                {
                    "system_id": sid,
                    "total_trades": np.nan,
                    "stitched_total_r": np.nan,
                    "mean_fold_pf": np.nan,
                    "mean_fold_pf_r": np.nan,
                    "positive_fold_count": np.nan,
                    "worst_fold_r": np.nan,
                    "fold_concentration": np.nan,
                    "cost_0_02_survives": np.nan,
                    "cost_0_03_survives": np.nan,
                }
            )
            continue
        rows.append(
            {
                "system_id": sid,
                "total_trades": r.get("total_trades"),
                "stitched_total_r": _safe_float(r.get("stitched_total_r")),
                "mean_fold_pf": _mf_pf(r),
                "mean_fold_pf_r": _mf_pf_r(r),
                "positive_fold_count": r.get("positive_fold_count"),
                "worst_fold_r": _safe_float(r.get("worst_fold_r")),
                "fold_concentration": _safe_float(r.get("fold_concentration")),
                "cost_0_02_survives": r.get("cost_0_02_survives"),
                "cost_0_03_survives": r.get("cost_0_03_survives"),
            }
        )
    out["component_table"] = pd.DataFrame(rows)

    # 2. Incremental
    inc_rows = []
    for base_id, var_id, label in _INCREMENTAL_PAIRS:
        b, v = _row(system_summary, base_id), _row(system_summary, var_id)
        if b is None or v is None:
            inc_rows.append(
                {
                    "base_system": base_id,
                    "variant_system": var_id,
                    "comparison_note": label,
                    "delta_total_r": np.nan,
                    "delta_worst_fold_r": np.nan,
                    "delta_positive_fold_count": np.nan,
                    "delta_fold_concentration": np.nan,
                    "delta_trades": np.nan,
                    "interpretation": "missing system row",
                }
            )
            continue
        dt_r = _safe_float(v.get("stitched_total_r")) - _safe_float(b.get("stitched_total_r"))
        dw = _safe_float(v.get("worst_fold_r")) - _safe_float(b.get("worst_fold_r"))
        dpfc = _safe_float(v.get("positive_fold_count")) - _safe_float(b.get("positive_fold_count"))
        dconc = _safe_float(v.get("fold_concentration")) - _safe_float(b.get("fold_concentration"))
        dtr = _safe_float(v.get("total_trades")) - _safe_float(b.get("total_trades"))
        interp = _interpret_delta(dt_r, dpfc, dconc, label)
        inc_rows.append(
            {
                "base_system": base_id,
                "variant_system": var_id,
                "comparison_note": label,
                "delta_total_r": dt_r,
                "delta_worst_fold_r": dw,
                "delta_positive_fold_count": dpfc,
                "delta_fold_concentration": dconc,
                "delta_trades": dtr,
                "interpretation": interp,
            }
        )
    out["incremental_table"] = pd.DataFrame(inc_rows)

    # 3. Max trades sensitivity
    mtd_rows = []
    for a, b, label in _MTD_PAIRS:
        r1, r2 = _row(system_summary, a), _row(system_summary, b)
        if r1 is None or r2 is None:
            mtd_rows.append(
                {
                    "mtd1_system": a,
                    "mtd2_system": b,
                    "family": label,
                    "delta_total_r": np.nan,
                    "delta_worst_fold_r": np.nan,
                    "delta_fold_concentration": np.nan,
                    "delta_trades": np.nan,
                    "mtd2_helps_headline_r": np.nan,
                    "mtd2_increases_concentration": np.nan,
                }
            )
            continue
        dt_r = _safe_float(r2.get("stitched_total_r")) - _safe_float(r1.get("stitched_total_r"))
        dw = _safe_float(r2.get("worst_fold_r")) - _safe_float(r1.get("worst_fold_r"))
        dc = _safe_float(r2.get("fold_concentration")) - _safe_float(r1.get("fold_concentration"))
        dtr = _safe_float(r2.get("total_trades")) - _safe_float(r1.get("total_trades"))
        mtd_rows.append(
            {
                "mtd1_system": a,
                "mtd2_system": b,
                "family": label,
                "delta_total_r": dt_r,
                "delta_worst_fold_r": dw,
                "delta_fold_concentration": dc,
                "delta_trades": dtr,
                "mtd2_helps_headline_r": dt_r > 0,
                "mtd2_increases_concentration": dc > 0,
            }
        )
    out["max_trades_sensitivity"] = pd.DataFrame(mtd_rows)

    # 4. Recent vs full-history
    rv_rows = []
    for recent_id, full_id in _RECENT_VS_FULL:
        rr, fr = _row(system_summary, recent_id), _row(system_summary, full_id)
        if rr is None or fr is None:
            rv_rows.append(
                {
                    "recent_system": recent_id,
                    "fullhist_system": full_id,
                    "delta_total_r_recent_minus_full": np.nan,
                    "delta_fold_concentration_recent_minus_full": np.nan,
                    "delta_positive_fold_count_recent_minus_full": np.nan,
                    "interpretation": "missing row",
                }
            )
            continue
        dtr = _safe_float(rr.get("stitched_total_r")) - _safe_float(fr.get("stitched_total_r"))
        dc = _safe_float(rr.get("fold_concentration")) - _safe_float(fr.get("fold_concentration"))
        dp = _safe_float(rr.get("positive_fold_count")) - _safe_float(fr.get("positive_fold_count"))
        note = (
            "recent higher stitched R" if dtr > 0 else "full-hist higher stitched R" if dtr < 0 else "similar R"
        )
        note2 = "; recent more concentrated" if dc > 0 else "; full-hist more concentrated" if dc < 0 else ""
        rv_rows.append(
            {
                "recent_system": recent_id,
                "fullhist_system": full_id,
                "delta_total_r_recent_minus_full": dtr,
                "delta_fold_concentration_recent_minus_full": dc,
                "delta_positive_fold_count_recent_minus_full": dp,
                "interpretation": note + note2,
            }
        )
    out["recent_vs_fullhistory"] = pd.DataFrame(rv_rows)

    # 5. Fold heatmap
    out["fold_heatmap"] = _fold_heatmap(fold_summary, system_summary)

    return out


def _fold_heatmap(fold_summary: pd.DataFrame, system_summary: pd.DataFrame) -> pd.DataFrame:
    if fold_summary.empty:
        return pd.DataFrame()
    rows = []
    for sid in sorted(fold_summary["system_id"].unique()):
        sub = fold_summary[fold_summary["system_id"] == sid]
        d: dict[str, Any] = {"system_id": sid}
        for _, r in sub.iterrows():
            fid = str(r.get("fold_id", ""))
            if fid == "y2023":
                d["y2023_total_r"] = r.get("total_r")
                d["y2023_pf_r"] = r.get("profit_factor_r")
            elif fid == "y2024":
                d["y2024_total_r"] = r.get("total_r")
                d["y2024_pf_r"] = r.get("profit_factor_r")
            elif fid == _FOLD_RECENT:
                d["recent_total_r"] = r.get("total_r")
                d["recent_pf_r"] = r.get("profit_factor_r")
        sr = _row(system_summary, sid)
        d["positive_fold_count"] = sr.get("positive_fold_count") if sr is not None else np.nan
        rows.append(d)
    return pd.DataFrame(rows)


def _interpret_delta(dt_r: float, dpfc: float, dconc: float, label: str) -> str:
    parts = []
    if np.isfinite(dt_r):
        parts.append(f"stitched_total_r {'+' if dt_r >= 0 else ''}{dt_r:.4f}")
    if np.isfinite(dpfc) and dpfc != 0:
        parts.append(f"Δpositive_folds={dpfc:+.0f}")
    if np.isfinite(dconc) and abs(dconc) > 0.01:
        parts.append(f"Δconcentration={dconc:+.4f}")
    if not parts:
        return f"(neutral / NA) — {label}"
    return "; ".join(parts) + f" — {label}"


def _diagnosis_conclusion(
    component_table: pd.DataFrame,
    incremental_table: pd.DataFrame,
    max_trades_sensitivity: pd.DataFrame,
    recent_vs_fullhistory: pd.DataFrame,
    fold_heatmap: pd.DataFrame,
) -> str:
    """Heuristic markdown conclusion — not a trading recommendation."""
    lines: list[str] = []
    lines.append("## Diagnosis conclusion (heuristic, not live-ready)")
    lines.append("")
    lines.append(
        "This section summarizes patterns in the tables above. It does **not** justify live trading "
        "or guarantee future performance."
    )
    lines.append("")

    if component_table.empty:
        lines.append("(No component table data.)")
        return "\n".join(lines)

    # Strongest single component by stitched_total_r
    ct = component_table.dropna(subset=["stitched_total_r"])
    if len(ct):
        w = ct.nlargest(1, "stitched_total_r").iloc[0]
        lines.append(
            f"1. **Strongest single-component headline (stitched total R):** `{w['system_id']}` "
            f"(stitched_total_r≈{_safe_float(w.get('stitched_total_r')):.4f})."
        )
    lines.append("")

    # Blame 2023/2024: sum y2023+y2024 total_r per component single
    if fold_heatmap.empty:
        lines.append("2. **2023/2024 weakness:** (no fold heatmap rows)")
    else:
        singles = fold_heatmap[fold_heatmap["system_id"].isin(_COMPONENT_SINGLE)].copy()
        if len(singles):
            singles["_early"] = (
                pd.to_numeric(singles.get("y2023_total_r"), errors="coerce").fillna(0)
                + pd.to_numeric(singles.get("y2024_total_r"), errors="coerce").fillna(0)
            )
            worst = singles.nsmallest(1, "_early").iloc[0]
            lines.append(
                f"2. **Largest combined 2023+2024 drag (among singles):** `{worst['system_id']}` "
                f"(y2023_total_r + y2024_total_r ≈ {_safe_float(worst.get('_early')):.4f})."
            )
        else:
            lines.append("2. **2023/2024:** (no single-component rows in heatmap)")
    lines.append("")

    lines.append(
        "3. **PRIOR_DAY_LEVEL_TRAP:** Compare `recent_trap_trio_mtd1` vs `recent_failed_gap_mtd1` "
        "in **incremental_table** — positive `delta_total_r` suggests the trap adds headline R; "
        "check **fold_heatmap** `recent_total_r` vs `y2023_total_r`/`y2024_total_r` for robustness vs recent-window upside."
    )
    lines.append("")
    lines.append(
        "4. **ORB_CONTINUATION / ORB_RETEST:** Compare `recent_opening_no_retest` vs `recent_opening_no_continuation` "
        "and vs `recent_opening_full_mtd2` in **fold_heatmap** — look for improved early-fold R without exploding concentration."
    )
    lines.append("")
    lines.append(
        "5. **max_trades_per_day=2:** See **max_trades_sensitivity** — `mtd2_helps_headline_r` and "
        "`mtd2_increases_concentration`; cross-check **fold_heatmap** `recent_total_r` vs older folds for the same system family."
    )
    lines.append("")
    if len(recent_vs_fullhistory):
        lines.append(
            "6. **Recent vs full-history candidates:** See **recent_vs_fullhistory** — negative "
            "`delta_fold_concentration_recent_minus_full` suggests full-hist paths are less single-fold dependent "
            "(not automatically better PnL)."
        )
    lines.append("")
    lines.append("### Mini-WFO readiness (decision support only)")
    lines.append("")
    lines.append(
        "- If **fullhist_failed_gap** pairs show more stable early folds and acceptable cost flags vs recent singles, "
        "a **narrow causal mini-WFO** could focus on **failed_orb + gap_acceptance** with **max_trades_per_day=1** first."
    )
    lines.append(
        "- If concentration remains extreme or mtd2 consistently worsens early folds, prefer **Layer 1 strategy-family work** "
        "before any mini-WFO."
    )
    lines.append("")

    return "\n".join(lines)


def write_diagnosis_report(
    output_root: Path,
    fold_summary: pd.DataFrame,
    system_summary: pd.DataFrame,
) -> Path:
    """Write diagnosis CSVs and `layer3_smoke_diagnosis_summary.md`."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    tables = build_component_diagnosis_tables(fold_summary, system_summary)

    name_map = {
        "component_table": "component_table.csv",
        "incremental_table": "incremental_table.csv",
        "max_trades_sensitivity": "max_trades_sensitivity.csv",
        "recent_vs_fullhistory": "recent_vs_fullhistory.csv",
        "fold_heatmap": "fold_heatmap.csv",
    }
    for key, fname in name_map.items():
        tables[key].to_csv(output_root / fname, index=False)

    md_lines: list[str] = []
    md_lines.append("# Layer 3 smoke — component diagnosis")
    md_lines.append("")
    md_lines.append(
        "**Not** full walk-forward. **Not** parameter optimization. **Not** live-ready. "
        "Explains Layer 3 smoke v1 patterns via fixed diagnostic systems."
    )
    md_lines.append("")
    md_lines.append("## Component singles")
    md_lines.append("")
    md_lines.append(_df_to_md(tables["component_table"]))
    md_lines.append("")
    md_lines.append("## Incremental comparisons")
    md_lines.append("")
    md_lines.append(_df_to_md(tables["incremental_table"]))
    md_lines.append("")
    md_lines.append("## Max trades per day (mtd1 vs mtd2)")
    md_lines.append("")
    md_lines.append(_df_to_md(tables["max_trades_sensitivity"]))
    md_lines.append("")
    md_lines.append("## Recent vs full-history candidate roots")
    md_lines.append("")
    md_lines.append(_df_to_md(tables["recent_vs_fullhistory"]))
    md_lines.append("")
    md_lines.append("## Fold heatmap")
    md_lines.append("")
    md_lines.append(_df_to_md(tables["fold_heatmap"]))
    md_lines.append("")
    md_lines.append(
        _diagnosis_conclusion(
            tables["component_table"],
            tables["incremental_table"],
            tables["max_trades_sensitivity"],
            tables["recent_vs_fullhistory"],
            tables["fold_heatmap"],
        )
    )
    md_lines.append("")

    path = output_root / "layer3_smoke_diagnosis_summary.md"
    path.write_text("\n".join(md_lines), encoding="utf-8")
    return path


def _df_to_md(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "(empty)"
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def main(argv: list[str] | None = None) -> int:
    """Regenerate diagnosis CSV/MD from saved fold_summary.csv + system_summary.csv."""
    import argparse

    p = argparse.ArgumentParser(description="Layer 3 component diagnosis from saved summaries.")
    p.add_argument("--root", required=True, type=Path, help="Folder with fold_summary.csv and system_summary.csv")
    args = p.parse_args(argv)
    root = Path(args.root)
    fs, ss = root / "fold_summary.csv", root / "system_summary.csv"
    if not fs.is_file() or not ss.is_file():
        raise SystemExit(f"missing fold_summary or system_summary under {root}")
    write_diagnosis_report(root, pd.read_csv(fs), pd.read_csv(ss))
    print(f"wrote diagnosis artifacts under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
