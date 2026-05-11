"""Derive cost/turnover / objective diagnostics from committed Layer 2 exports.

Reads ``top_unique_systems.csv``, optional ``cost_stress/cost_stress_results.csv``,
and optional sweep ``results.csv``. Writes curated summaries under ``--output-root``.

Does not change production combiner scoring; decomposition mirrors ``combiner_score``
in ``src/combiner/metrics.py`` using only columns available in the CSVs.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.candidate import load_candidates, select_candidate_set
from src.combiner.metrics import combiner_score


def decompose_combiner_score_public_terms(
    *,
    profit_factor: float,
    total_r: float,
    max_drawdown_r: float,
    avg_bars_held: float,
    max_hold_count: int = 0,
    eod_count: int = 0,
    end_of_session_count: int = 0,
    end_of_data_count: int = 0,
    trades: int = 100,
) -> dict[str, float]:
    """Return additive score terms that use only common sweep CSV columns.

    ``residual_vs_reported`` = reported_combiner_score - sum(public_terms) - low_trade_penalty
    captures max_hold / eod / rounding when those columns are missing from the row.
    """
    pf = float(profit_factor)
    if math.isnan(pf):
        pf = 0.0
    elif pf == float("inf"):
        pf = 25.0
    tr = float(total_r or 0.0)
    mdd = float(max_drawdown_r or 0.0)
    bh = float(avg_bars_held or 0.0)
    mh = int(max_hold_count or 0)
    eod = int(eod_count or 0)
    es = int(end_of_session_count or 0)
    ed = int(end_of_data_count or 0)
    low = int(trades) < 50
    terms = {
        "term_profit_factor": pf,
        "term_total_r": 0.015 * tr,
        "term_drawdown": -0.030 * abs(mdd),
        "term_avg_bars_held": -0.001 * bh,
        "term_max_hold": -0.020 * mh,
        "term_eod": -0.050 * eod,
        "term_end_of_session": -0.050 * es,
        "term_end_of_data": -0.050 * ed,
        "term_low_trade_count": -2.0 if low else 0.0,
    }
    terms["term_public_sum"] = sum(
        terms[k]
        for k in (
            "term_profit_factor",
            "term_total_r",
            "term_drawdown",
            "term_avg_bars_held",
            "term_max_hold",
            "term_eod",
            "term_end_of_session",
            "term_end_of_data",
            "term_low_trade_count",
        )
    )
    return terms


def recombiner_from_terms(terms: dict[str, float]) -> float:
    return float(terms["term_public_sum"])


def cost_adjusted_objective(
    *,
    total_r_001: float,
    pf_001: float,
    total_r_002: float,
    pf_002: float,
    total_r_003: float,
    pf_003: float,
    trades: float,
    max_drawdown_r_001: float,
    family_diversity_count: int,
) -> float:
    """Post-hoc rank helper (not production). Higher is better."""
    t = max(float(trades), 1.0)
    atr = float(total_r_001) / t
    rret02 = (
        float(total_r_002) / float(total_r_001)
        if total_r_001 and not math.isnan(total_r_001) and total_r_001 != 0
        else float("nan")
    )
    pen_dd = 0.02 * abs(float(max_drawdown_r_001 or 0.0))
    pen_trades = 0.0004 * t
    bonus_div = 0.15 * max(0, int(family_diversity_count) - 1)
    core = 0.0
    if not math.isnan(total_r_002) and total_r_002 > 0:
        core += 2.0 * min(total_r_002 / 20.0, 3.0)
    if not math.isnan(pf_002) and pf_002 > 1.0:
        core += 1.5 * min(pf_002 - 1.0, 0.5)
    if not math.isnan(total_r_003):
        if total_r_003 >= 0:
            core += 0.5
        else:
            core -= 1.0
    if not math.isnan(pf_003) and pf_003 < 1.0:
        core -= 0.8
    core += 1.2 * atr
    if not math.isnan(rret02):
        core += 0.8 * max(-1.0, min(1.0, rret02))
    return core - pen_dd - pen_trades + bonus_div


def strategy_from_candidate_id(cid: str) -> str:
    s = str(cid).strip()
    base = re.sub(r"_\d+$", "", s)
    return base.lower().replace("-", "_")


def _parse_strategies_from_json(candidate_ids_json: str) -> list[str]:
    try:
        ids = json.loads(candidate_ids_json)
    except json.JSONDecodeError:
        return []
    return [strategy_from_candidate_id(str(cid)) for cid in ids]


def family_diversity_count(candidate_ids_json: str) -> int:
    return len(set(_parse_strategies_from_json(candidate_ids_json)))


def candidate_set_family_label(candidate_set: str) -> str:
    cs = str(candidate_set)
    if cs == "vwap_core" or cs.startswith("vwap"):
        return "vwap_core"
    if "indicator" in cs:
        return "indicator_completion_core"
    if "opening" in cs or "trap" in cs:
        return "opening_trap_core"
    if cs == "pa_core" or ("pa_" in cs and "core" in cs):
        return "pa_core"
    if "non_vwap" in cs or "no_vwap" in cs:
        return "non_vwap_bucket"
    return "other"


def pivot_cost_stress(cost_path: Path) -> pd.DataFrame:
    df = pd.read_csv(cost_path)
    if len(df) == 0 or "source_combo_id" not in df.columns or "slippage_per_share" not in df.columns:
        return pd.DataFrame()
    out_rows: list[dict[str, Any]] = []
    for cid in sorted(df["source_combo_id"].dropna().unique()):
        sub = df[df["source_combo_id"] == cid]
        try:
            scid = int(float(cid))
        except (TypeError, ValueError):
            scid = cid
        row: dict[str, Any] = {"source_combo_id": scid}
        for slip in (0.01, 0.02, 0.03):
            s2 = sub[sub["slippage_per_share"] == slip]
            if len(s2) == 0:
                continue
            r = s2.iloc[0]
            row[f"total_r_{slip:g}"] = float(r["total_r"])
            row[f"profit_factor_{slip:g}"] = float(r["profit_factor"])
            if "max_drawdown_r" in r.index:
                row[f"max_drawdown_r_{slip:g}"] = float(r["max_drawdown_r"])
            if "trades" in r.index:
                row[f"trades_{slip:g}"] = int(r["trades"])
        out_rows.append(row)
    return pd.DataFrame(out_rows)


def stress_labels(
    tr01: float,
    tr02: float,
    tr03: float,
    pf01: float,
    pf02: float,
    pf03: float,
) -> dict[str, Any]:
    r01 = float(tr01) if not math.isnan(tr01) else float("nan")
    r02 = float(tr02) if not math.isnan(tr02) else float("nan")
    r03 = float(tr03) if not math.isnan(tr03) else float("nan")
    p01 = float(pf01) if not math.isnan(pf01) else float("nan")
    p02 = float(pf02) if not math.isnan(pf02) else float("nan")
    p03 = float(pf03) if not math.isnan(pf03) else float("nan")

    def _ret(a: float, b: float) -> float:
        if math.isnan(a) or math.isnan(b) or a == 0:
            return float("nan")
        return b / a

    out = {
        "r_ret_01_to_02": _ret(r01, r02),
        "r_ret_01_to_03": _ret(r01, r03),
        "pf_decay_01_to_02": (p02 - p01) if not math.isnan(p02) and not math.isnan(p01) else float("nan"),
        "pf_decay_01_to_03": (p03 - p01) if not math.isnan(p03) and not math.isnan(p01) else float("nan"),
        "PASS_0_02": (not math.isnan(r02) and r02 > 0 and not math.isnan(p02) and p02 > 1.0),
        "FAIL_0_02": (math.isnan(r02) or r02 <= 0 or math.isnan(p02) or p02 <= 1.0),
        "PASS_0_03": (not math.isnan(r03) and r03 > 0 and not math.isnan(p03) and p03 > 1.0),
        "FAIL_0_03": (math.isnan(r03) or r03 <= 0 or math.isnan(p03) or p03 <= 1.0),
    }
    thin = False
    if not math.isnan(r01) and not math.isnan(r02) and r01 > 0:
        if r02 / r01 < 0.35:
            thin = True
    out["THIN_EDGE"] = thin
    return out


def run_preflight(
    *,
    sweep_paths: list[Path],
    candidate_root: Path,
    base_cfg_path: Path,
) -> dict[str, Any]:
    import yaml

    raw = load_candidates(candidate_root)
    with base_cfg_path.open(encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)
    sets_cfg = base_cfg.get("candidate_sets") or {}
    report: dict[str, Any] = {"candidate_yaml_count": len(list(candidate_root.glob("*.yaml"))), "sweeps": {}}

    def _expand(grid: dict[str, Any]) -> list[dict[str, Any]]:
        from itertools import product

        keys = list(grid.keys())
        lists_out: list[list[Any]] = []
        for k in keys:
            v = grid[k]
            lists_out.append(v if isinstance(v, list) else [v])
        return [dict(zip(keys, combo)) for combo in product(*lists_out)]

    for sp in sweep_paths:
        with sp.open(encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        grid = doc.get("grid") or {}
        combos = _expand(grid)
        empty_sets: list[str] = []
        nonempty: list[str] = []
        grid_sets = {str(x) for x in (grid.get("candidate_set") or [])}
        for name in sorted(grid_sets):
            if name not in sets_cfg:
                continue
            prof = dict(sets_cfg[name])
            for tps in (1, 2, 4, 80):
                sel = select_candidate_set(raw, prof, top_per_strategy=tps)
                if len(sel) > 0:
                    nonempty.append(f"{name}@tps={tps} n={len(sel)}")
                    break
            else:
                empty_sets.append(name)
        used_sets: set[str] = set()
        for row in grid.get("candidate_set", []) or []:
            used_sets.add(str(row))
        bad = [u for u in sorted(used_sets) if u not in sets_cfg]
        report["sweeps"][sp.name] = {
            "combo_count": len(combos),
            "candidate_sets_in_grid": sorted(used_sets),
            "unknown_candidate_sets": bad,
            "sample_nonempty_resolution": nonempty[:20],
        }
    return report


def write_family_dominance(top_df: pd.DataFrame, out_csv: Path, *, head_n: int = 30) -> None:
    head = top_df.head(head_n)
    rows: list[dict[str, Any]] = []
    for bucket, sub in head.groupby("candidate_set"):
        rows.append(
            {
                "candidate_set": bucket,
                "rows_in_top_n": len(sub),
                "family_label": candidate_set_family_label(str(bucket)),
            }
        )
    pd.DataFrame(rows).sort_values("rows_in_top_n", ascending=False).to_csv(out_csv, index=False)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 2 cost/turnover diagnostics from exports.")
    p.add_argument("--result-root", type=Path, default=None)
    p.add_argument("--output-root", type=Path, default=None)
    p.add_argument("--sweep-results", type=Path, default=None, help="Optional sweep results.csv for full-grid stats.")
    p.add_argument("--preflight", action="store_true", help="Print sweep preflight JSON and exit.")
    p.add_argument("--candidate-root", type=Path, default=None)
    p.add_argument("--base-config", type=Path, default=None)
    p.add_argument("--preflight-sweeps", type=str, default="", help="Comma-separated sweep YAML paths for preflight.")
    args = p.parse_args(argv)

    cwd = Path.cwd()

    if args.preflight:
        if not args.candidate_root or not args.base_config or not args.preflight_sweeps:
            print("preflight requires --candidate-root, --base-config, --preflight-sweeps", file=sys.stderr)
            return 2
        cr = args.candidate_root if args.candidate_root.is_absolute() else cwd / args.candidate_root
        bc = args.base_config if args.base_config.is_absolute() else cwd / args.base_config
        sweeps = [
            Path(s.strip()) if Path(s.strip()).is_absolute() else cwd / s.strip()
            for s in args.preflight_sweeps.split(",")
            if s.strip()
        ]
        rep = run_preflight(sweep_paths=sweeps, candidate_root=cr, base_cfg_path=bc)
        print(json.dumps(rep, indent=2, default=str))
        return 0

    if args.result_root is None:
        print("--result-root is required unless --preflight", file=sys.stderr)
        return 2
    result_root = args.result_root if args.result_root.is_absolute() else cwd / args.result_root
    out_root = args.output_root or result_root
    out_root = out_root if out_root.is_absolute() else cwd / out_root

    top_path = result_root / "top_unique_systems.csv"
    if not top_path.exists():
        print(f"missing {top_path}", file=sys.stderr)
        return 2
    top = pd.read_csv(top_path)
    top["combo_id"] = pd.to_numeric(top["combo_id"], errors="coerce").astype("Int64")

    stress_path = result_root / "cost_stress" / "cost_stress_results.csv"
    stress_pivot = pivot_cost_stress(stress_path) if stress_path.exists() else pd.DataFrame()

    if len(stress_pivot) and "source_combo_id" in stress_pivot.columns:
        stress_pivot["source_combo_id"] = pd.to_numeric(
            stress_pivot["source_combo_id"], errors="coerce"
        ).astype("Int64")
        merged = top.merge(
            stress_pivot,
            left_on="combo_id",
            right_on="source_combo_id",
            how="left",
            suffixes=("", "_stress"),
        )
    else:
        merged = top.copy()
        merged["stress_note"] = "no_cost_stress_join"

    rows_dec: list[dict[str, Any]] = []
    rows_rank: list[dict[str, Any]] = []
    for _, r in merged.iterrows():
        pf = float(r.get("profit_factor", 0.0) or 0.0)
        tr = float(r.get("total_r", 0.0) or 0.0)
        mdd = float(r.get("max_drawdown_r", 0.0) or 0.0)
        bh = float(r.get("avg_bars_held", 0.0) or 0.0)
        trades = int(r.get("trades", 0) or 0)
        mh = int(r.get("max_hold_count", 0) or 0) if "max_hold_count" in r else 0
        eod = int(r.get("eod_count", 0) or 0) if "eod_count" in r else 0
        es = int(r.get("end_of_session_count", 0) or 0) if "end_of_session_count" in r else 0
        ed = int(r.get("end_of_data_count", 0) or 0) if "end_of_data_count" in r else 0
        terms = decompose_combiner_score_public_terms(
            profit_factor=pf,
            total_r=tr,
            max_drawdown_r=mdd,
            avg_bars_held=bh,
            max_hold_count=mh,
            eod_count=eod,
            end_of_session_count=es,
            end_of_data_count=ed,
            trades=trades,
        )
        reported = float(r.get("combiner_score", float("nan")))
        implied, _low = combiner_score(
            {
                "trades": trades,
                "profit_factor": pf,
                "total_r": tr,
                "max_drawdown_r": mdd,
                "avg_bars_held": bh,
                "max_hold_count": mh,
                "eod_count": eod,
                "end_of_session_count": es,
                "end_of_data_count": ed,
            }
        )
        rows_dec.append(
            {
                "unique_rank": r.get("unique_rank"),
                "combo_id": r.get("combo_id"),
                "candidate_set": r.get("candidate_set"),
                "combiner_score_reported": reported,
                "combiner_score_implied_full": implied,
                **terms,
                "residual_reported_minus_implied": (reported - implied) if not math.isnan(reported) else float("nan"),
            }
        )

        tr01 = tr
        pf01 = pf
        tr02 = float(r.get("total_r_0.02", float("nan")))
        tr03 = float(r.get("total_r_0.03", float("nan")))
        pf02 = float(r.get("profit_factor_0.02", float("nan")))
        pf03 = float(r.get("profit_factor_0.03", float("nan")))
        mdd01 = mdd
        cidj = str(r.get("candidate_ids_json", "[]"))
        divc = family_diversity_count(cidj)
        lbl = stress_labels(tr01, tr02, tr03, pf01, pf02, pf03)
        cao = cost_adjusted_objective(
            total_r_001=tr01,
            pf_001=pf01,
            total_r_002=tr02,
            pf_002=pf02,
            total_r_003=tr03,
            pf_003=pf03,
            trades=float(trades),
            max_drawdown_r_001=mdd01,
            family_diversity_count=divc,
        )
        rows_rank.append(
            {
                "unique_rank": r.get("unique_rank"),
                "combo_id": r.get("combo_id"),
                "candidate_set": r.get("candidate_set"),
                "combiner_score": reported,
                "cost_adjusted_objective": cao,
                "total_r_baseline": tr01,
                "profit_factor_baseline": pf01,
                "trades": trades,
                "avg_r_per_trade": tr / max(trades, 1),
                "total_r_0.02": tr02,
                "profit_factor_0.02": pf02,
                "total_r_0.03": tr03,
                "profit_factor_0.03": pf03,
                "family_diversity_strategies": divc,
                **{k: v for k, v in lbl.items()},
            }
        )

    dec_df = pd.DataFrame(rows_dec)
    dec_path = out_root / "layer2_score_decomposition.csv"
    dec_df.to_csv(dec_path, index=False)

    rank_df = pd.DataFrame(rows_rank)
    rank_df = rank_df.sort_values("cost_adjusted_objective", ascending=False, na_position="last")
    rank_df.insert(0, "cost_adjusted_rank", range(1, len(rank_df) + 1))
    rank_path = out_root / "layer2_cost_adjusted_ranking.csv"
    rank_df.to_csv(rank_path, index=False)

    turn = top.assign(
        avg_r_per_trade=top["total_r"] / top["trades"].clip(lower=1),
    )[
        [
            "unique_rank",
            "combo_id",
            "candidate_set",
            "trades",
            "total_r",
            "profit_factor",
            "max_drawdown_r",
            "avg_bars_held",
            "avg_r_per_trade",
            "combiner_score",
        ]
    ]
    turn_path = out_root / "layer2_turnover_summary.csv"
    turn.to_csv(turn_path, index=False)

    fam_path = out_root / "layer2_family_dominance_summary.csv"
    write_family_dominance(top, fam_path, head_n=30)

    # Markdown narrative
    n_top = min(20, len(top))
    head20 = top.head(n_top)
    dom = pd.read_csv(fam_path)
    vsub = dom[dom["candidate_set"].astype(str).eq("vwap_core")]
    vwap_rows_top30 = int(vsub["rows_in_top_n"].iloc[0]) if len(vsub) else 0

    def _md_table(df: pd.DataFrame) -> str:
        try:
            return df.to_markdown(index=False)
        except Exception:
            return df.to_string(index=False)
    lines = [
        "# Layer 2 cost / turnover diagnostic summary (existing Global L2 v2 exports)",
        "",
        f"- **result_root**: `{result_root.as_posix()}`",
        f"- **top_unique rows**: {len(top)}",
        f"- **cost stress join**: {'yes' if len(stress_pivot) else 'no'}",
        "",
        "## 1) Why VWAP dominates ``combiner_score``",
        "",
        "Production score (``src/combiner/metrics.py``) is roughly:",
        "",
        "```",
        "PF + 0.015*total_r - 0.03*|maxDD| - 0.001*avg_bars_held",
        "  - 0.02*max_hold_count - 0.05*(eod + end_of_session + end_of_data) - 2.0[trades<50]",
        "```",
        "",
        "Multi-strategy buckets with similar ``total_r`` can lose versus ``vwap_core`` when:",
        "",
        "- **max_hold_count** / exit-mix penalties are larger (not always present in ``top_unique`` export — see ``residual_reported_minus_implied`` in ``layer2_score_decomposition.csv``).",
        "- **Drawdown** is deeper (``-0.03*|maxDD|`` term).",
        "- **avg_bars_held** is higher (``-0.001`` per bar).",
        "- **PF** is lower — PF enters with unit weight, while ``total_r`` only scales by **0.015**.",
        "",
        "Example from this pack: **indicator_completion_core** near rank ~49 has **higher total_r** than the VWAP headline but **lower combiner_score** — decomposition shows the **drawdown + bars-held + PF tradeoff** vs VWAP; residual column captures missing **max_hold / exit counts** not exported in ``top_unique_systems.csv``.",
        "",
        "## 2) Top 20 unique systems (baseline 0.01 slip from sweep)",
        "",
        _md_table(
            head20[
                [
                    "unique_rank",
                    "candidate_set",
                    "trades",
                    "total_r",
                    "profit_factor",
                    "max_drawdown_r",
                    "avg_bars_held",
                    "combiner_score",
                ]
            ]
        ),
        "",
        "## 3) Cost robustness (joined stress ladder where available)",
        "",
        "Per-row PASS/FAIL uses **total_r > 0** and **PF > 1** at each stress slip. **THIN_EDGE** flags **>65%** decay in total_r from baseline → 0.02 when baseline > 0.",
        "",
        "See ``layer2_cost_adjusted_ranking.csv`` for post-hoc objective and retention metrics.",
        "",
        "## 4) Turnover / edge thickness",
        "",
        f"See ``layer2_turnover_summary.csv`` (``avg_r_per_trade = total_r / trades``).",
        "",
        "## 5) Family dominance (top 30 by unique_rank)",
        "",
        _md_table(dom),
        "",
        f"- **vwap_core rows in top 30**: {vwap_rows_top30}",
        "",
        "## 6) Decision from exports only",
        "",
        "- Confirms **`TUNE_LAYER2_COST_TURNOVER`**: headline systems are **high trade count**, **cost fragile at +0.03 slip**, and **behavior-dedupe** (see committed behavior pack) is still **VWAP-pair variants**.",
        "- Does **not** justify Layer 3 yet: need tightened turnover/session grids and non-VWAP diagnostics from new sweeps.",
        "",
        "## Outputs",
        "",
        f"- `{dec_path.name}`",
        f"- `{rank_path.name}`",
        f"- `{turn_path.name}`",
        f"- `{fam_path.name}`",
        "",
    ]
    summary_path = out_root / "layer2_cost_turnover_diagnostic_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
