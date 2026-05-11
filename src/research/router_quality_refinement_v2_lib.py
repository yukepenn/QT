"""
Pure helpers for offline router / quality refinement v2 (research-only).

No combiner wiring, no strategy semantics changes — diagnostics on a local row panel only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

W_ORIGINAL = {
    "regime_fit": 0.30,
    "level_context": 0.20,
    "signal_strength": 0.20,
    "cost_safety": 0.15,
    "freshness": 0.15,
}


def profit_factor_r(rs: pd.Series) -> float | None:
    rs = pd.to_numeric(rs, errors="coerce").dropna()
    if rs.empty:
        return None
    wins = float(rs[rs > 0].sum())
    losses = float(rs[rs < 0].sum())
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def max_drawdown_r_proxy(df: pd.DataFrame, *, r_col: str = "r_multiple", ts_col: str = "signal_ts_utc") -> float | None:
    if df.empty or r_col not in df.columns:
        return None
    d = df.copy()
    if ts_col in d.columns:
        d["_ts"] = pd.to_datetime(d[ts_col], utc=True, errors="coerce")
        d = d.sort_values("_ts")
    rs = pd.to_numeric(d[r_col], errors="coerce").fillna(0.0).to_numpy()
    if len(rs) == 0:
        return None
    eq = np.cumsum(rs)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    return float(dd.min())


def period_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    sd = pd.to_datetime(out["session_date"].astype(str), errors="coerce")
    out["period_month"] = sd.dt.strftime("%Y-%m")
    out["period_quarter"] = sd.dt.to_period("Q").astype(str)
    return out


def summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "trades": 0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "win_rate": 0.0,
            "pf_r": None,
            "max_dd_r_proxy": None,
            "worst_month_r": None,
            "worst_quarter_r": None,
            "2025Q1_total_r": None,
            "2022Q4_total_r": None,
            "2023Q3_total_r": None,
            "weak_period_total_r": None,
            "weak_period_trades": 0,
        }
    rs = pd.to_numeric(df["r_multiple"], errors="coerce")
    d = period_columns(df)
    m = d.groupby("period_month", dropna=False)["r_multiple"].sum()
    q = d.groupby("period_quarter", dropna=False)["r_multiple"].sum()
    weak_r = None
    weak_n = 0
    if "weak_period_flag" in df.columns:
        wf = df["weak_period_flag"].astype(str).str.lower().isin(("true", "1", "t", "yes"))
        wrs = pd.to_numeric(df.loc[wf, "r_multiple"], errors="coerce")
        weak_n = int(wf.sum())
        weak_r = float(wrs.sum()) if weak_n else None
    return {
        "trades": int(len(df)),
        "total_r": float(rs.sum()),
        "avg_r": float(rs.mean()),
        "win_rate": float((rs > 0).mean()),
        "pf_r": profit_factor_r(rs),
        "max_dd_r_proxy": max_drawdown_r_proxy(df),
        "worst_month_r": float(m.min()) if len(m) else None,
        "worst_quarter_r": float(q.min()) if len(q) else None,
        "2025Q1_total_r": float(q.get("2025Q1")) if "2025Q1" in q.index else None,
        "2022Q4_total_r": float(q.get("2022Q4")) if "2022Q4" in q.index else None,
        "2023Q3_total_r": float(q.get("2023Q3")) if "2023Q3" in q.index else None,
        "weak_period_total_r": weak_r,
        "weak_period_trades": weak_n,
    }


def _clip01(x: pd.Series) -> pd.Series:
    return x.clip(lower=0.0, upper=1.0)


def score_components_original(df: pd.DataFrame) -> pd.DataFrame:
    """Original v2 composite (0..100) in column quality_score_v2."""
    out = df.copy()
    cid = out.get("candidate_id", pd.Series("", index=out.index)).astype(str)
    ctx = out.get("context_bucket", pd.Series("unknown_mixed", index=out.index)).astype(str)
    regime_fit = pd.Series(0.5, index=out.index, dtype=float)
    regime_fit = regime_fit.mask(cid.eq("PA_BUY_SELL_CLOSE_TREND_003") & ctx.eq("trend_long"), 1.0)
    regime_fit = regime_fit.mask(cid.eq("PA_BUY_SELL_CLOSE_TREND_003") & ctx.eq("trading_range"), 0.3)
    regime_fit = regime_fit.mask(cid.eq("GAP_ACCEPTANCE_FAILURE_001") & ctx.eq("unknown_mixed"), 0.6)
    regime_fit = regime_fit.mask(cid.eq("GAP_ACCEPTANCE_FAILURE_001") & ctx.eq("trend_long"), 0.4)
    regime_fit = regime_fit.mask(cid.eq("CCI_EXTREME_SNAPBACK_003") & ctx.eq("trading_range"), 0.7)
    out["regime_fit_score"] = regime_fit

    dist = pd.to_numeric(out.get("decision_pa_distance_from_vwap_atr", pd.Series(np.nan, index=out.index)), errors="coerce")
    level = pd.Series(0.5, index=out.index, dtype=float)
    if dist.notna().any():
        level = 1.0 - _clip01(dist.abs() / 1.5)
    out["level_context_score"] = level

    ts = pd.to_numeric(out.get("decision_trend_score_20", pd.Series(np.nan, index=out.index)), errors="coerce")
    sig = pd.Series(0.5, index=out.index, dtype=float)
    if ts.notna().any():
        sig = 0.5 + 0.5 * np.tanh(ts / 3.0)
    out["signal_strength_score"] = sig

    rps = pd.to_numeric(out.get("risk_per_share", pd.Series(np.nan, index=out.index)), errors="coerce")
    cost = pd.Series(0.5, index=out.index, dtype=float)
    if rps.notna().any():
        cost = 1.0 - _clip01((rps - rps.median()) / (rps.std(ddof=0) + 1e-9) * 0.1 + 0.5)
    out["cost_safety_score"] = cost

    tno = pd.to_numeric(out.get("entry_trade_number_of_day", pd.Series(np.nan, index=out.index)), errors="coerce")
    fresh = pd.Series(0.5, index=out.index, dtype=float)
    fresh = fresh.mask(tno.eq(1), 0.7)
    fresh = fresh.mask(tno.eq(2), 0.5)
    fresh = fresh.mask(tno.ge(3), 0.4)
    prior_loss = out.get("entry_prior_trade_was_loss", pd.Series(np.nan, index=out.index))
    fresh = fresh.mask(prior_loss.eq(True), 0.35)
    out["freshness_score"] = fresh

    comp = (
        out["regime_fit_score"] * W_ORIGINAL["regime_fit"]
        + out["level_context_score"] * W_ORIGINAL["level_context"]
        + out["signal_strength_score"] * W_ORIGINAL["signal_strength"]
        + out["cost_safety_score"] * W_ORIGINAL["cost_safety"]
        + out["freshness_score"] * W_ORIGINAL["freshness"]
    )
    out["quality_score_v2"] = (comp * 100.0).astype(float)
    return out


def add_quality_variants(df: pd.DataFrame) -> pd.DataFrame:
    """Adds score columns for each diagnostic variant (no new input columns required)."""
    base = score_components_original(df)
    out = base.copy()

    # 2) no_signal_strength_fallback — redistribute signal weight to regime+level
    w2 = dict(W_ORIGINAL)
    w2["signal_strength"] = 0.0
    s = w2["regime_fit"] + w2["level_context"]
    w2["regime_fit"] = W_ORIGINAL["regime_fit"] + W_ORIGINAL["signal_strength"] * (W_ORIGINAL["regime_fit"] / max(s, 1e-9))
    w2["level_context"] = W_ORIGINAL["level_context"] + W_ORIGINAL["signal_strength"] * (W_ORIGINAL["level_context"] / max(s, 1e-9))
    comp2 = (
        out["regime_fit_score"] * w2["regime_fit"]
        + out["level_context_score"] * w2["level_context"]
        + out["cost_safety_score"] * w2["cost_safety"]
        + out["freshness_score"] * w2["freshness"]
    )
    out["score_no_signal_strength_fallback"] = (comp2 * 100.0).astype(float)

    # 3) regime_level_cost_only
    comp3 = (
        out["regime_fit_score"] * (0.45)
        + out["level_context_score"] * (0.35)
        + out["cost_safety_score"] * (0.20)
    )
    out["score_regime_level_cost_only"] = (comp3 * 100.0).astype(float)

    # 4) freshness_penalty_light — same components, lighter repeat penalty
    fresh_light = out["freshness_score"].copy()
    prior_loss = df.get("entry_prior_trade_was_loss", pd.Series(np.nan, index=out.index))
    fresh_light = fresh_light.mask(prior_loss.eq(True), 0.45)
    comp4 = (
        out["regime_fit_score"] * W_ORIGINAL["regime_fit"]
        + out["level_context_score"] * W_ORIGINAL["level_context"]
        + out["signal_strength_score"] * W_ORIGINAL["signal_strength"]
        + out["cost_safety_score"] * W_ORIGINAL["cost_safety"]
        + fresh_light * W_ORIGINAL["freshness"]
    )
    out["score_freshness_penalty_light"] = (comp4 * 100.0).astype(float)

    # 5) repeat_after_loss_penalty_only — only freshness channel scaled to 100
    out["score_repeat_after_loss_penalty_only"] = (out["freshness_score"] * 100.0).astype(float)

    # 6) context_fit_plus_cost
    comp6 = out["regime_fit_score"] * 0.55 + out["cost_safety_score"] * 0.45
    out["score_context_fit_plus_cost"] = (comp6 * 100.0).astype(float)

    # 7) profile_percentile_score — rank within profile (0..100), in-sample diagnostic
    out["score_profile_percentile"] = 50.0
    if "profile_id" in out.columns:
        g = out.groupby("profile_id", dropna=False)["quality_score_v2"].rank(pct=True, method="average")
        out["score_profile_percentile"] = (g * 100.0).astype(float)

    return out


SCORE_VARIANT_COLUMNS: dict[str, str] = {
    "original_v2_score": "quality_score_v2",
    "no_signal_strength_fallback": "score_no_signal_strength_fallback",
    "regime_level_cost_only": "score_regime_level_cost_only",
    "freshness_penalty_light": "score_freshness_penalty_light",
    "repeat_after_loss_penalty_only": "score_repeat_after_loss_penalty_only",
    "context_fit_plus_cost": "score_context_fit_plus_cost",
    "profile_percentile_score": "score_profile_percentile",
}


def router_keep_mask(df: pd.DataFrame, variant: str, *, scored_for_proxy: pd.DataFrame | None = None) -> pd.Series:
    """Boolean Series: True = keep trade. Unknown variant raises KeyError."""
    n = len(df)
    ctx = df.get("context_bucket", pd.Series("", index=df.index)).astype(str)
    cid = df.get("candidate_id", pd.Series("", index=df.index)).astype(str)
    win = df.get("window", pd.Series("", index=df.index)).astype(str)

    if variant == "baseline_all":
        return pd.Series(True, index=df.index)

    if variant == "soft_avoid_removed":
        return ~ctx.eq("trend_short_diagnostic")

    if variant == "soft_downweight_proxy":
        # Drop rare strong-avoid + bottom half of late_climax by original score
        s = scored_for_proxy if scored_for_proxy is not None else score_components_original(df)
        score = pd.to_numeric(s["quality_score_v2"], errors="coerce")
        lc = ctx.eq("late_climax")
        med_lc = float(score[lc].median()) if lc.any() else float("nan")
        drop_lc = lc & score.lt(med_lc)
        return ~ctx.eq("trend_short_diagnostic") & ~drop_lc

    if variant == "gap_context_guard":
        bad = cid.eq("GAP_ACCEPTANCE_FAILURE_001") & win.eq("late_oow") & ctx.eq("unknown_mixed")
        return ~bad

    if variant == "late_climax_guard":
        lts = pd.to_numeric(df.get("decision_pa_late_trend_score_20", pd.Series(np.nan, index=df.index)), errors="coerce")
        pa = cid.eq("PA_BUY_SELL_CLOSE_TREND_003")
        lc = ctx.eq("late_climax") & pa
        if not lc.any():
            return pd.Series(True, index=df.index)
        q75 = float(lts[lc].quantile(0.75))
        chase = lc & lts.ge(q75)
        return ~chase

    if variant == "high_chop_guard":
        # No high_chop rows in current panel — keep all (diagnostic placeholder)
        hc = ctx.eq("high_chop")
        if not hc.any():
            return pd.Series(True, index=df.index)
        return ~hc

    if variant == "repeat_after_loss_guard":
        pl = df.get("entry_prior_trade_was_loss", pd.Series(False, index=df.index))
        sf = df.get("entry_prior_trade_same_family", pd.Series(False, index=df.index))
        pl_b = pl.astype(str).str.lower().isin(("true", "1", "t", "yes")) | pl.eq(True)
        sf_b = sf.astype(str).str.lower().isin(("true", "1", "t", "yes")) | sf.eq(True)
        return ~(pl_b & sf_b)

    if variant == "combined_light_guard":
        m1 = router_keep_mask(df, "soft_avoid_removed", scored_for_proxy=scored_for_proxy)
        m2 = router_keep_mask(df, "gap_context_guard", scored_for_proxy=scored_for_proxy)
        m3 = router_keep_mask(df, "repeat_after_loss_guard", scored_for_proxy=scored_for_proxy)
        return m1 & m2 & m3

    raise KeyError(variant)


ROUTER_VARIANTS: tuple[str, ...] = (
    "baseline_all",
    "soft_avoid_removed",
    "soft_downweight_proxy",
    "gap_context_guard",
    "late_climax_guard",
    "high_chop_guard",
    "repeat_after_loss_guard",
    "combined_light_guard",
)


def threshold_keep_mask(
    df: pd.DataFrame,
    score_col: str,
    scheme: str,
) -> pd.Series:
    s = pd.to_numeric(df[score_col], errors="coerce")
    if scheme == "fixed_AB":
        return s.ge(75) | ((s.ge(55)) & (s.lt(75)))
    if scheme == "relaxed_AB":
        return s.ge(65) | ((s.ge(45)) & (s.lt(65)))
    if scheme == "percentile_profile_top80":
        if "profile_id" not in df.columns:
            return pd.Series(False, index=df.index)
        out = pd.Series(False, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.20)
            out.loc[gg.index] = ss.ge(thr)
        return out
    if scheme == "percentile_profile_top70":
        if "profile_id" not in df.columns:
            return pd.Series(False, index=df.index)
        out = pd.Series(False, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.30)
            out.loc[gg.index] = ss.ge(thr)
        return out
    if scheme == "percentile_profile_top50":
        if "profile_id" not in df.columns:
            return pd.Series(False, index=df.index)
        out = pd.Series(False, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.50)
            out.loc[gg.index] = ss.ge(thr)
        return out
    if scheme == "percentile_profile_window_top80":
        if "profile_id" not in df.columns or "window" not in df.columns:
            return pd.Series(False, index=df.index)
        out = pd.Series(False, index=df.index)
        for (_, _), gg in df.groupby(["profile_id", "window"], dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.20)
            out.loc[gg.index] = ss.ge(thr)
        return out
    if scheme == "percentile_profile_window_top70":
        if "profile_id" not in df.columns or "window" not in df.columns:
            return pd.Series(False, index=df.index)
        out = pd.Series(False, index=df.index)
        for (_, _), gg in df.groupby(["profile_id", "window"], dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.30)
            out.loc[gg.index] = ss.ge(thr)
        return out
    if scheme == "bottom_cut_10":
        if "profile_id" not in df.columns:
            return pd.Series(True, index=df.index)
        out = pd.Series(True, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.10)
            out.loc[gg.index] = ss.gt(thr)
        return out
    if scheme == "bottom_cut_20":
        if "profile_id" not in df.columns:
            return pd.Series(True, index=df.index)
        out = pd.Series(True, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.20)
            out.loc[gg.index] = ss.gt(thr)
        return out
    if scheme == "bottom_cut_30":
        if "profile_id" not in df.columns:
            return pd.Series(True, index=df.index)
        out = pd.Series(True, index=df.index)
        for pid, gg in df.groupby("profile_id", dropna=False):
            ss = pd.to_numeric(gg[score_col], errors="coerce")
            thr = ss.quantile(0.30)
            out.loc[gg.index] = ss.gt(thr)
        return out
    raise KeyError(scheme)


QUALITY_THRESHOLD_SCHEMES: tuple[str, ...] = (
    "fixed_AB",
    "relaxed_AB",
    "percentile_profile_top80",
    "percentile_profile_top70",
    "percentile_profile_top50",
    "percentile_profile_window_top80",
    "percentile_profile_window_top70",
    "bottom_cut_10",
    "bottom_cut_20",
    "bottom_cut_30",
)


def _finite_pf_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    if math.isinf(float(a)) or math.isinf(float(b)):
        return None
    return float(a - b)


def label_router_row(
    *,
    retention: float,
    delta_pf: float | None,
    delta_dd: float | None,
    delta_weak_r: float | None,
    delta_total_r: float,
    profile_id: str,
) -> str:
    if retention < 0.60:
        return "ROUTER_V2_TOO_DESTRUCTIVE"
    if retention > 0.999 and abs(delta_total_r) < 1e-6:
        return "ROUTER_V2_NO_IMPROVEMENT"
    improved = (delta_pf is not None and delta_pf > 0.01) or (delta_dd is not None and delta_dd > 1.0)
    if not improved:
        return "ROUTER_V2_NO_IMPROVEMENT"
    if profile_id == "pa_only_mtp1_meta" and delta_total_r < -40:
        return "ROUTER_V2_TOO_DESTRUCTIVE"
    if profile_id == "pa_gap_mtp2_meta" and delta_total_r < -80:
        return "ROUTER_V2_TOO_DESTRUCTIVE"
    if delta_weak_r is not None and delta_weak_r < -15:
        return "ROUTER_V2_NEEDS_REDESIGN"
    return "ROUTER_V2_PROMISING"


def label_quality_row(
    *,
    retention: float,
    delta_pf: float | None,
    delta_dd: float | None,
    delta_weak_r: float | None,
    delta_total_r: float,
    scheme: str,
) -> str:
    if retention < 0.60:
        if retention < 0.15:
            return "QUALITY_V2_TOO_SPARSE"
        return "QUALITY_V2_OVERFILTERS"
    improved = (delta_pf is not None and delta_pf > 0.01) or (delta_dd is not None and delta_dd > 1.0)
    if not improved and abs(delta_total_r) < 5:
        return "QUALITY_V2_NO_SEPARATION"
    if not improved:
        return "QUALITY_V2_NEEDS_REDESIGN"
    if delta_weak_r is not None and delta_weak_r < -20:
        return "QUALITY_V2_NEEDS_REDESIGN"
    return "QUALITY_V2_PROMISING"


DECISION_LABELS: tuple[str, ...] = (
    "DESIGN_LAYER2_ROUTER_INTEGRATION",
    "RUN_EXIT_OVERLAY_DIAGNOSTICS",
    "REFINE_ROUTER_QUALITY_SCORE_AGAIN",
    "DESIGN_SCALP_LONG_STRATEGIES",
    "DESIGN_SHORT_BRANCH",
    "HOLD_AND_REVIEW",
)


def pf_r_for_csv(v: float | None) -> str:
    if v is None:
        return ""
    if math.isinf(v):
        return "inf"
    return f"{v:.6f}"


def retention_pct(kept: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return float(kept / total)
