"""Helpers for regime_unknown decomposition (trade-quality research)."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd

from src.research.trade_quality_helpers import bucket_quantiles, profit_factor_r


def minute_bucket_open(m: pd.Series) -> pd.Series:
    x = pd.to_numeric(m, errors="coerce")
    out = pd.Series(["missing"] * len(m), index=m.index, dtype="object")
    out[(x >= 0) & (x <= 30)] = "m0_30"
    out[(x >= 31) & (x <= 60)] = "m31_60"
    out[(x >= 61) & (x <= 120)] = "m61_120"
    out[(x >= 121) & (x <= 240)] = "m121_240"
    out[x >= 241] = "m241p"
    out[x.isna()] = "missing"
    return out


def summarize_unknown_by(
    unk: pd.DataFrame,
    bucket_col: str,
    r_col: str = "r_multiple",
    min_n: int = 5,
) -> pd.DataFrame:
    """Metrics within regime_unknown subset; shares relative to unknown rows."""
    if unk.empty or bucket_col not in unk.columns:
        return pd.DataFrame()
    base_n = len(unk)
    base_r = float(unk[r_col].astype(float).sum())
    rows = []
    for key, g in unk.groupby(bucket_col, dropna=False):
        n = len(g)
        rs = g[r_col].astype(float)
        pf = profit_factor_r(rs)
        rows.append(
            {
                "bucket": key,
                "trades": n,
                "total_r": float(rs.sum()),
                "avg_r": float(rs.mean()) if n else 0.0,
                "median_r": float(rs.median()) if n else 0.0,
                "win_rate": float((rs > 0).mean()) if n else 0.0,
                "pf_r": float(pf) if math.isfinite(pf) else None,
                "max_loss_r": float(rs.min()) if n else 0.0,
                "share_unknown_trades": float(n / base_n) if base_n else 0.0,
                "share_unknown_pnl": float(rs.sum() / base_r) if base_r != 0 else 0.0,
                "low_sample_warning": n < min_n,
            }
        )
    return pd.DataFrame(rows).sort_values("bucket")


def prepare_unknown_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Filter entry_regime_label == regime_unknown and add bucket columns."""
    reg = df.get("entry_regime_label", pd.Series("", index=df.index)).astype(str)
    unk = df.loc[reg.eq("regime_unknown")].copy()
    if unk.empty:
        return unk
    unk["unk_minute_bucket"] = minute_bucket_open(
        unk.get("entry_minute_from_open", pd.Series(np.nan, index=unk.index))
    )
    vc_raw = unk.get("entry_vwap_cross_count")
    if vc_raw is None:
        vc = pd.Series(np.nan, index=unk.index, dtype=float)
    else:
        vc = pd.to_numeric(vc_raw, errors="coerce")
    unk["unk_vwap_x_bucket"] = pd.cut(
        vc, bins=[-np.inf, 2, 5, 10, np.inf], labels=["xc0_2", "xc3_5", "xc6_10", "xc10p"]
    ).astype(str)
    for col, prefix, src in [
        ("unk_reff_bucket", "re", "entry_range_efficiency"),
        ("unk_trend_bucket", "tr", "entry_trend_score"),
        ("unk_comp_bucket", "cp", "entry_compression_score"),
        ("unk_pa_brk", "brk", "entry_pa_strong_breakout_score"),
        ("unk_pa_tr", "trg", "entry_pa_trading_range_score"),
        ("unk_pa_clx", "clx", "entry_pa_climax_score"),
        ("unk_pa_lt", "lt", "entry_pa_late_trend_score"),
        ("unk_dvwap", "dv", "entry_distance_from_vwap_atr"),
    ]:
        if src in unk.columns:
            unk[col] = bucket_quantiles(pd.to_numeric(unk[src], errors="coerce"), prefix=prefix)
        else:
            unk[col] = "missing"
    ah = pd.to_numeric(unk.get("entry_above_vwap"), errors="coerce")
    bl = pd.to_numeric(unk.get("entry_below_vwap"), errors="coerce")
    unk["unk_vwap_side"] = np.where(ah >= 1, "above", np.where(bl >= 1, "below", "other"))
    if "entry_above_orb_high" in unk.columns and "entry_below_orb_low" in unk.columns:
        oa = pd.to_numeric(unk["entry_above_orb_high"], errors="coerce")
        ob = pd.to_numeric(unk["entry_below_orb_low"], errors="coerce")
        unk["unk_orb_ctx"] = np.where(oa >= 1, "above_orb", np.where(ob >= 1, "below_orb", "inside_other"))
    else:
        unk["unk_orb_ctx"] = "missing"
    nm = unk.get("entry_nearest_magnet")
    if nm is not None:
        unk["unk_magnet"] = nm.astype(str).str.slice(0, 40)
    else:
        unk["unk_magnet"] = "missing"
    unk["unk_exit"] = unk.get("exit_reason", "").astype(str)
    unk["unk_trade_num"] = pd.to_numeric(unk.get("entry_trade_number_of_day"), errors="coerce").fillna(0).astype(int)
    pl = unk.get("entry_prior_trade_was_loss")
    unk["unk_prior"] = "first_or_unknown"
    if pl is not None:
        pls = pd.Series(pl, index=unk.index)
        unk.loc[pls == True, "unk_prior"] = "after_loss"
        unk.loc[pls == False, "unk_prior"] = "after_win"
        unk.loc[pls == 1.0, "unk_prior"] = "after_loss"
        unk.loc[pls == 0.0, "unk_prior"] = "after_win"
    return unk
