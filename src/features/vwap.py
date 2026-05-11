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
    sess = out["session_date"]

    price = (
        (out["high"] + out["low"] + out["close"]) / 3.0
        if typical_price
        else out["close"].astype(float)
    )
    v_vol = out["volume"].astype(float)
    pv = price.astype(float) * v_vol
    cum_pv = pv.groupby(sess, sort=False).cumsum()
    cum_v = v_vol.groupby(sess, sort=False).cumsum()
    vwap = cum_pv / cum_v.replace(0.0, float("nan"))
    vwap = vwap.groupby(sess, sort=False).ffill()

    c = out["close"].astype(float)
    vw = vwap
    vwap_dist = c - vw
    vwap_dist_pct = c / vw - 1.0
    vwap_side = pd.Series(np.where(c > vw, 1, np.where(c < vw, -1, 0)), index=out.index, dtype=np.int8)

    dev = c - vw
    centered = c - vw
    vwap_std = centered.groupby(sess, sort=False).transform(lambda s: s.expanding().std())

    vz = dev / vwap_std
    vz = vz.replace([float("inf"), float("-inf")], pd.NA)
    vwap_z = vz

    gv = vwap.groupby(sess, sort=False)
    vwap_slope_5 = gv.diff(5)
    vwap_slope_15 = gv.diff(15)
    slope_extra: dict[str, pd.Series] = {}
    for _n in (20, 30, 60):
        slope_extra[f"vwap_slope_{_n}"] = gv.diff(_n)

    close_above = (c > vw.astype(float)).astype(np.int8)
    close_below = (c < vw.astype(float)).astype(np.int8)
    g_sess = close_above.groupby(sess, sort=False)
    g_sess_b = close_below.groupby(sess, sort=False)

    persist: dict[str, pd.Series] = {}
    for _pw in (10, 20, 30, 60):
        persist[f"vwap_persistence_above_{_pw}"] = g_sess.transform(
            lambda s, w=_pw: s.astype(float).rolling(w, min_periods=1).mean().shift(1)
        )
        persist[f"vwap_persistence_below_{_pw}"] = g_sess_b.transform(
            lambda s, w=_pw: s.astype(float).rolling(w, min_periods=1).mean().shift(1)
        )

    band_cols: dict[str, pd.Series] = {}
    vw_f = vw.astype(float)
    vstd = vwap_std
    for k in bands:
        ku = f"vwap_upper_{k}"
        kl = f"vwap_lower_{k}"
        fk = float(k)
        band_cols[ku] = vw_f + fk * vstd
        band_cols[kl] = vw_f - fk * vstd

    new_cols: dict[str, pd.Series] = {
        "vwap": vwap,
        "vwap_dist": vwap_dist,
        "vwap_dist_pct": vwap_dist_pct,
        "vwap_side": vwap_side,
        "vwap_std": vwap_std,
        "vwap_z": vwap_z,
        "vwap_slope_5": vwap_slope_5,
        "vwap_slope_15": vwap_slope_15,
        "close_above_vwap": close_above,
        "close_below_vwap": close_below,
        **slope_extra,
        **persist,
        **band_cols,
    }

    return pd.concat([out, pd.DataFrame(new_cols)], axis=1)
