"""Trade and equity metrics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def profit_factor(pnls: pd.Series) -> float:
    s = pnls.astype(float)
    wins = s[s > 0].sum()
    losses = s[s < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def profit_factor_r(r: pd.Series) -> float:
    """Gross profit R / gross loss R (absolute)."""
    s = r.astype(float)
    wins = float(s[s > 0].sum())
    losses = float(s[s < 0].sum())
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def quantile_safe(series: pd.Series | np.ndarray | list[Any], q: float, *, default: float = float("nan")) -> float:
    s = pd.Series(series).dropna()
    if len(s) == 0:
        return default
    try:
        return float(s.quantile(q))
    except Exception:
        return default


def estimate_round_trip_cost_per_share(
    slippage_per_share: float | None,
    commission_per_trade: float | None,
    quantity: float | None,
) -> float:
    slip = float(slippage_per_share or 0.0)
    comm = float(commission_per_trade or 0.0)
    rt = 2.0 * slip
    if quantity is None or quantity == 0 or (isinstance(quantity, float) and math.isnan(quantity)):
        if comm != 0.0:
            return float("nan")
        return float(rt)
    return float(rt + comm / float(quantity))


def add_cost_r_column(
    trades_df: pd.DataFrame,
    slippage_per_share: float | None,
    commission_per_trade: float | None,
    quantity: float | None,
) -> pd.DataFrame:
    out = trades_df.copy()
    rt = estimate_round_trip_cost_per_share(slippage_per_share, commission_per_trade, quantity)
    out["round_trip_cost_per_share"] = rt
    if "risk_per_share" not in out.columns:
        out["cost_r"] = float("nan")
        return out
    risk = out["risk_per_share"].astype(float)
    cost_r = pd.Series(np.nan, index=out.index, dtype=float)
    ok = risk.notna() & (risk > 0)
    if isinstance(rt, float) and not math.isnan(rt):
        cost_r.loc[ok] = rt / risk.loc[ok]
    out["cost_r"] = cost_r
    return out


def summarize_cost_r(
    trades_df: pd.DataFrame,
    slippage_per_share: float = 0.0,
    commission_per_trade: float = 0.0,
    quantity: float = 1.0,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "estimated_round_trip_cost_per_share": float("nan"),
        "avg_risk_per_share": float("nan"),
        "median_risk_per_share": float("nan"),
        "p10_risk_per_share": float("nan"),
        "p25_risk_per_share": float("nan"),
        "avg_cost_r": float("nan"),
        "median_cost_r": float("nan"),
        "p90_cost_r": float("nan"),
        "pct_trades_cost_r_gt_0_25": float("nan"),
        "pct_trades_cost_r_gt_0_50": float("nan"),
        "pct_trades_cost_r_gt_1_00": float("nan"),
    }
    if trades_df is None or len(trades_df) == 0:
        return out
    if "risk_per_share" not in trades_df.columns:
        return out
    risk = trades_df["risk_per_share"].astype(float)
    valid_r = risk.replace(0, np.nan).dropna()
    if len(valid_r) == 0:
        return out
    rt = estimate_round_trip_cost_per_share(slippage_per_share, commission_per_trade, quantity)
    out["estimated_round_trip_cost_per_share"] = rt
    out["avg_risk_per_share"] = float(valid_r.mean())
    out["median_risk_per_share"] = float(valid_r.median())
    out["p10_risk_per_share"] = quantile_safe(valid_r, 0.1)
    out["p25_risk_per_share"] = quantile_safe(valid_r, 0.25)
    if isinstance(rt, float) and math.isnan(rt):
        return out
    cost_r = rt / valid_r
    out["avg_cost_r"] = float(cost_r.mean())
    out["median_cost_r"] = float(cost_r.median())
    out["p90_cost_r"] = quantile_safe(cost_r, 0.9)
    n = len(cost_r)
    if n:
        out["pct_trades_cost_r_gt_0_25"] = float((cost_r > 0.25).sum() / n)
        out["pct_trades_cost_r_gt_0_50"] = float((cost_r > 0.50).sum() / n)
        out["pct_trades_cost_r_gt_1_00"] = float((cost_r > 1.00).sum() / n)
    return out


def summarize_r_distribution(trades_df: pd.DataFrame) -> dict[str, Any]:
    empty = {
        "profit_factor_r": 0.0,
        "median_r": float("nan"),
        "p25_r": float("nan"),
        "p75_r": float("nan"),
        "worst_trade_r": float("nan"),
        "best_trade_r": float("nan"),
        "std_r": float("nan"),
    }
    if trades_df is None or len(trades_df) == 0 or "r_multiple" not in trades_df.columns:
        return empty
    r = trades_df["r_multiple"].astype(float)
    return {
        "profit_factor_r": profit_factor_r(r),
        "median_r": float(r.median()),
        "p25_r": quantile_safe(r, 0.25),
        "p75_r": quantile_safe(r, 0.75),
        "worst_trade_r": float(r.min()),
        "best_trade_r": float(r.max()),
        "std_r": float(r.std(ddof=0)) if len(r) > 1 else 0.0,
    }


def summarize_daily(trades_df: pd.DataFrame) -> dict[str, Any]:
    empty = {
        "active_days": 0,
        "positive_day_rate": float("nan"),
        "avg_daily_r": float("nan"),
        "median_daily_r": float("nan"),
        "worst_day_r": float("nan"),
        "best_day_r": float("nan"),
        "daily_profit_factor_r": float("nan"),
        "avg_daily_trade_count": float("nan"),
        "max_daily_trade_count": 0,
    }
    if trades_df is None or len(trades_df) == 0 or "r_multiple" not in trades_df.columns:
        return empty
    df = trades_df
    day_col = None
    if "session_date" in df.columns:
        day_col = "session_date"
    elif "entry_ts_utc" in df.columns:
        df = df.copy()
        df["_day"] = pd.to_datetime(df["entry_ts_utc"], utc=True, errors="coerce").dt.normalize()
        day_col = "_day"
    elif "exit_ts_utc" in df.columns:
        df = df.copy()
        df["_day"] = pd.to_datetime(df["exit_ts_utc"], utc=True, errors="coerce").dt.normalize()
        day_col = "_day"
    else:
        return empty
    g = df.groupby(day_col, dropna=False)["r_multiple"].agg(["sum", "count"])
    if len(g) == 0:
        return empty
    daily_r = g["sum"].astype(float)
    counts = g["count"].astype(int)
    pos = int((daily_r > 0).sum())
    return {
        "active_days": int(len(g)),
        "positive_day_rate": float(pos / len(g)) if len(g) else float("nan"),
        "avg_daily_r": float(daily_r.mean()),
        "median_daily_r": float(daily_r.median()),
        "worst_day_r": float(daily_r.min()),
        "best_day_r": float(daily_r.max()),
        "daily_profit_factor_r": profit_factor_r(daily_r),
        "avg_daily_trade_count": float(counts.mean()),
        "max_daily_trade_count": int(counts.max()),
    }


def period_breakdown(trades_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    cols = [
        "period",
        "trades",
        "total_r",
        "total_net_pnl",
        "profit_factor",
        "profit_factor_r",
        "max_drawdown_r",
        "win_rate",
        "avg_r",
        "median_r",
    ]
    if trades_df is None or len(trades_df) == 0:
        return pd.DataFrame(columns=cols)
    df = trades_df.copy()
    if "session_date" in df.columns:
        dt = pd.to_datetime(df["session_date"], errors="coerce")
    elif "entry_ts_utc" in df.columns:
        dt = pd.to_datetime(df["entry_ts_utc"], utc=True, errors="coerce")
    elif "exit_ts_utc" in df.columns:
        dt = pd.to_datetime(df["exit_ts_utc"], utc=True, errors="coerce")
    else:
        return pd.DataFrame(columns=cols)
    df["_period"] = dt.dt.to_period(freq)
    rows: list[dict[str, Any]] = []
    for per, sub in df.groupby("_period", dropna=False):
        if per is pd.NaT or str(per) == "NaT":
            continue
        m = summarize_trades(sub)
        rd = summarize_r_distribution(sub)
        rows.append(
            {
                "period": str(per),
                "trades": m["trades"],
                "total_r": m["total_r"],
                "total_net_pnl": m["total_net_pnl"],
                "profit_factor": m["profit_factor"],
                "profit_factor_r": rd["profit_factor_r"],
                "max_drawdown_r": m["max_drawdown_r"],
                "win_rate": m["win_rate"],
                "avg_r": m["avg_r"],
                "median_r": rd["median_r"],
            }
        )
    return pd.DataFrame(rows, columns=cols)


def max_drawdown(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    x = series.astype(float).values
    # Drawdown is measured from an initial equity baseline of 0.0.
    peak = 0.0
    dd = 0.0
    for v in x:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    return float(dd)


def summarize_trades(
    trades_df: pd.DataFrame,
    *,
    slippage_per_share: float | None = None,
    commission_per_trade: float | None = None,
    quantity: float | None = None,
) -> dict:
    empty = {
        "trades": 0,
        "win_rate": 0.0,
        "total_net_pnl": 0.0,
        "avg_net_pnl": 0.0,
        "total_r": 0.0,
        "avg_r": 0.0,
        "profit_factor": 0.0,
        "max_drawdown_pnl": 0.0,
        "max_drawdown_r": 0.0,
        "avg_bars_held": 0.0,
        "stop_count": 0,
        "target_count": 0,
        "eod_count": 0,
        "end_of_data_count": 0,
        "max_hold_count": 0,
        "profit_factor_r": 0.0,
        "median_r": float("nan"),
        "p25_r": float("nan"),
        "p75_r": float("nan"),
        "worst_trade_r": float("nan"),
        "best_trade_r": float("nan"),
        "std_r": float("nan"),
        "active_days": 0,
        "positive_day_rate": float("nan"),
        "avg_daily_r": float("nan"),
        "median_daily_r": float("nan"),
        "worst_day_r": float("nan"),
        "best_day_r": float("nan"),
        "daily_profit_factor_r": float("nan"),
        "avg_daily_trade_count": float("nan"),
        "max_daily_trade_count": 0,
        "estimated_round_trip_cost_per_share": float("nan"),
        "avg_risk_per_share": float("nan"),
        "median_risk_per_share": float("nan"),
        "p10_risk_per_share": float("nan"),
        "p25_risk_per_share": float("nan"),
        "avg_cost_r": float("nan"),
        "median_cost_r": float("nan"),
        "p90_cost_r": float("nan"),
        "pct_trades_cost_r_gt_0_25": float("nan"),
        "pct_trades_cost_r_gt_0_50": float("nan"),
        "pct_trades_cost_r_gt_1_00": float("nan"),
    }
    if trades_df is None or len(trades_df) == 0:
        return empty

    net = trades_df["net_pnl"].astype(float)
    r = trades_df["r_multiple"].astype(float)
    wins = int((net > 0).sum())
    n = int(len(trades_df))
    cum_pnl = net.cumsum()
    cum_r = r.cumsum()

    er = trades_df["exit_reason"].astype(str).str.lower()
    base = {
        "trades": n,
        "win_rate": wins / n if n else 0.0,
        "total_net_pnl": float(net.sum()),
        "avg_net_pnl": float(net.mean()),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "profit_factor": profit_factor(net),
        "max_drawdown_pnl": max_drawdown(cum_pnl),
        "max_drawdown_r": max_drawdown(cum_r),
        "avg_bars_held": float(trades_df["bars_held"].astype(float).mean()),
        "stop_count": int((er == "stop").sum()),
        "target_count": int((er == "target").sum()),
        "eod_count": int((er == "eod").sum()),
        "end_of_data_count": int((er == "end_of_data").sum()),
        "max_hold_count": int((er == "max_hold").sum()),
    }
    base.update(summarize_r_distribution(trades_df))
    base.update(summarize_daily(trades_df))

    if slippage_per_share is not None or commission_per_trade is not None or quantity is not None:
        cs = summarize_cost_r(
            trades_df,
            slippage_per_share=float(slippage_per_share or 0.0),
            commission_per_trade=float(commission_per_trade or 0.0),
            quantity=float(quantity if quantity is not None else 1.0),
        )
        for k, v in cs.items():
            base[k] = v
    else:
        for k in (
            "estimated_round_trip_cost_per_share",
            "avg_risk_per_share",
            "median_risk_per_share",
            "p10_risk_per_share",
            "p25_risk_per_share",
            "avg_cost_r",
            "median_cost_r",
            "p90_cost_r",
            "pct_trades_cost_r_gt_0_25",
            "pct_trades_cost_r_gt_0_50",
            "pct_trades_cost_r_gt_1_00",
        ):
            base[k] = empty[k]

    return base


def total_r_over_abs_dd(total_r: float, max_drawdown_r: float) -> float:
    if max_drawdown_r >= 0 or (isinstance(max_drawdown_r, float) and math.isnan(max_drawdown_r)):
        return float("nan")
    denom = abs(float(max_drawdown_r))
    if denom == 0:
        return float("nan")
    return float(total_r) / denom
