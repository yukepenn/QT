"""Prior-exclusive PA swing / rolling-range features (no centered pivots, no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

from src.features.build_types import PaFeatureConfig
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


@njit(cache=True)
def _bars_since_last_in_session(
    flag: np.ndarray, session_id: np.ndarray, n: int, cap: int
) -> np.ndarray:
    """Bars since last flag==1 in same session; if none in session, cap; else min(age, cap)."""
    out = np.zeros(n, dtype=np.int32)
    last = -1_000_000_000
    cur_sid = -9_999_999_999
    for i in range(n):
        sid = session_id[i]
        if sid != cur_sid:
            cur_sid = sid
            last = -1_000_000_000
        if flag[i] != 0:
            last = i
        if last < -100_000_000:
            out[i] = cap
        else:
            d = i - last
            out[i] = d if d < cap else cap
    return out


@njit(cache=True)
def _rolling_sum_shift1_session(
    x: np.ndarray, session_id: np.ndarray, n: int, w: int
) -> np.ndarray:
    """Prior-exclusive rolling sum: sum of x over last w bars in session ending at t-1."""
    out = np.zeros(n, dtype=np.float64)
    for i in range(n):
        acc = 0.0
        cnt = 0
        j = i - 1
        while j >= 0 and cnt < w and session_id[j] == session_id[i]:
            acc += x[j]
            cnt += 1
            j -= 1
        out[i] = acc
    return out


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
                f"pa_pullback_bar_count_{nn}",
                f"pa_two_leg_pullback_down_{nn}",
                f"pa_two_leg_pullback_up_{nn}",
                f"pa_second_entry_buy_proxy_{nn}",
                f"pa_second_entry_sell_proxy_{nn}",
                f"pa_failed_breakout_age_{nn}",
                f"pa_breakout_attempt_count_up_{nn}",
                f"pa_breakout_attempt_count_down_{nn}",
                f"pa_trapped_bears_score_{nn}",
                f"pa_trapped_bulls_score_{nn}",
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

    sid = pd.factorize(out["session_date"], sort=False)[0].astype(np.int32)
    n_b = len(out)

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

        # Session-scoped prior bar vs prior-bar range anchor (no cross-session leak).
        prev_h = g["high"].shift(1)
        prev_lo = g["low"].shift(1)
        sd_series = out["session_date"]
        prev_rh = rh.groupby(sd_series, sort=False).shift(1)
        prev_rl = rl.groupby(sd_series, sort=False).shift(1)
        outside_prev = (prev_h > prev_rh) | (prev_lo < prev_rl)
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

        fbd_i = new_cols[f"pa_failed_breakout_down_{nn}"].to_numpy(dtype=np.int8)
        fbu_i = new_cols[f"pa_failed_breakout_up_{nn}"].to_numpy(dtype=np.int8)
        cbi_i = new_cols[f"pa_close_back_inside_{nn}"].to_numpy(dtype=np.int8)
        depth_np = depth
        mid_np = mid_s.to_numpy(dtype=float)
        c_np = c.to_numpy(dtype=float)

        new_cols[f"pa_failed_breakout_age_{nn}"] = pd.Series(
            _bars_since_last_in_session(fbd_i, sid, n_b, nn),
            index=out.index,
            dtype=np.int32,
        )
        pull_streak = np.zeros(n_b, dtype=np.int32)
        cur_sid_pb = -9_999_999_999
        st_pull = 0
        for ii in range(n_b):
            if sid[ii] != cur_sid_pb:
                cur_sid_pb = sid[ii]
                st_pull = 0
            ipb = bool(depth_np[ii] > 0.1) and bool(c_np[ii] < mid_np[ii])
            if ipb:
                st_pull += 1
            else:
                st_pull = 0
            pull_streak[ii] = st_pull
        new_cols[f"pa_pullback_bar_count_{nn}"] = pd.Series(
            pull_streak, index=out.index, dtype=np.int32
        )

        fbd_roll = (
            new_cols[f"pa_failed_breakout_down_{nn}"]
            .groupby(sd_series)
            .transform(lambda s: s.rolling(5, min_periods=1).sum())
            .fillna(0.0)
        )
        lo_s1 = g["low"].shift(1)
        lo_s2 = g["low"].shift(2)
        rising2 = (lo > lo_s1) & (lo_s1 > lo_s2)
        two_down = (fbd_roll >= 1.0) & rising2.fillna(False) & (c.astype(float) < mid_s)
        new_cols[f"pa_two_leg_pullback_down_{nn}"] = two_down.astype(np.int8)

        fbu_roll = (
            new_cols[f"pa_failed_breakout_up_{nn}"]
            .groupby(sd_series)
            .transform(lambda s: s.rolling(5, min_periods=1).sum())
            .fillna(0.0)
        )
        hi_s1 = g["high"].shift(1)
        hi_s2 = g["high"].shift(2)
        fall2 = (h < hi_s1) & (hi_s1 < hi_s2)
        two_up = (fbu_roll >= 1.0) & fall2.fillna(False) & (c.astype(float) > mid_s)
        new_cols[f"pa_two_leg_pullback_up_{nn}"] = two_up.astype(np.int8)

        bull_rev = (
            out["bull_reversal_bar"].astype(np.int8)
            if "bull_reversal_bar" in out.columns
            else pd.Series(0, index=out.index, dtype=np.int8)
        )
        bear_rev = (
            out["bear_reversal_bar"].astype(np.int8)
            if "bear_reversal_bar" in out.columns
            else pd.Series(0, index=out.index, dtype=np.int8)
        )
        sbc = (
            out["strong_bull_close"].astype(np.int8)
            if "strong_bull_close" in out.columns
            else pd.Series(0, index=out.index, dtype=np.int8)
        )
        sbe = (
            out["strong_bear_close"].astype(np.int8)
            if "strong_bear_close" in out.columns
            else pd.Series(0, index=out.index, dtype=np.int8)
        )
        sec_buy = (
            two_down
            & ((bull_rev != 0) | (sbc != 0))
            & (
                (new_cols[f"pa_higher_low_proxy_{nn}"] != 0)
                | (lo.astype(float) > rl.astype(float))
            )
        ).astype(np.int8)
        new_cols[f"pa_second_entry_buy_proxy_{nn}"] = sec_buy

        sec_sell = (
            two_up
            & ((bear_rev != 0) | (sbe != 0))
            & ((h.astype(float) < rh.astype(float)) | (h.astype(float) < hi_s1.fillna(h)))
        ).astype(np.int8)
        new_cols[f"pa_second_entry_sell_proxy_{nn}"] = sec_sell

        att_u = ((h > rh) | (c > rh)).astype(np.float64).to_numpy()
        att_d = ((lo < rl) | (c < rl)).astype(np.float64).to_numpy()
        new_cols[f"pa_breakout_attempt_count_up_{nn}"] = pd.Series(
            _rolling_sum_shift1_session(att_u, sid, n_b, nn),
            index=out.index,
            dtype=np.float64,
        )
        new_cols[f"pa_breakout_attempt_count_down_{nn}"] = pd.Series(
            _rolling_sum_shift1_session(att_d, sid, n_b, nn),
            index=out.index,
            dtype=np.float64,
        )

        sbc_f = sbc.astype(float)
        trapped_b = np.clip(
            0.35 * fbd_i.astype(float)
            + 0.35 * cbi_i.astype(float)
            + 0.3 * sbc_f.to_numpy(dtype=float),
            0.0,
            1.0,
        )
        new_cols[f"pa_trapped_bears_score_{nn}"] = pd.Series(
            trapped_b, index=out.index, dtype=float
        )
        trapped_u = np.clip(
            0.35 * fbu_i.astype(float)
            + 0.35 * bear_rev.astype(float)
            + 0.3 * sbe.astype(float),
            0.0,
            1.0,
        )
        new_cols[f"pa_trapped_bulls_score_{nn}"] = pd.Series(
            trapped_u, index=out.index, dtype=float
        )

    out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
