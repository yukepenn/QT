"""Bollinger and Donchian-style channel features (session-scoped, no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import ChannelsFeatureConfig
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def channel_column_names(spec: ChannelsFeatureConfig) -> list[str]:
    cols: list[str] = []
    for w in spec.bb_windows:
        cols.append(f"bb_mid_{w}")
        for std in spec.bb_stds:
            cols.extend(
                [
                    f"bb_upper_{w}_{std}",
                    f"bb_lower_{w}_{std}",
                    f"bb_width_{w}_{std}",
                    f"bb_percent_b_{w}_{std}",
                ]
            )
            for lb in spec.bb_bandwidth_lookbacks:
                cols.append(f"bb_width_percentile_{w}_{std}_{lb}")
                cols.append(f"bb_squeeze_{w}_{std}_{lb}")
    for dw in spec.donchian_windows:
        cols.extend(
            [
                f"donchian_high_{dw}_prior",
                f"donchian_low_{dw}_prior",
                f"donchian_mid_{dw}_prior",
                f"donchian_width_atr_{dw}",
            ]
        )
    return cols


def _pct_rank_last(arr: np.ndarray) -> float:
    if arr is None or len(arr) < 2 or not np.isfinite(arr[-1]):
        return np.nan
    return float(np.nansum(arr[:-1] < arr[-1])) / max(1, len(arr) - 1)


def add_channel_features(
    df: pd.DataFrame,
    spec: ChannelsFeatureConfig,
    *,
    squeeze_quantile: float = 0.25,
    atr_col: str = "atr_like_20",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    cols = channel_column_names(spec)
    if not cols:
        return safe_copy(df, copy)

    add_or_overwrite_columns(df, cols, module_name="channels", allow_overwrite=allow_overwrite)
    need = ["session_date", "open", "high", "low", "close"]
    if spec.donchian_windows:
        need.append(atr_col)
    ensure_columns(df, need, context="channels")

    out = safe_copy(df, copy)
    sd = out["session_date"]
    g = out.groupby(sd, sort=False)
    c = out["close"].astype(float)
    atr = out[atr_col].astype(float)

    new_cols: dict[str, pd.Series] = {}

    for w in spec.bb_windows:
        mid = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).mean())
        new_cols[f"bb_mid_{w}"] = mid
        dev_base = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).std()).fillna(0.0)
        for std in spec.bb_stds:
            stdf = float(std)
            upper = mid + stdf * dev_base
            lower = mid - stdf * dev_base
            new_cols[f"bb_upper_{w}_{std}"] = upper
            new_cols[f"bb_lower_{w}_{std}"] = lower
            width = (upper - lower) / (mid.replace(0, np.nan) + 1e-12)
            bw_name = f"bb_width_{w}_{std}"
            new_cols[bw_name] = width
            new_cols[f"bb_percent_b_{w}_{std}"] = (c - lower) / (upper - lower + 1e-12)

            lag_w = new_cols[bw_name].groupby(sd).transform(lambda s: s.shift(1))
            for lb in spec.bb_bandwidth_lookbacks:
                rank = lag_w.groupby(sd).transform(
                    lambda s, lbb=lb: s.rolling(lbb, min_periods=3).apply(_pct_rank_last, raw=True)
                )
                new_cols[f"bb_width_percentile_{w}_{std}_{lb}"] = rank
                q = lag_w.groupby(sd).transform(
                    lambda s, lbb=lb, sq=squeeze_quantile: s.rolling(lbb, min_periods=3).quantile(sq)
                )
                new_cols[f"bb_squeeze_{w}_{std}_{lb}"] = (lag_w <= q).astype(np.int8)

    for dw in spec.donchian_windows:
        dh = g["high"].transform(lambda s, d=dw: s.shift(1).rolling(d, min_periods=1).max())
        dl = g["low"].transform(lambda s, d=dw: s.shift(1).rolling(d, min_periods=1).min())
        new_cols[f"donchian_high_{dw}_prior"] = dh
        new_cols[f"donchian_low_{dw}_prior"] = dl
        new_cols[f"donchian_mid_{dw}_prior"] = (dh + dl) / 2.0
        ch_w = dh - dl
        new_cols[f"donchian_width_atr_{dw}"] = ch_w / (atr + 1e-12)

    if new_cols:
        out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
