"""Train-only frozen-system selection for Layer 3 mini-WFO (pure helpers + validation)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PRIMARY_ALLOWED = frozenset({"failed_orb", "gap_acceptance_failure", "prior_day_level_trap"})


class MiniWFOValidationError(ValueError):
    pass


def layer2_raw_combo_count(grid: dict[str, Any]) -> int:
    keys = list(grid.keys())
    lists: list[list[Any]] = []
    for k in keys:
        v = grid[k]
        if isinstance(v, list):
            lists.append(v)
        else:
            lists.append([v])
    return len(list(product(*lists))) if lists else 0


def validate_mini_wfo_config(cfg: dict[str, Any]) -> None:
    errs: list[str] = []
    sym = str(cfg.get("symbol", "")).upper().strip()
    if sym != "QQQ":
        errs.append("symbol must be QQQ")
    if str(cfg.get("asset", "")).strip() != "equity":
        errs.append("asset must be equity")
    if sym == "SPY":
        errs.append("SPY not allowed")

    tr = cfg.get("train") or {}
    te = cfg.get("test") or {}
    ts = str(tr.get("start", "")).strip()
    te_train_end = str(tr.get("end", "")).strip()
    test_start = str(te.get("start", "")).strip()
    test_end = str(te.get("end", "")).strip()
    if not (ts < te_train_end < test_end):
        errs.append("require train.start < train.end < test.end")
    if te_train_end >= test_start:
        errs.append("train window must end before test.start (no overlap)")

    exp = cfg.get("experiment") or {}
    if exp.get("live_ready") is True:
        errs.append("live_ready must not be true")

    paths = cfg.get("paths") or {}
    out_root = str(paths.get("output_root", "")).strip()
    if not out_root:
        errs.append("paths.output_root required")

    ex = cfg.get("execution") or {}
    if int(ex.get("max_open_positions", -1)) != 1:
        errs.append("execution.max_open_positions must be 1")

    l1 = cfg.get("layer1") or {}
    for s in l1.get("strategies") or []:
        if str(s).upper() == "SPY":
            errs.append("SPY not allowed in layer1.strategies")
        if str(s) not in PRIMARY_ALLOWED:
            errs.append(f"unsupported primary strategy: {s}")
    for s in l1.get("allow_optional_diagnostics") or []:
        if str(s).upper() == "SPY":
            errs.append("SPY not allowed in diagnostics")
        if str(s) not in PRIMARY_ALLOWED:
            errs.append(f"unsupported diagnostic strategy: {s}")

    if errs:
        raise MiniWFOValidationError("; ".join(errs))


def load_candidate_warnings(selected_candidates_csv: Path) -> dict[str, str]:
    if not selected_candidates_csv.is_file():
        return {}
    df = pd.read_csv(selected_candidates_csv)
    if "candidate_id" not in df.columns:
        return {}
    out: dict[str, str] = {}
    for _, r in df.iterrows():
        cid = str(r.get("candidate_id", "")).strip()
        w = str(r.get("warning", "") or "").strip()
        if cid:
            out[cid] = w
    return out


def _pf_r_ok(v: Any) -> bool:
    try:
        return float(v) > 1.0
    except (TypeError, ValueError):
        return False


def _parse_ids(cell: Any) -> list[str]:
    if isinstance(cell, str) and cell.strip().startswith("["):
        try:
            return list(json.loads(cell))
        except json.JSONDecodeError:
            pass
    return []


def filter_eligible_train_systems(
    df: pd.DataFrame,
    *,
    sel: dict[str, Any],
    cost_slip_002_by_unique_rank: dict[int, float] | None,
    warnings_by_candidate: dict[str, str],
) -> pd.DataFrame:
    """Apply Layer 2 train selection gates from mini-WFO YAML."""
    if df is None or len(df) == 0:
        return pd.DataFrame()

    out = df.copy()
    min_tr = int(sel.get("require_min_trades", 0) or 0)
    if "trades" in out.columns:
        out = out[out["trades"].astype(float) >= float(min_tr)]

    if sel.get("require_positive_total_r") and "total_r" in out.columns:
        out = out[out["total_r"].astype(float) > 0]

    if sel.get("require_pf_r_above_1"):
        if "profit_factor_r" in out.columns:
            out = out[out["profit_factor_r"].apply(_pf_r_ok)]
        elif "profit_factor" in out.columns:
            out = out[out["profit_factor"].astype(float) > 1.0]

    floor = float(sel.get("max_drawdown_r_floor", -50.0))
    if "max_drawdown_r" in out.columns:
        out = out[out["max_drawdown_r"].astype(float) >= floor]

    if (
        sel.get("require_cost_0_02_positive")
        and cost_slip_002_by_unique_rank is not None
        and "unique_rank" in out.columns
    ):

        def _ok(r: pd.Series) -> bool:
            ur = int(r["unique_rank"])
            tr = cost_slip_002_by_unique_rank.get(ur)
            return tr is not None and float(tr) > 0.0

        out = out[out.apply(_ok, axis=1)]

    if sel.get("penalize_relaxed_candidates") and warnings_by_candidate:
        # Rows whose candidate_ids reference any warned Layer 1 YAML get deprioritized via score penalty later.
        pass

    return out.reset_index(drop=True)


def selection_sort_score(
    row: pd.Series,
    *,
    primary_sets: set[str],
    diagnostic_sets: set[str],
    penalize_relaxed: bool,
    warnings_by_candidate: dict[str, str],
    slip002_total_r: float | None,
) -> float:
    """Higher is better; used to rank remaining systems after hard filters."""
    cs = float(row.get("combiner_score", 0.0) or 0.0)
    tr = float(row.get("total_r", 0.0) or 0.0)
    dd = float(row.get("max_drawdown_r", -99.0) or 0.0)
    mtd = int(row.get("max_trades_per_day", 99) or 99)
    cset = str(row.get("candidate_set", ""))

    bonus = 0.0
    if cset in primary_sets:
        bonus += 2.0
    if cset in diagnostic_sets:
        bonus -= 1.5

    pen = 0.0
    if penalize_relaxed:
        ids = _parse_ids(row.get("candidate_ids_json"))
        if any(str(warnings_by_candidate.get(i, "")).strip() for i in ids):
            pen += 3.0

    mtd_bonus = 0.25 if mtd == 1 else 0.0

    slip_bonus = 0.0
    if slip002_total_r is not None:
        slip_bonus = 0.01 * max(0.0, float(slip002_total_r))

    # Prefer lower magnitude drawdown (dd is negative).
    dd_term = 0.02 * float(dd)

    return cs + 0.05 * tr + bonus + mtd_bonus + slip_bonus + dd_term - pen


def pick_best_row(
    df: pd.DataFrame,
    *,
    primary_sets: list[str],
    diagnostic_sets: list[str],
    sel: dict[str, Any],
    warnings_by_candidate: dict[str, str],
    cost_df: pd.DataFrame | None,
) -> tuple[pd.Series | None, dict[str, Any]]:
    """Return best row and audit metadata."""
    primary = set(primary_sets)
    diagnostic = set(diagnostic_sets)

    slip002_by_ur: dict[int, float] | None = None
    if cost_df is not None and len(cost_df) and "unique_rank" in cost_df.columns:
        sub = cost_df[cost_df["slippage_per_share"].astype(float).sub(0.02).abs() < 1e-9]
        slip002_by_ur = {}
        for ur, g in sub.groupby("unique_rank"):
            slip002_by_ur[int(ur)] = float(g.iloc[0].get("total_r", 0.0) or 0.0)

    eligible = filter_eligible_train_systems(
        df,
        sel=sel,
        cost_slip_002_by_unique_rank=slip002_by_ur,
        warnings_by_candidate=warnings_by_candidate,
    )
    audit = {
        "input_rows": int(len(df)),
        "after_hard_filters": int(len(eligible)),
    }
    if eligible.empty:
        return None, audit

    scores: list[float] = []
    for _, r in eligible.iterrows():
        ur = int(r["unique_rank"]) if "unique_rank" in r.index else -1
        s002 = slip002_by_ur.get(ur) if slip002_by_ur else None
        scores.append(
            selection_sort_score(
                r,
                primary_sets=primary,
                diagnostic_sets=diagnostic,
                penalize_relaxed=bool(sel.get("penalize_relaxed_candidates")),
                warnings_by_candidate=warnings_by_candidate,
                slip002_total_r=s002,
            )
        )
    eligible = eligible.assign(_sel_score=scores).sort_values("_sel_score", ascending=False, na_position="last")
    best = eligible.iloc[0]
    audit["selected_candidate_set"] = str(best.get("candidate_set", ""))
    audit["selected_score"] = float(best["_sel_score"])
    return best.drop(labels=["_sel_score"]), audit


def frozen_system_yaml_schema_keys() -> frozenset[str]:
    return frozenset(
        {
            "system_id",
            "source",
            "candidate_root",
            "candidate_ids",
            "combiner",
            "cost",
            "selection_reason",
            "selection_metrics_train",
            "live_ready",
            "research_status",
        }
    )


def validate_frozen_system_yaml(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise ValueError("frozen system YAML must be a mapping")
    need = frozen_system_yaml_schema_keys()
    missing = sorted(need - set(doc.keys()))
    if missing:
        raise ValueError(f"selected_frozen_system.yaml missing keys: {missing}")
    if doc.get("live_ready") is not False:
        raise ValueError("live_ready must be false")


def mini_wfo_summary_expected_sections() -> list[str]:
    return [
        "# Layer 3 Mini-WFO v1 — QQQ 2023–2024 Train / 2025–2026 Test",
        "## 1. Purpose",
        "## 2. Train/test split",
        "## 3. Strategies included",
        "## 4. Train Layer 1 candidate summary",
        "## 5. Train Layer 2 selection",
        "## 6. Frozen system",
        "## 7. Test result",
        "## 8. Monthly stability",
        "## 9. Comparison to fixed smoke",
        "## 10. Decision",
        "## 11. Recommendation",
    ]


def render_mini_wfo_summary_md(
    *,
    decision: str,
    train_window: tuple[str, str],
    test_window: tuple[str, str],
    body_extra: str = "",
) -> str:
    lines = [
        "# Layer 3 Mini-WFO v1 — QQQ 2023–2024 Train / 2025–2026 Test",
        "",
        "## 1. Purpose",
        "",
        "Single causal mini-WFO: train-only selection, one held-out test. Not full WFO; not live-ready.",
        "",
        "## 2. Train/test split",
        "",
        f"- Train: **{train_window[0]}** → **{train_window[1]}**",
        f"- Test: **{test_window[0]}** → **{test_window[1]}**",
        "",
        "## 3. Strategies included",
        "",
        "**Primary:** failed_orb, gap_acceptance_failure.",
        "**Diagnostic:** prior_day_level_trap (optional set only).",
        "**Excluded:** ORB_RETEST, ORB_CONTINUATION, VWAP — prior diagnosis flagged opening/trap/VWAP paths as noisy or unstable vs the gap/failed_orb core.",
        "",
        "## 4. Train Layer 1 candidate summary",
        "",
        "(Filled by mini-WFO runner from manifest + selected candidates.)",
        "",
        "## 5. Train Layer 2 selection",
        "",
        "(Filled by runner from behavior-unique / cost tables.)",
        "",
        "## 6. Frozen system",
        "",
        "(Filled by runner.)",
        "",
        "## 7. Test result",
        "",
        "(Filled by runner.)",
        "",
        "## 8. Monthly stability",
        "",
        "(Filled by runner.)",
        "",
        "## 9. Comparison to fixed smoke",
        "",
        "(Filled by runner.)",
        "",
        "## 10. Decision",
        "",
        f"**{decision}**",
        "",
        "## 11. Recommendation",
        "",
        "(Filled by runner based on decision.)",
        "",
    ]
    if body_extra.strip():
        lines.extend(["---", "", body_extra.strip(), ""])
    return "\n".join(lines)


@dataclass
class ComparisonRow:
    system: str
    source_type: str
    selected_using: str
    test_window: str
    trades: Any
    total_r: Any
    PF: Any
    PF_R: Any
    maxDD_r: Any
    slip_0_02_total_r: Any
    slip_0_03_total_r: Any
    interpretation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "source_type": self.source_type,
            "selected_using": self.selected_using,
            "test_window": self.test_window,
            "trades": self.trades,
            "total_r": self.total_r,
            "PF": self.PF,
            "PF_R": self.PF_R,
            "maxDD_r": self.maxDD_r,
            "slip_0_02_total_r": self.slip_0_02_total_r,
            "slip_0_03_total_r": self.slip_0_03_total_r,
            "interpretation": self.interpretation,
        }
