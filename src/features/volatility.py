"""Intraday volatility-style rolling stats (session-scoped)."""

from __future__ import annotations

import pandas as pd

from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def _volatility_col_names(windows: tuple[int, ...]) -> list[str]:
    names = ["ret_1m", "tr"]
    for w in windows:
        names.extend([f"ret_std_{w}", f"range_{w}", f"range_pct_{w}", f"atr_like_{w}"])
    return names


def add_intraday_volatility(
    df: pd.DataFrame,
    *,
    windows: tuple[int, ...] = (5, 15, 30),
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "volatility"
    cols = _volatility_col_names(windows)
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "high", "low", "close"], context="volatility")

    out = safe_copy(df, copy)
    g = out.groupby("session_date", sort=False)
    sess = out["session_date"]

    ret_1m = g["close"].pct_change()
    prev_close = g["close"].shift(1)
    hl = out["high"].astype(float) - out["low"].astype(float)
    tr = pd.concat(
        [
            hl,
            (out["high"].astype(float) - prev_close).abs(),
            (out["low"].astype(float) - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    new_cols: dict[str, pd.Series] = {
        "ret_1m": ret_1m,
        "tr": tr,
    }

    g_ret = ret_1m.groupby(sess, sort=False)
    g_hi = out["high"].astype(float).groupby(sess, sort=False)
    g_lo = out["low"].astype(float).groupby(sess, sort=False)
    g_tr = tr.groupby(sess, sort=False)
    close_f = out["close"].astype(float)

    for w in windows:
        ww = int(w)
        new_cols[f"ret_std_{ww}"] = g_ret.transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).std()
        )
        hmax = g_hi.transform(lambda x, n=ww: x.rolling(n, min_periods=1).max())
        lmin = g_lo.transform(lambda x, n=ww: x.rolling(n, min_periods=1).min())
        rng = hmax - lmin
        new_cols[f"range_{ww}"] = rng
        new_cols[f"range_pct_{ww}"] = rng / close_f
        new_cols[f"atr_like_{ww}"] = g_tr.transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).mean()
        )

    return pd.concat([out, pd.DataFrame(new_cols)], axis=1)
