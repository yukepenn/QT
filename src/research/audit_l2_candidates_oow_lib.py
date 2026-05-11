"""
Pure helpers for per-candidate Layer2 combiner OOW audit (research-only).

No strategy / candidate YAML edits. Labels are heuristic rules for triage, not optimization.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml

from src.research.fixed_profile_oow_lib import load_window_bounds


MIN_TRADES_SPARSE = 10
MIN_TRADES_ANTI = 20
WEAK_OOW_FLOOR = -3.0
STRONG_NEG = -5.0
INSAMPLE_POS = 5.0
HIGH_TPD = 1.15
WEAK_AVG_R = 0.03


@dataclass(frozen=True)
class CandidateMeta:
    candidate_id: str
    strategy: str
    strategy_family: str
    yaml_path: str
    selection_score: float | None
    warning: str
    side: str


def safe_run_segment(candidate_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", candidate_id.strip())


def parse_candidate_yaml(path: Path) -> CandidateMeta | None:
    try:
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    cid = str(d.get("candidate_id") or path.stem)
    strat = str(d.get("strategy") or "")
    fam = str(d.get("strategy_family") or (d.get("metadata") or {}).get("family") or strat)
    sel = (d.get("selection") or {}).get("score")
    warn = str((d.get("selection") or {}).get("warning") or "")
    score = float(sel) if sel is not None and str(sel).strip() != "" else None
    side = str(d.get("side") or "long").strip() or "long"
    return CandidateMeta(
        candidate_id=cid,
        strategy=strat,
        strategy_family=fam,
        yaml_path=str(path.as_posix()),
        selection_score=score,
        warning=warn,
        side=side,
    )


def iter_candidate_metas(candidate_root: Path) -> list[CandidateMeta]:
    out: list[CandidateMeta] = []
    for p in sorted(candidate_root.glob("*.yaml")):
        m = parse_candidate_yaml(p)
        if m and m.strategy:
            out.append(m)
    return out


def family_group(meta: CandidateMeta) -> str:
    s, f = meta.strategy.lower(), meta.strategy_family.lower()
    if "vwap" in s or "vwap" in f:
        return "vwap"
    if s in {
        "cci_extreme_snapback",
        "macd_momentum_turn",
        "rsi_failure_swing",
        "stochastic_oversold_cross",
        "supertrend_atr_flip",
    }:
        return "indicator"
    if s in {"failed_orb", "gap_acceptance_failure", "prior_day_level_trap", "multi_day_level_trap"}:
        return "opening_trap"
    if s.startswith("pa_"):
        return "pa"
    if "afternoon" in s:
        return "afternoon"
    return "other"


def filter_by_families(metas: Iterable[CandidateMeta], families: set[str] | None) -> list[CandidateMeta]:
    if not families:
        return list(metas)
    out = []
    for m in metas:
        g = family_group(m)
        if g in families or ("all" in families):
            out.append(m)
    return out


def discover_singleton_runs(runs_root: Path) -> list[tuple[str, str, Path]]:
    """Layout: runs_root/<candidate_segment>/<window_id>/run_*/metrics.json — latest run per pair."""
    runs_root = runs_root.resolve()
    if not runs_root.is_dir():
        return []
    best: dict[tuple[str, str], Path] = {}
    for mp in runs_root.glob("*/*/run_*/metrics.json"):
        run_dir = mp.parent
        parts = run_dir.relative_to(runs_root).parts
        if len(parts) < 3:
            continue
        cid, wid = parts[0], parts[1]
        key = (cid, wid)
        prev = best.get(key)
        if prev is None or run_dir.stat().st_mtime > prev.stat().st_mtime:
            best[key] = run_dir
    return [(c, w, d) for (c, w), d in sorted(best.items())]


def read_metrics_row(run_dir: Path, *, candidate_id: str, window_id: str, meta: CandidateMeta | None) -> dict[str, Any]:
    mj = run_dir / "metrics.json"
    if not mj.is_file():
        return {"candidate_id": candidate_id, "window_id": window_id, "status": "MISSING"}
    m = json.loads(mj.read_text(encoding="utf-8"))
    trades = int(m.get("trades") or 0)
    sess = int(m.get("active_days") or m.get("sessions") or 0)
    tpd = float(trades) / sess if sess else 0.0
    crp = run_dir / "config_resolved.yaml"
    st = en = ""
    if crp.is_file():
        try:
            cd = yaml.safe_load(crp.read_text(encoding="utf-8"))
            rd = (cd or {}).get("run") or {}
            st, en = str(rd.get("start", "")), str(rd.get("end", ""))
        except Exception:
            pass
    row: dict[str, Any] = {
        "candidate_id": candidate_id,
        "window_id": window_id,
        "status": "OK" if trades else "EMPTY",
        "strategy": meta.strategy if meta else "",
        "strategy_family": meta.strategy_family if meta else "",
        "yaml_path": meta.yaml_path if meta else "",
        "selection_score": meta.selection_score if meta else None,
        "warning": meta.warning if meta else "",
        "side": meta.side if meta else "",
        "audit_family": family_group(meta) if meta else "",
        "trades": trades,
        "sessions": sess,
        "total_r": float(m.get("total_r") or 0.0),
        "avg_r": float(m.get("avg_r") or 0.0),
        "median_r": float(m.get("median_r") or 0.0),
        "pf_r": float(m["profit_factor_r"]) if m.get("profit_factor_r") is not None else None,
        "win_rate": float(m.get("win_rate") or 0.0),
        "max_dd_r": float(m.get("max_drawdown_r") or 0.0),
        "target_count": int(m.get("target_count") or 0),
        "stop_count": int(m.get("stop_count") or 0),
        "eod_count": int(m.get("eod_count") or 0),
        "max_hold_count": int(m.get("max_hold_count") or 0),
        "trades_per_day": tpd,
        "avg_bars_held": float(m.get("avg_bars_held") or 0.0),
        "selection_rate": float(m.get("selection_rate") or 0.0),
        "rejected_signals": int(m.get("rejected_signals") or 0),
        "window_start": st,
        "window_end": en,
        "run_dir": str(run_dir),
    }
    return row


def assign_robustness_label(
    *,
    insample_r: float,
    early_r: float,
    late_r: float,
    insample_n: int,
    early_n: int,
    late_n: int,
    avg_r_in: float,
    tpd_in: float,
) -> str:
    def _bad_r(x: float) -> bool:
        return x != x  # NaN

    if _bad_r(insample_r) or _bad_r(early_r) or _bad_r(late_r):
        return "TOO_SPARSE"
    if min(insample_n, early_n, late_n) < MIN_TRADES_SPARSE:
        return "TOO_SPARSE"
    if insample_r > INSAMPLE_POS and early_r < STRONG_NEG and late_r < STRONG_NEG:
        return "INSAMPLE_ONLY"
    if (
        early_r < STRONG_NEG
        and late_r < STRONG_NEG
        and insample_r <= INSAMPLE_POS
        and min(insample_n, early_n, late_n) >= MIN_TRADES_ANTI
    ):
        return "ANTI_PREDICTIVE_CANDIDATE"
    if (early_r >= WEAK_OOW_FLOOR) != (late_r >= WEAK_OOW_FLOOR):
        return "OOW_MIXED"
    if early_r < WEAK_OOW_FLOOR and late_r < WEAK_OOW_FLOOR:
        return "OOW_NEGATIVE"
    if insample_r > INSAMPLE_POS and early_r >= WEAK_OOW_FLOOR and late_r >= WEAK_OOW_FLOOR:
        if tpd_in > HIGH_TPD and avg_r_in < WEAK_AVG_R:
            return "HIGH_TURNOVER_FRAGILE"
        return "ROBUST_POSITIVE"
    return "OOW_MIXED"


def merge_metrics_for_labels(long_df: pd.DataFrame) -> pd.DataFrame:
    """Wide pivot + labels using insample avg_r / tpd."""
    if long_df.empty:
        return pd.DataFrame()
    ok = long_df[long_df["status"] == "OK"].copy()
    if ok.empty:
        return pd.DataFrame()
    meta = ok.groupby("candidate_id").first()[["strategy", "strategy_family", "yaml_path", "selection_score", "warning", "side"]]
    piv_r = ok.pivot_table(index="candidate_id", columns="window_id", values="total_r", aggfunc="first")
    piv_n = ok.pivot_table(index="candidate_id", columns="window_id", values="trades", aggfunc="first")
    piv_a = ok.pivot_table(index="candidate_id", columns="window_id", values="avg_r", aggfunc="first")
    piv_t = ok.pivot_table(index="candidate_id", columns="window_id", values="trades_per_day", aggfunc="first")
    piv_r.columns = [f"total_r_{c}" for c in piv_r.columns]
    piv_n.columns = [f"trades_{c}" for c in piv_n.columns]
    piv_a.columns = [f"avg_r_{c}" for c in piv_a.columns]
    piv_t.columns = [f"tpd_{c}" for c in piv_t.columns]
    wide = meta.join(piv_r, how="inner").join(piv_n, how="left").join(piv_a, how="left").join(piv_t, how="left").reset_index()
    labels = []
    for _, r in wide.iterrows():
        def getf(prefix: str, w: str) -> float:
            c = f"{prefix}_{w}"
            return float(r[c]) if c in r and pd.notna(r[c]) else float("nan")

        def geti(prefix: str, w: str) -> int:
            c = f"{prefix}_{w}"
            v = r.get(c)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return 0
            return int(v)

        ins = getf("total_r", "insample_ref")
        early = getf("total_r", "early_oow")
        late = getf("total_r", "late_oow")
        ins_n, ea_n, la_n = geti("trades", "insample_ref"), geti("trades", "early_oow"), geti("trades", "late_oow")
        avg_in = getf("avg_r", "insample_ref")
        tpd_in = getf("tpd", "insample_ref")
        lab = assign_robustness_label(
            insample_r=ins,
            early_r=early,
            late_r=late,
            insample_n=ins_n,
            early_n=ea_n,
            late_n=la_n,
            avg_r_in=avg_in if pd.notna(avg_in) else 0.0,
            tpd_in=tpd_in if pd.notna(tpd_in) else 0.0,
        )
        labels.append(lab)
    wide["robustness_label"] = labels
    return wide


def policy_action_for_label(label: str) -> str:
    if label == "ROBUST_POSITIVE":
        return "KEEP_CORE_CANDIDATE"
    if label == "INSAMPLE_ONLY":
        return "DROP_FROM_CORE"
    if label == "ANTI_PREDICTIVE_CANDIDATE":
        return "REQUIRES_SIDE_FLIP_RESEARCH"
    if label == "TOO_SPARSE":
        return "TOO_SPARSE"
    if label == "HIGH_TURNOVER_FRAGILE":
        return "WATCHLIST_DIAGNOSTIC"
    if label in ("OOW_NEGATIVE", "OOW_MIXED"):
        return "WATCHLIST_DIAGNOSTIC"
    return "NEEDS_MORE_DATA"


def fixed_profile_strategy_candidates(
    *,
    fixed_profile_configs: dict[str, Path],
    candidate_root: Path,
) -> dict[str, list[str]]:
    """Map profile_id -> candidate_ids from YAMLs whose strategy is listed in that profile's combiner config."""
    out: dict[str, list[str]] = {}
    for pid, cfg_path in fixed_profile_configs.items():
        if not cfg_path.is_file():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        sets_cfg = cfg.get("candidate_sets") or {}
        strategies: set[str] = set()
        for _name, prof in sets_cfg.items():
            for s in (prof.get("strategies") or []):
                strategies.add(str(s))
        ids = []
        for m in iter_candidate_metas(candidate_root):
            if m.strategy in strategies:
                ids.append(m.candidate_id)
        out[pid] = sorted(set(ids))
    return out


def collect_long_metrics_frame(*, runs_root: Path, candidate_root: Path) -> pd.DataFrame:
    metas = {m.candidate_id: m for m in iter_candidate_metas(candidate_root)}
    rows: list[dict[str, Any]] = []
    for cid, wid, rdir in discover_singleton_runs(runs_root):
        m = metas.get(cid)
        rows.append(read_metrics_row(rdir, candidate_id=cid, window_id=wid, meta=m))
    return pd.DataFrame(rows)


def labels_table_from_wide(wide: pd.DataFrame) -> pd.DataFrame:
    if wide.empty:
        return pd.DataFrame(
            columns=[
                "candidate_id",
                "strategy",
                "strategy_family",
                "audit_family",
                "side",
                "yaml_path",
                "robustness_label",
                "policy_action",
                "total_r_insample_ref",
                "total_r_early_oow",
                "total_r_late_oow",
            ]
        )
    out = wide.copy()
    out["policy_action"] = out["robustness_label"].map(policy_action_for_label)

    def _fam_row(r: pd.Series) -> str:
        score = r.get("selection_score")
        sel = float(score) if pd.notna(score) else None
        m = CandidateMeta(
            candidate_id=str(r["candidate_id"]),
            strategy=str(r["strategy"]),
            strategy_family=str(r["strategy_family"]),
            yaml_path=str(r["yaml_path"]),
            selection_score=sel,
            warning=str(r.get("warning") or ""),
            side=str(r.get("side") or "long"),
        )
        return family_group(m)

    out["audit_family"] = out.apply(_fam_row, axis=1)
    cols = [
        "candidate_id",
        "strategy",
        "strategy_family",
        "audit_family",
        "side",
        "yaml_path",
        "robustness_label",
        "policy_action",
    ]
    for c in ("total_r_insample_ref", "total_r_early_oow", "total_r_late_oow", "trades_insample_ref", "trades_early_oow", "trades_late_oow"):
        if c not in out.columns:
            out[c] = pd.NA
    cols += [c for c in ("total_r_insample_ref", "total_r_early_oow", "total_r_late_oow", "trades_insample_ref", "trades_early_oow", "trades_late_oow") if c in out.columns]
    return out[cols]


def family_label_counts(wide_labeled: pd.DataFrame) -> pd.DataFrame:
    if wide_labeled.empty:
        return pd.DataFrame()
    base = labels_table_from_wide(wide_labeled)
    rows = []
    for fam, g in base.groupby("audit_family"):
        vc = g["robustness_label"].value_counts()
        rows.append(
            {
                "audit_family": fam,
                "candidates_audited": int(len(g)),
                "robust_positive": int(vc.get("ROBUST_POSITIVE", 0)),
                "insample_only": int(vc.get("INSAMPLE_ONLY", 0)),
                "oow_mixed": int(vc.get("OOW_MIXED", 0)),
                "oow_negative": int(vc.get("OOW_NEGATIVE", 0)),
                "too_sparse": int(vc.get("TOO_SPARSE", 0)),
                "high_turnover_fragile": int(vc.get("HIGH_TURNOVER_FRAGILE", 0)),
                "anti_predictive": int(vc.get("ANTI_PREDICTIVE_CANDIDATE", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("audit_family")


def strategy_label_counts(wide_labeled: pd.DataFrame) -> pd.DataFrame:
    if wide_labeled.empty:
        return pd.DataFrame()
    base = labels_table_from_wide(wide_labeled)
    rows = []
    for strat, g in base.groupby("strategy"):
        vc = g["robustness_label"].value_counts()
        rows.append(
            {
                "strategy": strat,
                "candidates_audited": int(len(g)),
                "robust_positive": int(vc.get("ROBUST_POSITIVE", 0)),
                "insample_only": int(vc.get("INSAMPLE_ONLY", 0)),
                "oow_negative": int(vc.get("OOW_NEGATIVE", 0)),
                "too_sparse": int(vc.get("TOO_SPARSE", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("strategy")
