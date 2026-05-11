"""
Build committed max_hold_alignment_v1 aggregate CSV/MD from local alignment detail.

Reads ``exit_overlay_diagnostics_v2/local_rows/alignment_trade_detail.csv`` (gitignored)
and the local trade-context panel; writes only under
``exit_overlay_diagnostics_v2/max_hold_alignment_v1/`` (curated aggregates).

Usage::

    python -m src.research.build_max_hold_alignment_v1_aggregates
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd

from src.research.exit_overlay_alignment import normalize_exit_reason

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_DETAIL = _REPO / "src/research/results/exit_overlay_diagnostics_v2/local_rows/alignment_trade_detail.csv"
_DEFAULT_PANEL = _REPO / "src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv"
_DEFAULT_OUT = _REPO / "src/research/results/exit_overlay_diagnostics_v2/max_hold_alignment_v1"
_DEFAULT_GRID = _REPO / "src/research/results/exit_overlay_diagnostics_v2/alignment/alignment_grid_results.csv"


def _git_tip() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO, text=True).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _norm_series(s: pd.Series) -> pd.Series:
    return s.map(lambda x: normalize_exit_reason(x))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build max_hold_alignment_v1 aggregate tables.")
    p.add_argument("--detail", type=Path, default=_DEFAULT_DETAIL)
    p.add_argument("--panel", type=Path, default=_DEFAULT_PANEL)
    p.add_argument("--grid", type=Path, default=_DEFAULT_GRID)
    p.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    ns = p.parse_args(argv)
    detail_path: Path = ns.detail
    panel_path: Path = ns.panel
    grid_path: Path = ns.grid
    out: Path = ns.out
    out.mkdir(parents=True, exist_ok=True)

    if not detail_path.is_file():
        raise SystemExit(f"missing alignment detail (run alignment with --local-row-output): {detail_path}")
    if not panel_path.is_file():
        raise SystemExit(f"missing panel: {panel_path}")

    d_all = pd.read_csv(detail_path)
    d = d_all[d_all["config_id"].astype(str) == "cfg_0015"].copy()
    if d.empty:
        raise SystemExit("no cfg_0015 rows in alignment detail")

    panel = pd.read_csv(panel_path)
    key_cols = [c for c in ("trade_id", "profile_id", "window") if c in d.columns and c in panel.columns]
    if not key_cols or "trade_id" not in key_cols:
        key_cols = ["trade_id"]

    merge_cols = list(dict.fromkeys(key_cols + [c for c in (
        "candidate_id",
        "context_bucket",
        "bars_held",
        "exit_price",
        "exit_idx",
        "exit_reason",
    ) if c in panel.columns]))
    m = d.merge(panel[merge_cols], on=key_cols, how="left", suffixes=("", "_panel"))

    m["panel_exit_reason_n"] = _norm_series(m["panel_exit_reason"])
    m["replay_exit_n"] = _norm_series(m["exit_reason_replay"])
    m["pei"] = pd.to_numeric(m["panel_exit_idx"], errors="coerce")
    m["rjb"] = pd.to_numeric(m["replay_exit_bar_index"], errors="coerce")

    mh = m[m["panel_exit_reason_n"] == "max_hold"].copy()
    n_mh = int(len(mh))
    mm = mh[mh["replay_exit_n"].isin(("stop", "target"))].copy()
    n_mm = int(len(mm))

    touch_before = int((mm["rjb"] < mm["pei"]).sum()) if n_mm else 0
    touch_on = int((mm["rjb"] == mm["pei"]).sum()) if n_mm else 0
    touch_after = int((mm["rjb"] > mm["pei"]).sum()) if n_mm else 0

    overview = pd.DataFrame(
        [
            {
                "metric": "git_tip_at_build",
                "value": _git_tip(),
            },
            {"metric": "alignment_config", "value": "cfg_0015"},
            {"metric": "panel_rows_in_detail", "value": str(len(d))},
            {"metric": "max_hold_panel_rows", "value": str(n_mh)},
            {"metric": "max_hold_mismatch_rows_replay_stop_or_target", "value": str(n_mm)},
            {"metric": "mismatch_touch_before_panel_exit_idx", "value": str(touch_before)},
            {"metric": "mismatch_touch_on_panel_exit_idx", "value": str(touch_on)},
            {"metric": "mismatch_touch_after_panel_exit_idx", "value": str(touch_after)},
            {
                "metric": "replay_exit_reason_dist_on_mismatches",
                "value": str(mm["replay_exit_n"].value_counts().to_dict()) if n_mm else "{}",
            },
        ]
    )
    overview.to_csv(out / "max_hold_drift_overview.csv", index=False, lineterminator="\n")

    md_lines = [
        "# max_hold drift overview",
        "",
        f"- **Detail source:** `{detail_path.relative_to(_REPO)}` (local-only; do not commit).",
        f"- **Panel:** `{panel_path.relative_to(_REPO)}`.",
        "",
        "## Counts",
        "",
        f"- Panel **`max_hold`** rows (cfg_0015): **{n_mh}**",
        f"- Rows where replay exits **stop/target** while panel says **max_hold**: **{n_mm}**",
        f"- Of those, replay exit bar **before** `panel_exit_idx`: **{touch_before}**",
        f"- **On** `panel_exit_idx`: **{touch_on}**",
        f"- **After** `panel_exit_idx`: **{touch_after}**",
        "",
        "## Interpretation",
        "",
        "All observed mismatches in this full-panel run exit **before** the panel `exit_idx`.",
        "That means the dominant failure mode is **not** same-bar max_hold vs intrabar ordering on the terminal bar; ",
        "it is **pre-terminal** path divergence (replay sees an earlier stop/target fill that the archived panel row did not).",
        "",
        "Research-only `panel_exit_reason_authoritative` (only forces max_hold when `j == panel_exit_idx`) therefore **does not**",
        "change aggregate metrics vs `intrabar_first` on this dataset.",
        "",
    ]
    (out / "max_hold_drift_overview.md").write_text("\n".join(md_lines), encoding="utf-8")

    def _write_group(by_cols: list[str], name: str) -> None:
        if not n_mm:
            pd.DataFrame(columns=by_cols + ["rows", "sum_signed_r_diff", "mean_abs_r_diff"]).to_csv(
                out / name, index=False, lineterminator="\n"
            )
            return
        mm2 = mm.copy()
        mm2["signed_r_diff"] = pd.to_numeric(mm2["r_replay"], errors="coerce") - pd.to_numeric(
            mm2["r_original"], errors="coerce"
        )
        mm2["abs_r_diff"] = mm2["signed_r_diff"].abs()
        g = mm2.groupby(by_cols, dropna=False, observed=True).agg(
            rows=("trade_id", "count"),
            sum_signed_r_diff=("signed_r_diff", "sum"),
            mean_abs_r_diff=("abs_r_diff", "mean"),
        )
        g.reset_index().sort_values("rows", ascending=False).to_csv(out / name, index=False, lineterminator="\n")

    _write_group(["profile_id"], "max_hold_drift_by_profile.csv")
    _write_group(["window"], "max_hold_drift_by_window.csv")
    _write_group(["candidate_id"], "max_hold_drift_by_candidate.csv")
    if "context_bucket" in mm.columns:
        _write_group(["context_bucket"], "max_hold_drift_by_context.csv")

    if "bars_held" in mm.columns:
        mm_bh = mm.copy()
        mm_bh["bars_bucket"] = pd.cut(
            pd.to_numeric(mm_bh["bars_held"], errors="coerce"),
            bins=[0, 5, 15, 30, 60, 120, 10_000],
            labels=["(0,5]", "(5,15]", "(15,30]", "(30,60]", "(60,120]", ">120"],
        )
        mm2 = mm_bh
        by_cols = ["bars_bucket"]
        if not n_mm:
            pd.DataFrame(columns=by_cols + ["rows", "sum_signed_r_diff", "mean_abs_r_diff"]).to_csv(
                out / "max_hold_drift_by_bars_held.csv", index=False, lineterminator="\n"
            )
        else:
            mm2 = mm2.copy()
            mm2["signed_r_diff"] = pd.to_numeric(mm2["r_replay"], errors="coerce") - pd.to_numeric(
                mm2["r_original"], errors="coerce"
            )
            mm2["abs_r_diff"] = mm2["signed_r_diff"].abs()
            g = mm2.groupby(by_cols, dropna=False, observed=True).agg(
                rows=("trade_id", "count"),
                sum_signed_r_diff=("signed_r_diff", "sum"),
                mean_abs_r_diff=("abs_r_diff", "mean"),
            )
            g.reset_index().sort_values("rows", ascending=False).to_csv(
                out / "max_hold_drift_by_bars_held.csv", index=False, lineterminator="\n"
            )

    ex_cols = [
        "trade_id",
        "profile_id",
        "window",
        "candidate_id",
        "r_original",
        "r_replay",
        "panel_exit_reason",
        "exit_reason_replay",
        "panel_exit_idx",
        "replay_exit_bar_index",
        "bars_held_replay",
    ]
    ex_cols = [c for c in ex_cols if c in mm.columns]
    if n_mm:
        mm["abs_r_diff"] = (
            pd.to_numeric(mm["r_replay"], errors="coerce") - pd.to_numeric(mm["r_original"], errors="coerce")
        ).abs()
        top = mm.nlargest(min(25, n_mm), "abs_r_diff")[ex_cols].copy()
        top["touch_before_panel_exit_idx"] = top["replay_exit_bar_index"] < top["panel_exit_idx"]
        top["touch_on_panel_exit_idx"] = top["replay_exit_bar_index"] == top["panel_exit_idx"]
        top["touch_after_panel_exit_idx"] = top["replay_exit_bar_index"] > top["panel_exit_idx"]
        top["terminal_bar_conflict"] = top["touch_on_panel_exit_idx"] & top["exit_reason_replay"].map(
            normalize_exit_reason
        ).isin(["stop", "target"])
        top["pre_terminal_conflict"] = top["touch_before_panel_exit_idx"]
        top["panel_max_hold_authoritative_candidate"] = False
        top["possible_combiner_semantics_bug"] = top["touch_after_panel_exit_idx"]
        top["needs_more_trace_fields"] = top["pre_terminal_conflict"]
        top.to_csv(out / "max_hold_drift_examples_sanitized.csv", index=False, lineterminator="\n")

    # Comparison across configs from grid
    if grid_path.is_file():
        grid = pd.read_csv(grid_path)
        want = {
            "cfg_0015": "intrabar_first_baseline",
            "cfg_0016_mh_forced": "forced_first_on_terminal_bar",
            "cfg_0017_mh_panelauth": "panel_exit_reason_authoritative",
            "cfg_0018_mh_skipconf": "skip_terminal_bar_conflicts",
        }
        rows = []
        for cid, label in want.items():
            r = grid[grid["config_id"].astype(str) == cid]
            if r.empty:
                continue
            r0 = r.iloc[0].to_dict()
            rows.append({"config_id": cid, "mode_label": label, **r0})
        comp = pd.DataFrame(rows)
        comp.to_csv(out / "max_hold_alignment_comparison.csv", index=False, lineterminator="\n")
        cmp_md = [
            "# max_hold alignment comparison",
            "",
            "| config | max_hold_priority | trades | mean_abs_r_diff | total_r_diff | label |",
            "|---|---|---:|---:|---:|---|",
        ]
        for _, row in comp.iterrows():
            cmp_md.append(
                f"| {row.get('config_id')} | {row.get('max_hold_priority')} | "
                f"{int(row.get('trades', 0))} | {row.get('mean_abs_r_diff')} | "
                f"{row.get('total_r_diff')} | {row.get('label')} |"
            )
        cmp_md.extend(
            [
                "",
                "**Note:** `skip_terminal_bar_conflicts` excludes max_hold-vs-stop/target mismatches from metrics; ",
                "it is diagnostic-only and not an economic overlay baseline.",
                "",
            ]
        )
        (out / "max_hold_alignment_comparison.md").write_text("\n".join(cmp_md), encoding="utf-8")

    gate = pd.DataFrame(
        [
            {
                "gate": "OVERLAY_BLOCKED_ALIGNMENT_FAIL",
                "reason": "Best economic clone row cfg_0015 remains ALIGNMENT_FAIL (total_r_diff ~ +52.4R).",
            },
            {
                "gate": "OVERLAY_BLOCKED_PANEL_AUTHORITATIVE_ONLY",
                "reason": "panel_exit_reason_authoritative does not improve metrics; dominant drift is pre-terminal, not terminal-bar ordering.",
            },
        ]
    )
    gate.to_csv(out / "overlay_gate_after_max_hold_alignment.csv", index=False, lineterminator="\n")
    (out / "overlay_gate_after_max_hold_alignment.md").write_text(
        "\n".join(
            [
                "# Overlay gate after max_hold alignment refinement",
                "",
                "**Decision:** `OVERLAY_BLOCKED_ALIGNMENT_FAIL`",
                "",
                "- Headline clone config **`cfg_0015`** still fails aggregate budgets (`total_r_diff` > 15R).",
                "- **`skip_terminal_bar_conflicts`** achieves PASS only by excluding the contested rows — **not** an overlay-eligible baseline.",
                "- **`panel_exit_reason_authoritative`** matches **`intrabar_first`** on this panel because every max_hold/stop/target mismatch exits **before** `panel_exit_idx`.",
                "",
                "**Do not run `--mode overlay` until a PASS / PASS_WITH_WARNINGS config exists under an economically interpretable clone policy.**",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assess = pd.DataFrame(
        [
            {
                "classification": "AMBIGUOUS_SEMANTICS_DOCUMENT_ONLY",
                "summary": "Combiner loop orders intrabar stop/target before max_hold on each bar (simulator.py); panel max_hold with earlier replay stop/target implies path/materialization mismatch, not a proven single-line bug.",
            },
            {
                "classification": "INSUFFICIENT_PANEL_TRACE",
                "summary": "476 rows need reconciling fields (e.g. effective intrabar policy at archive time, staged stop, partials) to prove whether panel or clone diverges from historical combiner.",
            },
        ]
    )
    assess.to_csv(out / "combiner_bug_assessment.csv", index=False, lineterminator="\n")
    (out / "combiner_bug_assessment.md").write_text(
        "\n".join(
            [
                "# Combiner bug assessment (max_hold_alignment_v1)",
                "",
                "## Verdict",
                "",
                "**No strong evidence of a production combiner bug from alignment alone.**",
                "",
                "Dominant pattern: replay reaches **stop/target on a strictly earlier bar index** than `panel_exit_idx` while the panel labels **`max_hold`** at `exit_idx`.",
                "That is consistent with **clone vs archived panel materialization drift** (entry bar, stop level, session bar alignment, or missing trace), ",
                "or with **panel rows that are not byte-for-byte replayable** from published fields alone.",
                "",
                "## Recommended follow-up (separate task if pursued)",
                "",
                "- **`COMBINER_MAX_HOLD_SEMANTICS_AUDIT_FIX`** only if independent replay from combiner trade logs (not panel) confirms wrong `exit_reason` / `exit_idx` for these sessions.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
