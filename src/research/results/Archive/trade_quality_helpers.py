"""
Pure helpers for trade-quality research: timestamp joins, prior-trade context, bucketing, metrics.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# Brooks enum code maps (see src/features/pa_brooks_enums.py)
REGIME_LABEL_MAP: dict[int, str] = {
    0: "regime_unknown",
    1: "strong_bull_breakout",
    -1: "strong_bear_breakout",
    2: "tight_bull_channel",
    -2: "tight_bear_channel",
    3: "broad_bull_channel",
    -3: "broad_bear_channel",
    4: "trading_range",
    5: "late_trend_climax",
}
TRADE_MODE_MAP: dict[int, str] = {
    0: "trade_mode_neutral",
    1: "trend_long",
    -1: "trend_short",
    2: "range_mode",
    3: "climax_mode",
}
ALWAYS_IN_MAP: dict[int, str] = {
    -1: "always_in_short",
    0: "always_in_neutral",
    1: "always_in_long",
}


def enum_label(m: dict[int, str], code: Any) -> str:
    if code is None or (isinstance(code, float) and math.isnan(code)):
        return "missing"
    try:
        k = int(code)
    except (TypeError, ValueError):
        return "missing"
    return m.get(k, f"other_{k}")


def parse_utc_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, utc=True, errors="coerce")


def merge_features_asof_backward(
    trades: pd.DataFrame,
    features: pd.DataFrame,
    trade_ts_col: str = "entry_ts_utc",
    feature_ts_col: str = "ts_utc",
) -> pd.DataFrame:
    """Left-join each trade to the last feature row at or before entry (no lookahead)."""
    t = trades.copy()
    t["_join_ts"] = parse_utc_series(t[trade_ts_col])
    t = t.sort_values("_join_ts")
    f = features.copy()
    f["_feat_ts"] = parse_utc_series(f[feature_ts_col])
    f = f.sort_values("_feat_ts")
    merged = pd.merge_asof(
        t,
        f,
        left_on="_join_ts",
        right_on="_feat_ts",
        direction="backward",
        allow_exact_matches=True,
    )
    merged = merged.drop(columns=["_join_ts", "_feat_ts"], errors="ignore")
    return merged


def add_prior_trade_columns(
    df: pd.DataFrame,
    session_col: str = "session_date",
    entry_ts_col: str = "entry_ts_utc",
    strategy_col: str = "strategy",
    family_col: str = "strategy_family",
    r_col: str = "r_multiple",
) -> pd.DataFrame:
    out = df.copy()
    out["_entry_ts"] = parse_utc_series(out[entry_ts_col])
    out = out.sort_values([session_col, "_entry_ts"])
    g = out.groupby(session_col, sort=False)
    out["entry_trade_number_of_day"] = g.cumcount() + 1
    prior_r = g[r_col].shift(1)
    out["entry_prior_trade_pnl_r"] = prior_r
    out["entry_prior_trade_was_loss"] = (prior_r < 0).where(prior_r.notna(), np.nan)
    out["entry_prior_trade_same_strategy"] = (
        g[strategy_col].shift(1).eq(out[strategy_col])
    ).where(prior_r.notna(), np.nan)
    out["entry_prior_trade_same_family"] = (
        g[family_col].shift(1).eq(out[family_col])
    ).where(prior_r.notna(), np.nan)
    out = out.drop(columns=["_entry_ts"])
    return out


def exit_reason_flags(exit_reason: Any) -> Tuple[Optional[bool], Optional[bool], Optional[bool]]:
    """Derive (is_profit_target, is_stop, is_forced) from exit_reason string."""
    if exit_reason is None or (isinstance(exit_reason, float) and math.isnan(exit_reason)):
        return None, None, None
    s = str(exit_reason).lower()
    is_target = "target" in s or "take" in s or "profit" in s
    is_stop = "stop" in s
    is_forced = "eod" in s or "session" in s or "forced" in s or "max_hold" in s or "time" in s
    return is_target, is_stop, is_forced


def profit_factor_r(rs: pd.Series) -> float:
    wins = rs[rs > 0].sum()
    losses = rs[rs < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def bucket_quantiles(
    s: pd.Series,
    q_edges: Sequence[float] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    prefix: str = "q",
) -> pd.Series:
    """Quantile buckets with stable labels; NaN -> 'missing'."""
    if s.isna().all():
        return pd.Series(["missing"] * len(s), index=s.index)
    qs = s.quantile([x for x in q_edges if 0 < x < 1]).sort_values()
    edges = [-np.inf] + list(qs.values) + [np.inf]
    # Drop duplicate edges (constant series) so labels always match bin count - 1.
    edges_u: list[float] = []
    for e in edges:
        if not edges_u or e > edges_u[-1] + 1e-15:
            edges_u.append(float(e))
    nbin = len(edges_u) - 1
    if nbin <= 0:
        return pd.Series([f"{prefix}_flat"] * len(s), index=s.index)
    labels = [f"{prefix}{i}" for i in range(nbin)]
    b = pd.cut(s, bins=edges_u, labels=labels, include_lowest=True)
    out = b.astype(str).replace("nan", "missing")
    out = out.mask(out.eq("nan"), f"{prefix}_flat")
    return out


def bucket_fixed_edges(s: pd.Series, edges: Sequence[float], labels: Sequence[str]) -> pd.Series:
    b = pd.cut(s, bins=list(edges), labels=list(labels), include_lowest=True)
    return b.astype(str).replace("nan", "missing")


def summarize_bucket(
    df: pd.DataFrame,
    bucket_col: str,
    r_col: str = "r_multiple",
    bars_col: Optional[str] = "bars_held",
    min_n: int = 5,
) -> pd.DataFrame:
    rows = []
    total_trades = len(df)
    total_r = df[r_col].sum()
    for key, g in df.groupby(bucket_col, dropna=False):
        n = len(g)
        rs = g[r_col]
        wr = (rs > 0).mean() if n else 0.0
        pf = profit_factor_r(rs)
        row = {
            "bucket": key,
            "trades": n,
            "total_r": float(rs.sum()),
            "avg_r": float(rs.mean()) if n else 0.0,
            "median_r": float(rs.median()) if n else 0.0,
            "win_rate": float(wr),
            "pf_r": float(pf) if math.isfinite(pf) else None,
            "max_loss_r": float(rs.min()) if n else 0.0,
            "share_trades": float(n / total_trades) if total_trades else 0.0,
            "share_pnl": float(rs.sum() / total_r) if total_r != 0 else 0.0,
            "low_sample_warning": n < min_n,
        }
        if bars_col and bars_col in g.columns:
            row["avg_bars_held"] = float(g[bars_col].mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("bucket")


def write_bucket_md(title: str, summary: pd.DataFrame, path: str) -> None:
    lines = [f"# {title}", "", "| " + " | ".join(summary.columns) + " |", "| " + " | ".join(["---"] * len(summary.columns)) + " |"]
    for _, r in summary.iterrows():
        cells = [str(r[c]) for c in summary.columns]
        lines.append("| " + " | ".join(cells) + " |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
