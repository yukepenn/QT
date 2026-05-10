"""Prior-exclusive PA swing / rolling-range features (no centered pivots, no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def pa_swing_column_names(spec: PaFeatureConfig) -> list[str]:
    cols: list[str] = []
    for n in spec.swing_windows:
        nn = int(n)
        cols.extend(
            [
                f"pa_prior_high_{nn}",
                f"pa_prior_low_{nn}",
                f"pa_range_high_{nn}",
                f"pa_range_low_{nn}",
                f"pa_range_mid_{nn}",
                f"pa_range_upper_third_{nn}",
                f"pa_range_lower_third_{nn}",
                f"pa_range_width_{nn}",
                f"pa_range_width_atr_{nn}",
                f"pa_breakout_up_{nn}",
                f"pa_breakout_down_{nn}",
                f"pa_close_back_inside_{nn}",
                f"pa_failed_breakout_up_{nn}",
                f"pa_failed_breakout_down_{nn}",
                f"pa_leg_direction_{nn}",
                f"pa_pullback_depth_atr_{nn}",
                f"pa_wedge_push_count_{nn}",
                f"pa_higher_low_proxy_{nn}",
            ]
        )
    return cols


def add_pa_swing_features(
    df: pd.DataFrame,
    spec: PaFeatureConfig,
    *,
    atr_col: str = "atr_like_20",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    cols = pa_swing_column_names(spec)
    if not cols:
        return safe_copy(df, copy)

    add_or_overwrite_columns(
        df, cols, module_name="pa_swings", allow_overwrite=allow_overwrite
    )
    ensure_columns(
        df, ["session_date", "open", "high", "low", "close"], context="pa_swings"
    )
    if atr_col not in df.columns:
        raise ValueError(
            f"pa_swings requires {atr_col!r} (extend features.vol_windows / indicators)"
        )

    out = safe_copy(df, copy)
    g = out.groupby("session_date", sort=False)
    h = out["high"].astype(float)
    lo = out["low"].astype(float)
    c = out["close"].astype(float)
    atr = out[atr_col].astype(float)

    new_cols: dict[str, pd.Series] = {}
    for n in spec.swing_windows:
        nn = int(n)
        # Prior-exclusive rolling extrema: rolling max/min over N bars ending at t-1 (shift after rolling).
        rh = g["high"].transform(
            lambda s, w=nn: s.rolling(w, min_periods=1).max().shift(1)
        )
        rl = g["low"].transform(
            lambda s, w=nn: s.rolling(w, min_periods=1).min().shift(1)
        )
        new_cols[f"pa_prior_high_{nn}"] = rh
        new_cols[f"pa_prior_low_{nn}"] = rl
        new_cols[f"pa_range_high_{nn}"] = rh
        new_cols[f"pa_range_low_{nn}"] = rl
        width = (rh - rl).astype(float)
        new_cols[f"pa_range_width_{nn}"] = width
        mid = (rh + rl) * 0.5
        new_cols[f"pa_range_mid_{nn}"] = mid
        new_cols[f"pa_range_upper_third_{nn}"] = rl + (2.0 / 3.0) * width
        new_cols[f"pa_range_lower_third_{nn}"] = rl + (1.0 / 3.0) * width
        new_cols[f"pa_range_width_atr_{nn}"] = width / (atr + 1e-12)

        new_cols[f"pa_breakout_up_{nn}"] = ((c > rh) | (h > rh)).astype(np.int8)
        new_cols[f"pa_breakout_down_{nn}"] = ((c < rl) | (lo < rl)).astype(np.int8)

        outside_prev = (h.shift(1) > rh.shift(1)) | (lo.shift(1) < rl.shift(1))
        inside_now = (c >= rl) & (c <= rh)
        new_cols[f"pa_close_back_inside_{nn}"] = (
            inside_now & outside_prev.fillna(False)
        ).astype(np.int8)

        new_cols[f"pa_failed_breakout_down_{nn}"] = ((lo < rl) & (c > rl)).astype(
            np.int8
        )
        new_cols[f"pa_failed_breakout_up_{nn}"] = ((h > rh) & (c < rh)).astype(np.int8)

        prev_c = g["close"].transform(lambda s, w=nn: s.shift(nn))
        ld = c.astype(float) - prev_c.astype(float)
        leg = np.sign(
            np.where(
                np.isfinite(ld.to_numpy(dtype=float)), ld.to_numpy(dtype=float), 0.0
            )
        ).astype(np.int8)
        new_cols[f"pa_leg_direction_{nn}"] = pd.Series(
            leg, index=out.index, dtype=np.int8
        )

        mid_s = mid.astype(float)
        up_leg = c.astype(float) > mid_s
        depth = np.where(
            up_leg,
            (rh.astype(float) - c.astype(float)) / (atr + 1e-12),
            (c.astype(float) - rl.astype(float)) / (atr + 1e-12),
        )
        new_cols[f"pa_pullback_depth_atr_{nn}"] = pd.Series(
            depth, index=out.index, dtype=float
        )

        rising = (lo > g["low"].shift(1)).astype(float)
        wsum = rising.groupby(out["session_date"]).transform(
            lambda s, w=nn: s.rolling(w, min_periods=1).sum().shift(1)
        )
        new_cols[f"pa_wedge_push_count_{nn}"] = wsum.clip(lower=0.0, upper=float(nn))

        # Prior range low vs current low: coarse "higher low" vs the rolling buy zone anchor.
        new_cols[f"pa_higher_low_proxy_{nn}"] = (lo > rl).astype(np.int8)

    out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
