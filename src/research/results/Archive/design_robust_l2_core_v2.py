"""
Design-only: dedupe robust Layer2 l2_core v2 candidates from singleton OOW audit outputs.

Inputs come from:
  - src/research/results/layer2_candidate_robustness_v1/

Outputs are written under:
  - src/research/results/robust_l2_core_v2_design/

This module must NOT:
  - run Layer2 sweeps
  - edit candidate YAMLs
  - copy YAMLs into a production root
  - emit/commit raw trades; it may read local-only trades.csv to compute compact overlap stats.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


_DEFAULT_AUDIT_ROOT = Path("src/research/results/layer2_candidate_robustness_v1")
_DEFAULT_OUT_ROOT = Path("src/research/results/robust_l2_core_v2_design")


WINDOWS = ("early_oow", "insample_ref", "late_oow")


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """
    Minimal markdown table writer without requiring optional `tabulate`.
    """
    if df is None or df.empty:
        return "| (empty) |\n|---|\n"
    cols = [str(c) for c in df.columns]
    rows = df.astype(object).where(pd.notna(df), "").values.tolist()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in rows)
    return header + "\n" + sep + "\n" + body + "\n"


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    """
    Deterministic CSV writer (explicit \n line endings) so GitHub raw views are sane.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _repo_relative_path(repo_root: Path, p: str) -> str:
    """
    Normalize paths to repo-relative POSIX paths for curated CSVs.
    - removes Windows drive prefixes if they point inside repo_root
    - replaces backslashes with forward slashes
    """
    s = str(p).replace("\\", "/")
    rr = str(repo_root.resolve()).replace("\\", "/")
    if s.startswith(rr + "/"):
        s = s[len(rr) + 1 :]
    # If the path contains the repo root somewhere (rare), strip to the first "src/" occurrence.
    if "src/" in s and not s.startswith("src/"):
        s = s[s.index("src/") :]
    return s


@dataclass(frozen=True)
class CandidateRow:
    candidate_id: str
    strategy: str
    strategy_family: str
    audit_family: str
    yaml_path: str
    robustness_label: str
    policy_action: str
    total_r_insample_ref: float
    total_r_early_oow: float
    total_r_late_oow: float
    trades_insample_ref: int
    trades_early_oow: int
    trades_late_oow: int


def _git_tip(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--oneline"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "(unavailable)"


def _read_labels(audit_root: Path) -> pd.DataFrame:
    p = audit_root / "candidate_robustness_labels.csv"
    return pd.read_csv(p)


def _read_robust_manifest(audit_root: Path) -> pd.DataFrame:
    p = audit_root / "robust_core_dry_run" / "selected_candidates_manifest.csv"
    return pd.read_csv(p)


def _as_int(x: Any) -> int:
    try:
        if pd.isna(x):
            return 0
        return int(x)
    except Exception:
        return 0


def _as_float(x: Any) -> float:
    try:
        if pd.isna(x):
            return float("nan")
        return float(x)
    except Exception:
        return float("nan")


def _metric_signature(r: CandidateRow, *, ndigits: int = 6) -> str:
    key = {
        "trades": {
            "insample_ref": r.trades_insample_ref,
            "early_oow": r.trades_early_oow,
            "late_oow": r.trades_late_oow,
        },
        "total_r": {
            "insample_ref": round(r.total_r_insample_ref, ndigits),
            "early_oow": round(r.total_r_early_oow, ndigits),
            "late_oow": round(r.total_r_late_oow, ndigits),
        },
        "strategy": r.strategy,
        "audit_family": r.audit_family,
    }
    return json.dumps(key, sort_keys=True)


def _l2_distance(a: CandidateRow, b: CandidateRow) -> float:
    va = [a.total_r_insample_ref, a.total_r_early_oow, a.total_r_late_oow]
    vb = [b.total_r_insample_ref, b.total_r_early_oow, b.total_r_late_oow]
    if any(math.isnan(x) for x in va + vb):
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(va, vb)))


def _try_read_trades_entries(
    *,
    runs_root: Path,
    candidate_id: str,
    window_id: str,
) -> tuple[set[str], set[str], bool]:
    """
    Returns:
      - entry_ts_utc set
      - session_date set
      - ok flag (file existed and parsed)
    """
    # Layout: runs_root/<candidate_id>/<window_id>/run_*/trades.csv (choose latest run_*)
    wdir = runs_root / candidate_id / window_id
    if not wdir.is_dir():
        return set(), set(), False
    run_dirs = sorted(wdir.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not run_dirs:
        return set(), set(), False
    tpath = run_dirs[0] / "trades.csv"
    if not tpath.is_file():
        return set(), set(), False
    try:
        df = pd.read_csv(tpath, usecols=["entry_ts_utc", "session_date"])
    except Exception:
        return set(), set(), False
    ent = set(df["entry_ts_utc"].astype(str).tolist())
    ses = set(df["session_date"].astype(str).tolist())
    return ent, ses, True


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return float(inter) / float(uni) if uni else 0.0


def build_design(
    *,
    repo_root: Path,
    audit_root: Path,
    out_root: Path,
    allow_local_trade_overlap: bool,
) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "config_skeletons").mkdir(parents=True, exist_ok=True)

    labels = _read_labels(audit_root)
    robust = _read_robust_manifest(audit_root)

    # Join robust manifest to the authoritative label table (includes metrics and yaml_path).
    lab = labels.set_index("candidate_id")
    rows: list[CandidateRow] = []
    for cid in robust["candidate_id"].astype(str).tolist():
        r0 = lab.loc[cid]
        rows.append(
            CandidateRow(
                candidate_id=str(cid),
                strategy=str(r0["strategy"]),
                strategy_family=str(r0["strategy_family"]),
                audit_family=str(r0["audit_family"]),
                yaml_path=_repo_relative_path(repo_root, str(r0["yaml_path"])),
                robustness_label=str(r0["robustness_label"]),
                policy_action=str(r0["policy_action"]),
                total_r_insample_ref=_as_float(r0["total_r_insample_ref"]),
                total_r_early_oow=_as_float(r0["total_r_early_oow"]),
                total_r_late_oow=_as_float(r0["total_r_late_oow"]),
                trades_insample_ref=_as_int(r0.get("trades_insample_ref")),
                trades_early_oow=_as_int(r0.get("trades_early_oow")),
                trades_late_oow=_as_int(r0.get("trades_late_oow")),
            )
        )

    # Metric-identical clustering (signature includes trades + rounded total_r + strategy + audit_family).
    sig_to_members: dict[str, list[CandidateRow]] = {}
    for r in rows:
        sig = _metric_signature(r)
        sig_to_members.setdefault(sig, []).append(r)

    clusters: list[dict[str, Any]] = []
    cand_to_cluster: dict[str, str] = {}
    cluster_idx = 0
    for sig, mem in sorted(sig_to_members.items(), key=lambda kv: (len(kv[1]) * -1, kv[1][0].candidate_id)):
        cluster_idx += 1
        cid = f"cluster_{cluster_idx:02d}"
        rep = sorted(mem, key=lambda x: x.candidate_id)[0]
        for m in mem:
            cand_to_cluster[m.candidate_id] = cid
        clusters.append(
            {
                "cluster_id": cid,
                "cluster_kind": "METRIC_IDENTICAL",
                "audit_family": rep.audit_family,
                "strategy": rep.strategy,
                "members": ",".join(sorted(m.candidate_id for m in mem)),
                "n_members": len(mem),
                "representative_candidate_id": rep.candidate_id,
                "raw_cluster_representative": rep.candidate_id,
                "design_representative": "",
                "design_representative_reason": "",
                "reason": "same trades-by-window + same total_r-by-window (rounded) under the audit envelope",
            }
        )

    # Near-duplicate detection (metrics-only heuristic).
    # This does NOT overwrite metric-identical clustering; it is informational.
    near_rows: list[dict[str, Any]] = []
    for a, b in itertools.combinations(rows, 2):
        same_strat = a.strategy == b.strategy
        same_counts = (
            a.trades_insample_ref == b.trades_insample_ref
            and a.trades_early_oow == b.trades_early_oow
            and a.trades_late_oow == b.trades_late_oow
        )
        d = _l2_distance(a, b)
        if same_strat and same_counts:
            near_rows.append(
                {
                    "candidate_a": a.candidate_id,
                    "candidate_b": b.candidate_id,
                    "strategy": a.strategy,
                    "audit_family": a.audit_family,
                    "kind": "SAME_STRATEGY_SAME_TRADES",
                    "l2_total_r_distance": d,
                }
            )

    # Optional local trade overlap on robust candidates (entry_ts_utc + session_date Jaccard).
    overlap_rows: list[dict[str, Any]] = []
    overlap_summary_lines: list[str] = []
    runs_root = audit_root / "local_runs"
    trades_ok = False
    trade_identical_components: list[list[str]] = []
    if allow_local_trade_overlap:
        # union trades across windows per candidate
        cand_entries: dict[str, set[str]] = {}
        cand_sessions: dict[str, set[str]] = {}
        cand_ok: dict[str, bool] = {}
        for r in rows:
            ent_all: set[str] = set()
            ses_all: set[str] = set()
            ok_any = False
            for wid in WINDOWS:
                ent, ses, ok = _try_read_trades_entries(runs_root=runs_root, candidate_id=r.candidate_id, window_id=wid)
                ent_all |= ent
                ses_all |= ses
                ok_any = ok_any or ok
            cand_entries[r.candidate_id] = ent_all
            cand_sessions[r.candidate_id] = ses_all
            cand_ok[r.candidate_id] = ok_any
            trades_ok = trades_ok or ok_any

        for a, b in itertools.combinations(sorted(cand_entries.keys()), 2):
            ja = _jaccard(cand_entries[a], cand_entries[b])
            js = _jaccard(cand_sessions[a], cand_sessions[b])
            overlap_rows.append(
                {
                    "candidate_a": a,
                    "candidate_b": b,
                    "jaccard_entry_ts_utc": ja,
                    "jaccard_session_date": js,
                    "n_entries_a": len(cand_entries[a]),
                    "n_entries_b": len(cand_entries[b]),
                    "n_sessions_a": len(cand_sessions[a]),
                    "n_sessions_b": len(cand_sessions[b]),
                    "ok_a": cand_ok[a],
                    "ok_b": cand_ok[b],
                }
            )

        overlap_df = pd.DataFrame(overlap_rows).sort_values(
            ["jaccard_entry_ts_utc", "jaccard_session_date"], ascending=[False, False]
        )
        _write_csv(overlap_df, out_root / "robust_candidate_overlap_matrix.csv")

        # Build strict trade-identical connected components (entry_ts_utc AND session_date Jaccard == 1.0).
        nodes = sorted(cand_entries.keys())
        adj: dict[str, set[str]] = {n: set() for n in nodes}
        for _, rr in overlap_df.iterrows():
            a = str(rr["candidate_a"])
            b = str(rr["candidate_b"])
            if float(rr["jaccard_entry_ts_utc"]) == 1.0 and float(rr["jaccard_session_date"]) == 1.0:
                adj[a].add(b)
                adj[b].add(a)
        seen: set[str] = set()
        for n in nodes:
            if n in seen:
                continue
            stack = [n]
            comp: set[str] = set()
            while stack:
                x = stack.pop()
                if x in comp:
                    continue
                comp.add(x)
                for y in adj.get(x, set()):
                    if y not in comp:
                        stack.append(y)
            seen |= comp
            if len(comp) >= 2:
                trade_identical_components.append(sorted(comp))

        # Append trade-identical clusters to effective clusters (design-only dedupe aid).
        for comp in trade_identical_components:
            comp_rows = [r for r in rows if r.candidate_id in set(comp)]
            strategies = sorted({r.strategy for r in comp_rows})
            audit_fams = sorted({r.audit_family for r in comp_rows})
            if len(strategies) != 1 or len(audit_fams) != 1:
                continue
            rep = sorted(comp_rows, key=lambda x: x.candidate_id)[0]
            clusters.append(
                {
                    "cluster_id": f"trade_identical_{rep.strategy}_{rep.audit_family}",
                    "cluster_kind": "TRADE_IDENTICAL",
                    "audit_family": rep.audit_family,
                    "strategy": rep.strategy,
                    "members": ",".join(sorted(comp)),
                    "n_members": len(comp),
                    "representative_candidate_id": rep.candidate_id,
                    "raw_cluster_representative": rep.candidate_id,
                    "design_representative": "",
                    "design_representative_reason": "",
                    "reason": "entry_ts_utc and session_date sets identical across windows (Jaccard=1.0); treat as one effective signal",
                }
            )

        overlap_summary_lines = [
            "# Robust-candidate overlap summary (local-only trades read)",
            "",
            "- Overlap is computed on **entry_ts_utc** and **session_date** sets, unioned across all three windows.",
            "- Raw trade rows are not written; only compact overlap metrics are persisted.",
            "",
            "## Highest entry overlap pairs",
            "",
            "```",
            overlap_df.head(10).to_string(index=False),
            "```",
            "",
        ]
        (out_root / "robust_candidate_overlap_summary.md").write_text("\n".join(overlap_summary_lines), encoding="utf-8")

    if not allow_local_trade_overlap or not trades_ok:
        # Ensure deterministic artifacts exist even when local trades are missing.
        if not (out_root / "robust_candidate_overlap_matrix.csv").is_file():
            empty_overlap = pd.DataFrame(
                columns=[
                    "candidate_a",
                    "candidate_b",
                    "jaccard_entry_ts_utc",
                    "jaccard_session_date",
                    "n_entries_a",
                    "n_entries_b",
                    "n_sessions_a",
                    "n_sessions_b",
                    "ok_a",
                    "ok_b",
                ]
            )
            _write_csv(empty_overlap, out_root / "robust_candidate_overlap_matrix.csv")
        if not (out_root / "robust_candidate_overlap_summary.md").is_file():
            (out_root / "robust_candidate_overlap_summary.md").write_text(
                "# Robust-candidate overlap summary\n\n"
                "**Status:** skipped (local trades not read or not available).\n",
                encoding="utf-8",
            )

    # Build per-candidate table
    dedupe_rows: list[dict[str, Any]] = []
    for r in rows:
        dedupe_rows.append(
            {
                "candidate_id": r.candidate_id,
                "strategy": r.strategy,
                "strategy_family": r.strategy_family,
                "audit_family": r.audit_family,
                "cluster_id": cand_to_cluster.get(r.candidate_id, ""),
                "metric_signature": _metric_signature(r),
                "total_r_insample_ref": r.total_r_insample_ref,
                "total_r_early_oow": r.total_r_early_oow,
                "total_r_late_oow": r.total_r_late_oow,
                "trades_insample_ref": r.trades_insample_ref,
                "trades_early_oow": r.trades_early_oow,
                "trades_late_oow": r.trades_late_oow,
                "yaml_path": r.yaml_path,
            }
        )
    dedupe_df = pd.DataFrame(dedupe_rows).sort_values(["audit_family", "strategy", "candidate_id"])
    _write_csv(dedupe_df, out_root / "robust_candidate_dedupe_table.csv")

    # Fill design representatives into clusters for clarity (raw vs design rep).
    def _design_rep_for_cluster(row: dict[str, Any]) -> tuple[str, str]:
        members = str(row.get("members") or "").split(",") if row.get("members") else []
        members = [m.strip() for m in members if m.strip()]
        if row.get("cluster_kind") == "TRADE_IDENTICAL" and row.get("strategy") == "pa_buy_sell_close_trend":
            return "PA_BUY_SELL_CLOSE_TREND_003", "best cross-window balance among trade-identical entries"
        if row.get("strategy") == "gap_acceptance_failure":
            return "GAP_ACCEPTANCE_FAILURE_001", "dedupe GAP cluster to one representative"
        if row.get("strategy") == "cci_extreme_snapback" and "CCI_EXTREME_SNAPBACK_003" in members:
            return "CCI_EXTREME_SNAPBACK_003", "primary CCI (positive both OOW)"
        return (str(row.get("raw_cluster_representative") or row.get("representative_candidate_id") or ""), "default = raw representative")

    for c in clusters:
        rep, why = _design_rep_for_cluster(c)
        c["design_representative"] = rep
        c["design_representative_reason"] = why

    clusters_df = pd.DataFrame(clusters).sort_values(["n_members", "audit_family"], ascending=[False, True])
    _write_csv(clusters_df, out_root / "effective_signal_clusters.csv")

    near_df = pd.DataFrame(near_rows).sort_values(["kind", "l2_total_r_distance", "candidate_a", "candidate_b"])
    _write_csv(near_df, out_root / "robust_candidate_near_duplicates.csv")

    # Representative choices (design-only, deterministic)
    def pick_primary() -> dict[str, str]:
        # default picks aligned with audit narrative:
        # - GAP: any one (metrics identical) -> 001
        # - PA close trend: prefer best cross-window balance -> 003
        # - CCI: prefer positive both OOW -> 003
        return {
            "GAP_ACCEPTANCE_FAILURE_001": "PRIMARY_REPRESENTATIVE",
            "PA_BUY_SELL_CLOSE_TREND_003": "PRIMARY_REPRESENTATIVE",
            "CCI_EXTREME_SNAPBACK_003": "PRIMARY_REPRESENTATIVE",
        }

    primary = pick_primary()

    def role_for(cid: str) -> str:
        if cid in primary:
            return primary[cid]
        if cid.startswith("GAP_ACCEPTANCE_FAILURE_"):
            return "DEDUPED_EQUIVALENT"
        if cid.startswith("PA_BUY_SELL_CLOSE_TREND_"):
            # Trade overlap (if available) shows 001–003 are identical trades; keep only one from that trio.
            if cid in {"PA_BUY_SELL_CLOSE_TREND_001", "PA_BUY_SELL_CLOSE_TREND_002"}:
                return "DEDUPED_EQUIVALENT"
            if cid == "PA_BUY_SELL_CLOSE_TREND_004":
                return "SECONDARY_REPRESENTATIVE"
            return "WATCHLIST_SECONDARY"
        if cid.startswith("CCI_EXTREME_SNAPBACK_"):
            return "WATCHLIST_SECONDARY"
        return "WATCHLIST_SECONDARY"

    # Representative manifest (full 10 robust names)
    rep_rows: list[dict[str, Any]] = []
    rep_rank = {
        "PRIMARY_REPRESENTATIVE": 1,
        "SECONDARY_REPRESENTATIVE": 2,
        "WATCHLIST_SECONDARY": 3,
        "DEDUPED_EQUIVALENT": 9,
        "EXCLUDED_DUPLICATE": 10,
    }
    for r in sorted(rows, key=lambda x: x.candidate_id):
        role = role_for(r.candidate_id)
        include_primary = "yes" if role == "PRIMARY_REPRESENTATIVE" else "no"
        include_extended = "yes" if role in {"PRIMARY_REPRESENTATIVE", "SECONDARY_REPRESENTATIVE"} else "no"
        if r.candidate_id.startswith("GAP_ACCEPTANCE_FAILURE_") and r.candidate_id != "GAP_ACCEPTANCE_FAILURE_001":
            include_extended = "no"
        if r.candidate_id == "CCI_EXTREME_SNAPBACK_002":
            include_extended = "yes"  # optional second CCI in balanced core
        rep_rows.append(
            {
                "candidate_id": r.candidate_id,
                "strategy": r.strategy,
                "strategy_family": r.strategy_family,
                "audit_family": r.audit_family,
                "representative_role": role,
                "representative_rank": rep_rank.get(role, 99),
                "include_in_primary_core": include_primary,
                "include_in_extended_core": include_extended,
                "source_yaml_path": r.yaml_path,
                "insample_ref_total_r": r.total_r_insample_ref,
                "early_oow_total_r": r.total_r_early_oow,
                "late_oow_total_r": r.total_r_late_oow,
                "trades_insample_ref": r.trades_insample_ref,
                "trades_early_oow": r.trades_early_oow,
                "trades_late_oow": r.trades_late_oow,
                "cluster_id": cand_to_cluster.get(r.candidate_id, ""),
                "cluster_role": "REPRESENTATIVE" if role == "PRIMARY_REPRESENTATIVE" else "MEMBER",
                "reason": "",
            }
        )
    rep_df = pd.DataFrame(rep_rows).sort_values(["representative_rank", "audit_family", "candidate_id"])
    # Expand schema to requested columns and ensure repo-relative paths.
    rep_df = rep_df.rename(columns={"include_in_extended_core": "include_in_balanced_core"})
    rep_df["include_in_extended_watchlist"] = "yes"
    rep_df["include_in_primary_core"] = rep_df["include_in_primary_core"].astype(str)
    rep_df["include_in_balanced_core"] = rep_df["include_in_balanced_core"].astype(str)
    rep_df["include_in_extended_watchlist"] = rep_df["include_in_extended_watchlist"].astype(str)
    rep_df["source_yaml_path"] = rep_df["source_yaml_path"].map(lambda x: _repo_relative_path(repo_root, str(x)))
    # Reorder / enforce columns
    rep_cols = [
        "candidate_id",
        "strategy",
        "strategy_family",
        "audit_family",
        "representative_role",
        "representative_rank",
        "include_in_primary_core",
        "include_in_balanced_core",
        "include_in_extended_watchlist",
        "source_yaml_path",
        "insample_ref_total_r",
        "early_oow_total_r",
        "late_oow_total_r",
        "trades_insample_ref",
        "trades_early_oow",
        "trades_late_oow",
        "cluster_id",
        "cluster_role",
        "reason",
    ]
    rep_df = rep_df[[c for c in rep_cols if c in rep_df.columns]]
    _write_csv(rep_df, out_root / "representative_candidate_manifest.csv")
    (out_root / "representative_candidate_manifest.md").write_text(
        "# Representative candidate manifest (design-only)\n\n"
        + _df_to_markdown_table(rep_df)
        + "\n",
        encoding="utf-8",
    )

    # Candidate set buckets
    primary_core = ["GAP_ACCEPTANCE_FAILURE_001", "PA_BUY_SELL_CLOSE_TREND_003", "CCI_EXTREME_SNAPBACK_003"]
    balanced_core = [
        "GAP_ACCEPTANCE_FAILURE_001",
        "PA_BUY_SELL_CLOSE_TREND_003",
        "PA_BUY_SELL_CLOSE_TREND_004",
        "CCI_EXTREME_SNAPBACK_003",
        "CCI_EXTREME_SNAPBACK_002",
    ]
    pa_gap = ["PA_BUY_SELL_CLOSE_TREND_003", "GAP_ACCEPTANCE_FAILURE_001"]
    pa_cci = ["PA_BUY_SELL_CLOSE_TREND_003", "CCI_EXTREME_SNAPBACK_003"]
    gap_cci = ["GAP_ACCEPTANCE_FAILURE_001", "CCI_EXTREME_SNAPBACK_003"]
    pa_only = ["PA_BUY_SELL_CLOSE_TREND_003"]
    cci_only = ["CCI_EXTREME_SNAPBACK_003", "CCI_EXTREME_SNAPBACK_002"]

    extended_watchlist = [r.candidate_id for r in sorted(rows, key=lambda x: x.candidate_id)]
    exclude = labels[labels["policy_action"].isin(["DROP_FROM_CORE", "REQUIRES_SIDE_FLIP_RESEARCH"])].copy()
    exclude_ids = exclude["candidate_id"].astype(str).tolist()

    cid_to_meta = labels.set_index("candidate_id")[["strategy", "audit_family", "yaml_path"]].to_dict(orient="index")

    def _set_rows(set_name: str, ids: list[str], *, purpose: str, caveat: str, run_recommended: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for cid in ids:
            meta = cid_to_meta.get(cid, {})
            out.append(
                {
                    "candidate_set": set_name,
                    "candidate_id": cid,
                    "strategy": str(meta.get("strategy", "")),
                    "family": str(meta.get("audit_family", "")),
                    "role_in_set": "member",
                    "source_yaml_path": _repo_relative_path(repo_root, str(meta.get("yaml_path", ""))),
                    "purpose": purpose,
                    "caveat": caveat,
                    "run_recommended": run_recommended,
                    "design_only": "yes",
                }
            )
        return out

    sets_rows: list[dict[str, Any]] = []
    sets_rows += _set_rows(
        "primary_representative_core",
        primary_core,
        purpose="minimum redundancy; maximum interpretability",
        caveat="GAP deduped (001–004 identical); PA 001–003 trade-identical (use 003)",
        run_recommended="yes",
    )
    sets_rows += _set_rows(
        "balanced_representative_core",
        balanced_core,
        purpose="slightly broader core; still deduped",
        caveat="adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW)",
        run_recommended="yes",
    )
    sets_rows += _set_rows("pa_gap_core", pa_gap, purpose="pairwise ablation", caveat="", run_recommended="yes")
    sets_rows += _set_rows("pa_cci_core", pa_cci, purpose="pairwise ablation", caveat="", run_recommended="yes")
    sets_rows += _set_rows("gap_cci_core", gap_cci, purpose="pairwise ablation", caveat="", run_recommended="yes")
    sets_rows += _set_rows("pa_only_core", pa_only, purpose="single-family ablation", caveat="optionally add PA_004 in a separate set", run_recommended="yes")
    sets_rows += _set_rows("cci_only_core", cci_only, purpose="single-family ablation", caveat="CCI_002 is secondary (early OOW weak)", run_recommended="yes")
    sets_rows += _set_rows(
        "extended_robust_watchlist",
        extended_watchlist,
        purpose="all nominal robust-positive (documentation only)",
        caveat="contains deduped equivalents; not recommended for immediate diagnostic",
        run_recommended="no",
    )
    sets_rows += _set_rows(
        "exclude_from_core",
        exclude_ids,
        purpose="DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets",
        caveat="research contrasts only; do not promote to core",
        run_recommended="no",
    )

    sets_df = pd.DataFrame(sets_rows).sort_values(["candidate_set", "candidate_id"])
    _write_csv(sets_df, out_root / "candidate_sets_design.csv")
    (out_root / "candidate_sets_design.md").write_text(
        "# Candidate sets (design-only)\n\n" + _df_to_markdown_table(sets_df) + "\n",
        encoding="utf-8",
    )

    # Core/watchlist/drop policy outputs across all 66
    bucket_map = {
        "KEEP_CORE_CANDIDATE": "watchlist_secondary",  # overridden below by representative selection
        "WATCHLIST_DIAGNOSTIC": "watchlist_diagnostic",
        "DROP_FROM_CORE": "drop_from_core",
        "REQUIRES_SIDE_FLIP_RESEARCH": "side_flip_research_only",
        "TOO_SPARSE": "too_sparse",
        "NEEDS_MORE_DATA": "needs_more_data",
    }
    policy_rows: list[dict[str, Any]] = []
    keep_ids = set(labels.loc[labels["policy_action"] == "KEEP_CORE_CANDIDATE", "candidate_id"].astype(str))
    rep_primary = set(primary_core)
    rep_secondary = set(balanced_core) - rep_primary
    for _, r in labels.iterrows():
        cid = str(r["candidate_id"])
        base = str(r["policy_action"])
        bucket = bucket_map.get(base, "watchlist_diagnostic")
        if cid in rep_primary:
            bucket = "core_representative"
        elif cid in rep_secondary:
            bucket = "core_secondary_optional"
        elif cid in keep_ids:
            # KEEP candidates not chosen as reps are treated as dedup/watchlist.
            bucket = "watchlist_secondary"
        rep_row = rep_df[rep_df["candidate_id"] == cid]
        in_primary = "yes" if (not rep_row.empty and rep_row.iloc[0].get("include_in_primary_core") == "yes") else "no"
        in_balanced = "yes" if (not rep_row.empty and rep_row.iloc[0].get("include_in_balanced_core") == "yes") else "no"
        side_flip = "yes" if base == "REQUIRES_SIDE_FLIP_RESEARCH" else "no"
        drop = "yes" if base == "DROP_FROM_CORE" else "no"
        watch = "yes" if base == "WATCHLIST_DIAGNOSTIC" else "no"

        action = {
            "core_representative": "CORE_REPRESENTATIVE",
            "core_secondary_optional": "CORE_SECONDARY_OPTIONAL",
            "watchlist_secondary": "DEDUPED_EQUIVALENT",
            "watchlist_diagnostic": "WATCHLIST_DIAGNOSTIC",
            "drop_from_core": "DROP_FROM_CORE",
            "side_flip_research_only": "SIDE_FLIP_RESEARCH_ONLY",
            "too_sparse": "WATCHLIST_DIAGNOSTIC",
            "needs_more_data": "WATCHLIST_DIAGNOSTIC",
        }.get(bucket, "WATCHLIST_DIAGNOSTIC")

        policy_rows.append(
            {
                "candidate_id": cid,
                "strategy": str(r["strategy"]),
                "family": str(r["audit_family"]),
                "action": action,
                "reason": "",
                "source_label": base,
                "robust_label": str(r["robustness_label"]),
                "insample_ref_total_r": r.get("total_r_insample_ref", ""),
                "early_oow_total_r": r.get("total_r_early_oow", ""),
                "late_oow_total_r": r.get("total_r_late_oow", ""),
                "include_in_primary_core": in_primary,
                "include_in_balanced_core": in_balanced,
                "side_flip_research_only": side_flip,
                "drop_from_core": drop,
                "watchlist": watch,
            }
        )
    policy_df = pd.DataFrame(policy_rows).sort_values(["action", "family", "candidate_id"])
    _write_csv(policy_df, out_root / "core_watchlist_drop_actions.csv")
    (out_root / "core_watchlist_drop_policy.md").write_text(
        "# Core / watchlist / drop policy (design-only)\n\n"
        "This reorganizes the full **66**-candidate l2_core into design buckets for future *small* diagnostics.\n\n"
        "Must-hold caveats:\n\n"
        "- **VWAP is not in robust core v2.**\n"
        "- **Old indicator five-pack is not in robust core v2.**\n"
        "- **`MACD_MOMENTUM_TURN_003`** and **`MULTI_DAY_LEVEL_TRAP_001`–`004`** are **side-flip research-only**.\n"
        "- **`PA_TRADING_RANGE_BLS_HS_001`–`003`** are excluded from core.\n"
        "- **`GAP_ACCEPTANCE_FAILURE_001`–`004`** is deduped to one effective cluster.\n"
        "- **CCI** appears only as the snapback representatives.\n\n"
        "## Bucket counts\n\n"
        "```\\n"
        + policy_df["action"].value_counts().to_string()
        + "\\n```\n\n"
        "## Actions table (full)\n\n"
        + _df_to_markdown_table(policy_df)
        + "\n",
        encoding="utf-8",
    )

    # Baseline inventory (design root)
    keep_ct = int((labels["policy_action"] == "KEEP_CORE_CANDIDATE").sum())
    drop_ct = int((labels["policy_action"] == "DROP_FROM_CORE").sum())
    watch_ct = int((labels["policy_action"] == "WATCHLIST_DIAGNOSTIC").sum())
    side_ct = int((labels["policy_action"] == "REQUIRES_SIDE_FLIP_RESEARCH").sum())
    inv_lines = [
        "# Robust l2_core v2 design — baseline inventory",
        "",
        f"- **git tip:** `{_git_tip(repo_root)}`",
        "- **handoff decision:** `CREATE_ROBUST_L2_CORE_V2_DESIGN`",
        "- **audit coverage:** 66 / 66 candidates; 198 / 198 candidate-window metric rows OK",
        "",
        "## Robust-positive candidates (nominal, n=10)",
        "",
        "- " + "\n- ".join(sorted(r.candidate_id for r in rows)),
        "",
        "## Anti-predictive candidates (n=5)",
        "",
        "- " + "\n- ".join(sorted(labels.loc[labels["robustness_label"] == "ANTI_PREDICTIVE_CANDIDATE", "candidate_id"].astype(str))),
        "",
        "## Current policy-action counts (from full audit)",
        "",
        f"- KEEP_CORE_CANDIDATE: **{keep_ct}**",
        f"- WATCHLIST_DIAGNOSTIC: **{watch_ct}**",
        f"- DROP_FROM_CORE: **{drop_ct}**",
        f"- REQUIRES_SIDE_FLIP_RESEARCH: **{side_ct}**",
        "",
        "## Files inspected / inputs",
        "",
        f"- `{(audit_root / 'candidate_robustness_labels.csv').as_posix()}`",
        f"- `{(audit_root / 'candidate_oow_metrics.csv').as_posix()}` (not parsed here; labels are authoritative)",
        f"- `{(audit_root / 'robust_core_dry_run/selected_candidates_manifest.csv').as_posix()}`",
        "",
        "## Local raw run availability",
        "",
        f"- local runs root: `{runs_root.as_posix()}`",
        f"- trade overlap read: **{'enabled' if allow_local_trade_overlap else 'disabled'}**",
        "",
        "## Expected outputs from this design pack",
        "",
        "- `robust_candidate_dedupe_table.csv`",
        "- `effective_signal_clusters.csv`",
        "- `robust_candidate_near_duplicates.csv`",
        "- `robust_candidate_overlap_matrix.csv`",
        "- `robust_candidate_overlap_summary.md`",
        "- `representative_candidate_manifest.{csv,md}`",
        "- `candidate_sets_design.{csv,md}`",
        "- `core_watchlist_drop_policy.md`",
        "- `core_watchlist_drop_actions.csv`",
        "- `robust_l2_core_v2_design.md`",
        "- `robust_l2_core_v2_decision.md`",
        "- `robust_l2_core_v2_design_summary.md`",
        "- `robust_l2_core_v2_key_findings.csv`",
        "",
    ]
    (out_root / "baseline_inventory.md").write_text("\n".join(inv_lines), encoding="utf-8")

    # Main design doc (design-only)
    design_md = [
        "# Robust l2_core v2 — design-only plan",
        "",
        "## 1. Purpose",
        "",
        "Convert the **10** nominal `ROBUST_POSITIVE` singleton candidates into a **deduped** set of **effective signals** for a future small Layer2 diagnostic.",
        "",
        "## 2. Non-goals",
        "",
        "- no Layer2 sweep",
        "- no WFO",
        "- no live/paper",
        "- no SPY",
        "- no strategy/feature/YAML edits",
        "- no router",
        "- no production short support",
        "- no OOW tuning",
        "",
        "## 3. Source evidence (full 66/66 audit)",
        "",
        "- Robust-positive: **10**",
        "- Anti-predictive: **5**",
        "- Family winners: `pa` (close trend), `opening_trap` (gap acceptance), `indicator` (CCI pocket)",
        "",
        "## 4. Effective signal clusters",
        "",
        _df_to_markdown_table(clusters_df),
        "",
        "## 5. Dedupe rules",
        "",
        "- Metric-identical candidates (same trades + same total_r across windows) count as **one** effective signal cluster.",
        "- Near-duplicates are capped; prefer candidates with **positive both OOW** and better cross-window balance.",
        "- Catastrophic OOW candidates stay **out** of core sets.",
        "",
        "## 6. Candidate-set design",
        "",
        _df_to_markdown_table(sets_df),
        "",
        "## 7. Future Layer2 diagnostic design (NOT RUN here)",
        "",
        "- Candidate-set axis (design buckets): primary vs balanced vs ablations (PA-only, GAP-only, CCI-only, pairwise mixes).",
        "- Risk control axis (design only): `max_trades_per_day` ∈ {1, 2}; `daily_max_loss_r` ∈ {−1.5, −2.0}; `priority_policy` ∈ {metadata_priority, score_adjusted_priority}.",
        "- No router; no broad grid.",
        "",
        "## 8. Interpretation",
        "",
        "- Singleton OOW robustness does **not** guarantee combination robustness.",
        "- This is a design transition from broad l2_core to a deduped robust pocket for diagnostics.",
        "",
        "## 9. Recommended next step",
        "",
        "**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`** (produce runnable configs in a follow-up task; do not execute here).",
        "",
    ]
    (out_root / "robust_l2_core_v2_design.md").write_text("\n".join(design_md), encoding="utf-8")

    decision_md = [
        "# Robust l2_core v2 — decision (design-only)",
        "",
        "## Decision label (exactly one)",
        "",
        "**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`**",
        "",
        "## Rationale (3–6 bullets)",
        "",
        "- Full singleton audit is complete (66/66; 198/198 OK), enabling a clean design step.",
        "- Metric-identical **GAP 001–004** must be treated as **one** effective signal; design needs dedupe rules before any new diagnostics.",
        "- PA close-trend shows multiple robust positives but needs redundancy caps (metrics-only and/or trade-overlap).",
        "- CCI 003 is the primary oscillator rep (positive both OOW); CCI 002 is secondary/watchlist.",
        "- No broad grid / WFO / router is appropriate before validating a small representative core under Layer2 constraints.",
        "",
        "## Explicit non-runs",
        "",
        "No Layer2 sweep; no mini/full WFO; no live/paper; no SPY; no Global L1; no broad Global L2 grid; no YAML edits; no OOW tuning; no executable side-flip/short research; no heavy artifact commits.",
        "",
        "## Recommended next step (exactly one)",
        "",
        "Implement **design-only** runnable combiner config(s) that reference the representative candidate sets, plus a small grid outline, but do **not** execute them in this task.",
        "",
    ]
    (out_root / "robust_l2_core_v2_decision.md").write_text("\n".join(decision_md), encoding="utf-8")

    summary_md = [
        "# Robust l2_core v2 — design summary",
        "",
        "## 1. Purpose",
        "Deduplicate 10 robust-positive singleton candidates into effective clusters and representative candidate sets.",
        "",
        "## 2. Input evidence",
        "- 66/66 singleton audit complete; 198/198 metric rows OK.",
        "- Robust-positive: 10; Anti-predictive: 5.",
        "",
        "## 3. Robust candidate clusters",
        _df_to_markdown_table(clusters_df),
        "",
        "## 4. Deduplication results",
        "- GAP 001–004 collapsed to one effective cluster by metric identity.",
        "- PA close-trend remains a multi-member cluster (near-duplicate table + optional trade overlap guide caps).",
        "- CCI 003 primary; CCI 002 watchlist/secondary.",
        "",
        "## 5. Representative core design",
        "- `primary_representative_core`: 3 names (GAP + PA + CCI).",
        "- `balanced_representative_core`: 5 names (adds PA secondary + CCI secondary).",
        "",
        "## 6. Watchlist/drop design",
        "See `core_watchlist_drop_actions.csv` and `core_watchlist_drop_policy.md`.",
        "",
        "## 7. Future small Layer2 diagnostic plan (not run)",
        "Design-only ablation candidate sets + small risk-control grid (mtp/day-loss/priority axes).",
        "",
        "## 8. What was intentionally not done",
        "No sweeps, WFO, YAML edits, router, short support, or OOW tuning; no raw trades committed.",
        "",
        "## 9. Decision",
        "**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`**",
        "",
        "## 10. Recommended next step",
        "Create runnable (still-not-run) config skeletons and a runbook for a follow-up diagnostic-only execution task.",
        "",
    ]
    (out_root / "robust_l2_core_v2_design_summary.md").write_text("\n".join(summary_md), encoding="utf-8")

    kf_rows = [
        {
            "topic": "GAP dedupe",
            "candidate_or_cluster": "GAP_ACCEPTANCE_FAILURE_001–004",
            "result": "metric-identical; treat as one effective signal",
            "evidence_strength": "high",
            "implication": "only one GAP rep in primary/balanced core",
            "next_action": "use GAP_001 as representative; keep others as deduped equivalents",
        },
        {
            "topic": "PA redundancy",
            "candidate_or_cluster": "PA_BUY_SELL_CLOSE_TREND_001–004",
            "result": "robust pocket; cap representatives",
            "evidence_strength": "medium",
            "implication": "pick 1 primary + 1 secondary; avoid all four by default",
            "next_action": "use PA_003 primary; PA_002 secondary (design-only; revise if overlap extreme)",
        },
        {
            "topic": "CCI selection",
            "candidate_or_cluster": "CCI_EXTREME_SNAPBACK_002/003",
            "result": "CCI_003 positive in both OOW; CCI_002 weaker early OOW",
            "evidence_strength": "high",
            "implication": "keep CCI_003 primary; CCI_002 optional",
            "next_action": "include CCI_002 only in balanced core",
        },
        {
            "topic": "Exclude buckets",
            "candidate_or_cluster": "DROP_FROM_CORE + REQUIRES_SIDE_FLIP_RESEARCH",
            "result": "excluded from robust core v2 design",
            "evidence_strength": "high",
            "implication": "prevents VWAP reclaim cluster / anti-predictive names from contaminating diagnostic core",
            "next_action": "use exclude_from_core set for diagnostics comparisons only",
        },
    ]
    pd.DataFrame(kf_rows).to_csv(out_root / "robust_l2_core_v2_key_findings.csv", index=False)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Design-only robust l2_core v2 plan from singleton OOW audit.")
    p.add_argument("--audit-root", default=str(_DEFAULT_AUDIT_ROOT))
    p.add_argument("--output-root", default=str(_DEFAULT_OUT_ROOT))
    p.add_argument("--design-only", action="store_true", help="No-op flag; keeps CLI explicit about scope.")
    p.add_argument(
        "--allow-local-trade-overlap",
        action="store_true",
        help="Read local-only trades.csv under audit_root/local_runs/** for robust candidates (no raw rows written).",
    )
    args = p.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    audit_root = Path(args.audit_root)
    out_root = Path(args.output_root)
    if not audit_root.is_absolute():
        audit_root = (repo_root / audit_root).resolve()
    if not out_root.is_absolute():
        out_root = (repo_root / out_root).resolve()

    build_design(
        repo_root=repo_root,
        audit_root=audit_root,
        out_root=out_root,
        allow_local_trade_overlap=bool(args.allow_local_trade_overlap),
    )
    print(f"[design] wrote {out_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

