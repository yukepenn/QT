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

    out["ret_1m"] = out.groupby("session_date", sort=False)["close"].pct_change()

    prev_close = out.groupby("session_date", sort=False)["close"].shift(1)
    hl = out["high"].astype(float) - out["low"].astype(float)
    tr = pd.concat(
        [
            hl,
            (out["high"].astype(float) - prev_close).abs(),
            (out["low"].astype(float) - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["tr"] = tr

    for w in windows:
        ww = int(w)
        out[f"ret_std_{ww}"] = out.groupby("session_date", sort=False)["ret_1m"].transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).std()
        )
        hmax = out.groupby("session_date", sort=False)["high"].transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).max()
        )
        lmin = out.groupby("session_date", sort=False)["low"].transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).min()
        )
        out[f"range_{ww}"] = hmax - lmin
        out[f"range_pct_{ww}"] = out[f"range_{ww}"] / out["close"].astype(float)
        out[f"atr_like_{ww}"] = out.groupby("session_date", sort=False)["tr"].transform(
            lambda x, n=ww: x.rolling(n, min_periods=1).mean()
        )

    return out
