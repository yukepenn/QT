"""
Trade-quality score v2 diagnostics (aggregate-only) — research-only.

Implements a *minimal* v2 scoring aligned with the playbook design weights:
- regime_fit_score 30%
- level_context_score 20%
- signal_strength_score 20% (placeholder proxy)
- cost_safety_score 15% (placeholder proxy)
- freshness_score 15%

This is intentionally conservative and will report missingness rather than over-claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


W = {
    "regime_fit": 0.30,
    "level_context": 0.20,
    "signal_strength": 0.20,
    "cost_safety": 0.15,
    "freshness": 0.15,
}


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _df_to_md_table(df: pd.DataFrame, *, max_rows: int = 40) -> str:
    if df is None or df.empty:
        return "_(empty)_"
    d = df.head(int(max_rows)).copy()
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def _pf_r(rs: pd.Series) -> float | None:
    wins = float(rs[rs > 0].sum())
    losses = float(rs[rs < 0].sum())
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def _period_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    sd = pd.to_datetime(out["session_date"].astype(str), errors="coerce")
    out["period_month"] = sd.dt.strftime("%Y-%m")
    out["period_quarter"] = sd.dt.to_period("Q").astype(str)
    return out


def _max_dd_proxy(df: pd.DataFrame) -> float | None:
    if df.empty:
        return None
    d = df.copy()
    if "signal_ts_utc" in d.columns:
        d["_ts"] = pd.to_datetime(d["signal_ts_utc"], utc=True, errors="coerce")
        d = d.sort_values("_ts")
    rs = pd.to_numeric(d["r_multiple"], errors="coerce").fillna(0.0).to_numpy()
    eq = np.cumsum(rs)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    return float(dd.min()) if len(dd) else None


def _summ(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"trades": 0, "total_r": 0.0, "avg_r": 0.0, "win_rate": 0.0, "pf_r": None, "max_dd_r_proxy": None}
    rs = pd.to_numeric(df["r_multiple"], errors="coerce")
    return {
        "trades": int(len(df)),
        "total_r": float(rs.sum()),
        "avg_r": float(rs.mean()),
        "win_rate": float((rs > 0).mean()),
        "pf_r": _pf_r(rs),
        "max_dd_r_proxy": _max_dd_proxy(df),
    }


def _clip01(x: pd.Series) -> pd.Series:
    return x.clip(lower=0.0, upper=1.0)


def _score_components(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Returns (scored_df, coverage_meta).
    """
    out = df.copy()
    meta: dict[str, Any] = {"rows_in": int(len(out))}

    # Regime-fit proxy: prefers PA in trend_long, GAP in unknown_mixed/opening, CCI in trading_range.
    cid = out.get("candidate_id", pd.Series("", index=out.index)).astype(str)
    ctx = out.get("context_bucket", pd.Series("unknown_mixed", index=out.index)).astype(str)
    regime_fit = pd.Series(0.5, index=out.index, dtype=float)
    regime_fit = regime_fit.mask(cid.eq("PA_BUY_SELL_CLOSE_TREND_003") & ctx.eq("trend_long"), 1.0)
    regime_fit = regime_fit.mask(cid.eq("PA_BUY_SELL_CLOSE_TREND_003") & ctx.eq("trading_range"), 0.3)
    regime_fit = regime_fit.mask(cid.eq("GAP_ACCEPTANCE_FAILURE_001") & ctx.eq("unknown_mixed"), 0.6)
    regime_fit = regime_fit.mask(cid.eq("GAP_ACCEPTANCE_FAILURE_001") & ctx.eq("trend_long"), 0.4)
    regime_fit = regime_fit.mask(cid.eq("CCI_EXTREME_SNAPBACK_003") & ctx.eq("trading_range"), 0.7)
    out["regime_fit_score"] = regime_fit

    # Level-context proxy: closer to VWAP is better for mean reversion; farther for trend.
    dist = pd.to_numeric(out.get("decision_pa_distance_from_vwap_atr", pd.Series(np.nan, index=out.index)), errors="coerce")
    level = pd.Series(0.5, index=out.index, dtype=float)
    if dist.notna().any():
        # dist in ATR: smaller is better up to ~1.5 ATR
        level = 1.0 - _clip01(dist.abs() / 1.5)
    out["level_context_score"] = level

    # Signal-strength placeholder: use trend_score when available; else 0.5.
    ts = pd.to_numeric(out.get("decision_trend_score_20", pd.Series(np.nan, index=out.index)), errors="coerce")
    sig = pd.Series(0.5, index=out.index, dtype=float)
    if ts.notna().any():
        # normalize to [0,1] via tanh
        sig = 0.5 + 0.5 * np.tanh(ts / 3.0)
    out["signal_strength_score"] = sig

    # Cost-safety placeholder: lower risk_per_share is slightly safer (proxy only).
    rps = pd.to_numeric(out.get("risk_per_share", pd.Series(np.nan, index=out.index)), errors="coerce")
    cost = pd.Series(0.5, index=out.index, dtype=float)
    if rps.notna().any():
        cost = 1.0 - _clip01((rps - rps.median()) / (rps.std(ddof=0) + 1e-9) * 0.1 + 0.5)
    out["cost_safety_score"] = cost

    # Freshness proxy: trade #1 better than trade #2; repeats after loss downweighted.
    tno = pd.to_numeric(out.get("entry_trade_number_of_day", pd.Series(np.nan, index=out.index)), errors="coerce")
    fresh = pd.Series(0.5, index=out.index, dtype=float)
    fresh = fresh.mask(tno.eq(1), 0.7)
    fresh = fresh.mask(tno.eq(2), 0.5)
    fresh = fresh.mask(tno.ge(3), 0.4)
    prior_loss = out.get("entry_prior_trade_was_loss", pd.Series(np.nan, index=out.index))
    fresh = fresh.mask(prior_loss.eq(True), 0.35)
    out["freshness_score"] = fresh

    # Composite (0..100)
    comp = (
        out["regime_fit_score"] * W["regime_fit"]
        + out["level_context_score"] * W["level_context"]
        + out["signal_strength_score"] * W["signal_strength"]
        + out["cost_safety_score"] * W["cost_safety"]
        + out["freshness_score"] * W["freshness"]
    )
    out["quality_score_v2"] = (comp * 100.0).astype(float)

    meta["missing_trend_score_rows"] = int(ts.isna().sum())
    meta["missing_distance_from_vwap_rows"] = int(dist.isna().sum())
    meta["missing_trade_number_rows"] = int(tno.isna().sum())
    return out, meta


def _bucket(score: pd.Series) -> pd.Series:
    s = pd.to_numeric(score, errors="coerce")
    out = pd.Series(["C"] * len(s), index=s.index, dtype="string")
    out = out.mask(s >= 75, "A")
    out = out.mask((s >= 55) & (s < 75), "B")
    out = out.mask(s.isna(), "missing")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run trade-quality score v2 diagnostics (aggregate-only).")
    p.add_argument("--context-replay-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--local-panel", required=True)
    args = p.parse_args(argv)

    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(Path(args.local_panel))
    if panel.empty:
        raise RuntimeError("local panel is empty")

    scored, meta = _score_components(panel)
    scored["quality_bucket_v2"] = _bucket(scored["quality_score_v2"])

    # coverage
    _write_csv(pd.DataFrame([meta | {"weights": json.dumps(W, sort_keys=True)}]), out / "quality_score_component_coverage.csv")

    # distribution
    dist = scored["quality_bucket_v2"].value_counts(dropna=False).reset_index()
    dist.columns = ["bucket", "trades"]
    dist["share"] = dist["trades"] / float(dist["trades"].sum())
    _write_csv(dist, out / "quality_bucket_distribution.csv")

    # bucket results
    rows = []
    for b in ["A", "B", "C", "missing"]:
        sub = scored[scored["quality_bucket_v2"].astype(str) == b].copy()
        rows.append({"bucket": b, **_summ(sub)})
    _write_csv(pd.DataFrame(rows), out / "quality_bucket_results.csv")

    # group results
    groups = {
        "all": scored,
        "A+B": scored[scored["quality_bucket_v2"].isin(["A", "B"])],
        "A_only": scored[scored["quality_bucket_v2"].isin(["A"])],
        "C_removed": scored[~scored["quality_bucket_v2"].isin(["C"])],
    }
    g_rows = []
    for k, sub in groups.items():
        m = _summ(sub)
        m["group"] = k
        m["retention"] = float(len(sub) / len(scored)) if len(scored) else None
        d2 = _period_cols(sub)
        q = d2.groupby("period_quarter", dropna=False)["r_multiple"].sum()
        m["worst_quarter_r"] = float(q.min()) if len(q) else None
        m["2025Q1_total_r"] = float(q.get("2025Q1")) if "2025Q1" in q.index else None
        m["2022Q4_total_r"] = float(q.get("2022Q4")) if "2022Q4" in q.index else None
        g_rows.append(m)
    _write_csv(pd.DataFrame(g_rows), out / "quality_group_results.csv")

    # by profile/context
    if "profile_id" in scored.columns:
        parts = []
        for (pid, b), gg in scored.groupby(["profile_id", "quality_bucket_v2"], dropna=False):
            parts.append({"profile_id": pid, "bucket": b, **_summ(gg)})
        _write_csv(pd.DataFrame(parts), out / "quality_by_profile.csv")
    if "context_bucket" in scored.columns:
        parts = []
        for (ctx, b), gg in scored.groupby(["context_bucket", "quality_bucket_v2"], dropna=False):
            parts.append({"context_bucket": ctx, "bucket": b, **_summ(gg)})
        _write_csv(pd.DataFrame(parts), out / "quality_by_context.csv")

    # summary
    lines = [
        "# quality_score_v2_summary",
        "",
        "- This is an **offline diagnostic** score (no production wiring).",
        "- Some components are proxies; interpret primarily as *rank-separation evidence* not as final scoring logic.",
        "",
        "## Bucket distribution",
        "",
        _df_to_md_table(dist),
        "",
        "## Group results",
        "",
        _df_to_md_table(pd.DataFrame(g_rows)),
        "",
    ]
    _write_md(out / "quality_score_v2_summary.md", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

