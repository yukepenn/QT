"""Session VWAP and distance / band features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_vwap(
    df: pd.DataFrame,
    *,
    typical_price: bool = True,
    bands: tuple[float, ...] = (1.0, 2.0),
    z_window: int | None = None,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    del z_window  # reserved for future bounded expanding window
    module_name = "vwap"
    base_cols = list(FEATURE_COLUMNS[module_name])
    extra_band_cols: list[str] = []
    default_bands = {1.0, 2.0}

    def _is_default_band(x: float) -> bool:
        fx = float(x)
        return any(abs(fx - d) < 1e-9 for d in default_bands)

    for k in bands:
        if not _is_default_band(k):
            extra_band_cols.extend([f"vwap_upper_{k}", f"vwap_lower_{k}"])

    add_or_overwrite_columns(df, base_cols + extra_band_cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "open", "high", "low", "close", "volume"], context="vwap")

    out = safe_copy(df, copy)

    price = (out["high"] + out["low"] + out["close"]) / 3.0 if typical_price else out["close"].astype(float)
    out["_v"] = out["volume"].astype(float)
    out["_pv"] = price * out["_v"]
    cum_pv = out.groupby("session_date", sort=False)["_pv"].cumsum()
    cum_v = out.groupby("session_date", sort=False)["_v"].cumsum()
    out["vwap"] = cum_pv / cum_v.replace(0.0, float("nan"))
    out["vwap"] = out.groupby("session_date", sort=False)["vwap"].ffill()
    out.drop(columns=["_pv", "_v"], inplace=True)

    out["vwap_dist"] = out["close"].astype(float) - out["vwap"]
    out["vwap_dist_pct"] = out["close"].astype(float) / out["vwap"] - 1.0

    c = out["close"].astype(float)
    vw = out["vwap"]
    out["vwap_side"] = 0
    out.loc[c > vw, "vwap_side"] = 1
    out.loc[c < vw, "vwap_side"] = -1

    dev = c - vw
    centered = out["close"].astype(float) - out["vwap"]
    out["vwap_std"] = centered.groupby(out["session_date"]).transform(lambda s: s.expanding().std())

    vz = dev / out["vwap_std"]
    vz = vz.replace([float("inf"), float("-inf")], pd.NA)
    out["vwap_z"] = vz

    gv = out.groupby("session_date", sort=False)["vwap"]
    out["vwap_slope_5"] = gv.diff(5)
    out["vwap_slope_15"] = gv.diff(15)
    for _n in (20, 30, 60):
        out[f"vwap_slope_{_n}"] = gv.diff(_n)

    c = out["close"].astype(float)
    vw = out["vwap"].astype(float)
    out["close_above_vwap"] = (c > vw).astype(np.int8)
    out["close_below_vwap"] = (c < vw).astype(np.int8)

    g_sess = out.groupby("session_date", sort=False)
    for _pw in (10, 20, 30, 60):
        out[f"vwap_persistence_above_{_pw}"] = g_sess["close_above_vwap"].transform(
            lambda s, w=_pw: s.astype(float).rolling(w, min_periods=1).mean().shift(1)
        )
        out[f"vwap_persistence_below_{_pw}"] = g_sess["close_below_vwap"].transform(
            lambda s, w=_pw: s.astype(float).rolling(w, min_periods=1).mean().shift(1)
        )

    for k in bands:
        ku = f"vwap_upper_{k}"
        kl = f"vwap_lower_{k}"
        out[ku] = vw + float(k) * out["vwap_std"]
        out[kl] = vw - float(k) * out["vwap_std"]

    return out
