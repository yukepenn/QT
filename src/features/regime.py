"""Lightweight intraday regime proxies (session-scoped, no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import RegimeFeatureConfig
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def regime_column_names(spec: RegimeFeatureConfig) -> list[str]:
    cols: list[str] = []
    for w in spec.windows:
        cols.extend(
            [
                f"range_efficiency_{w}",
                f"vwap_cross_count_{w}",
                f"trend_score_{w}",
                f"compression_score_{w}",
            ]
        )
    return cols


def add_regime_features(
    df: pd.DataFrame,
    spec: RegimeFeatureConfig,
    *,
    atr_col: str = "atr_like_20",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    cols = regime_column_names(spec)
    if not cols:
        return safe_copy(df, copy)

    add_or_overwrite_columns(df, cols, module_name="regime", allow_overwrite=allow_overwrite)
    ensure_columns(df, ["session_date", "close", "vwap", atr_col], context="regime")

    out = safe_copy(df, copy)
    sd = out["session_date"]
    g = out.groupby(sd, sort=False)
    c = out["close"].astype(float)
    atr = out[atr_col].astype(float)

    vwap_side = (c > out["vwap"].astype(float)).astype(np.int8)
    prev_side = vwap_side.groupby(sd).transform(lambda s: s.shift(1))
    cross = (vwap_side != prev_side.fillna(vwap_side)).astype(np.int8)

    new_cols: dict[str, pd.Series] = {}
    for w in spec.windows:
        prev_c = g["close"].transform(lambda s, ww=w: s.shift(ww))
        net_move = (c - prev_c).abs()
        roll_sum = g["close"].transform(lambda s, ww=w: s.diff().abs().rolling(ww, min_periods=1).sum())
        new_cols[f"range_efficiency_{w}"] = net_move / (roll_sum + 1e-12)

        new_cols[f"vwap_cross_count_{w}"] = cross.groupby(sd).transform(
            lambda s, ww=w: s.rolling(ww, min_periods=1).sum()
        )

        new_cols[f"trend_score_{w}"] = (c - prev_c) / (atr + 1e-12)

        hi = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).max())
        lo = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).min())
        rng = hi - lo
        new_cols[f"compression_score_{w}"] = (1.0 - (rng / (atr * float(w) + 1e-12))).clip(lower=0.0, upper=1.0)

    if new_cols:
        out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
