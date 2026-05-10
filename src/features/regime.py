"""Lightweight intraday regime proxies (session-scoped, no lookahead)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig, RegimeFeatureConfig
from src.features.pa_brooks_enums import (
    PA_ALWAYS_IN_LONG,
    PA_ALWAYS_IN_NEUTRAL,
    PA_ALWAYS_IN_SHORT,
    PA_REGIME_BROAD_BEAR_CHANNEL,
    PA_REGIME_BROAD_BULL_CHANNEL,
    PA_REGIME_LATE_TREND_CLIMAX,
    PA_REGIME_STRONG_BEAR_BREAKOUT,
    PA_REGIME_STRONG_BULL_BREAKOUT,
    PA_REGIME_TIGHT_BEAR_CHANNEL,
    PA_REGIME_TIGHT_BULL_CHANNEL,
    PA_REGIME_TRADING_RANGE,
    PA_REGIME_UNKNOWN,
    PA_TRADE_MODE_CLIMAX,
    PA_TRADE_MODE_NEUTRAL,
    PA_TRADE_MODE_RANGE,
    PA_TRADE_MODE_TREND_LONG,
    PA_TRADE_MODE_TREND_SHORT,
)
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def _range_efficiency_session(g: Any, w: int, c: pd.Series) -> pd.Series:
    prev_c = g["close"].transform(lambda s, ww=w: s.shift(ww))
    net_move = (c - prev_c).abs()
    roll_sum = g["close"].transform(
        lambda s, ww=w: s.diff().abs().rolling(ww, min_periods=1).sum()
    )
    return net_move / (roll_sum + 1e-12)


def _trend_score_session(g: Any, w: int, c: pd.Series, atr: pd.Series) -> pd.Series:
    prev_c = g["close"].transform(lambda s, ww=w: s.shift(ww))
    return (c - prev_c) / (atr + 1e-12)


def pa_regime_column_names(pa: PaFeatureConfig) -> list[str]:
    cols: list[str] = []
    for n in pa.regime_windows:
        nn = int(n)
        cols.extend(
            [
                f"pa_strong_breakout_score_{nn}",
                f"pa_tight_bull_channel_score_{nn}",
                f"pa_tight_bear_channel_score_{nn}",
                f"pa_broad_bull_channel_score_{nn}",
                f"pa_broad_bear_channel_score_{nn}",
                f"pa_bar_range_expansion_{nn}",
                f"pa_trading_range_score_{nn}",
                f"pa_climax_score_{nn}",
                f"pa_overlap_score_{nn}",
                f"pa_followthrough_up_{nn}",
                f"pa_followthrough_down_{nn}",
                f"pa_always_in_side_{nn}",
                f"pa_regime_label_{nn}",
                f"pa_trade_mode_{nn}",
                f"pa_late_trend_score_{nn}",
                f"pa_trend_to_tr_transition_score_{nn}",
                f"pa_limit_order_market_score_{nn}",
            ]
        )
    cols.append("pa_distance_from_vwap_atr")
    return cols


def regime_column_names(
    spec: RegimeFeatureConfig, pa: PaFeatureConfig | None = None
) -> list[str]:
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
    p = pa or PaFeatureConfig()
    cols.extend(pa_regime_column_names(p))
    return cols


def add_regime_features(
    df: pd.DataFrame,
    spec: RegimeFeatureConfig,
    *,
    pa: PaFeatureConfig | None = None,
    atr_col: str = "atr_like_20",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    pa_spec = pa or PaFeatureConfig()
    cols = regime_column_names(spec, pa_spec)
    if not cols:
        return safe_copy(df, copy)

    add_or_overwrite_columns(
        df, cols, module_name="regime", allow_overwrite=allow_overwrite
    )
    ensure_columns(df, ["session_date", "close", "vwap", atr_col], context="regime")

    out = safe_copy(df, copy)
    if "bar_range" not in out.columns:
        out["bar_range"] = (out["high"].astype(float) - out["low"].astype(float)).abs()
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
        roll_sum = g["close"].transform(
            lambda s, ww=w: s.diff().abs().rolling(ww, min_periods=1).sum()
        )
        new_cols[f"range_efficiency_{w}"] = net_move / (roll_sum + 1e-12)

        new_cols[f"vwap_cross_count_{w}"] = cross.groupby(sd).transform(
            lambda s, ww=w: s.rolling(ww, min_periods=1).sum()
        )

        new_cols[f"trend_score_{w}"] = (c - prev_c) / (atr + 1e-12)

        hi = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).max())
        lo = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).min())
        rng = hi - lo
        new_cols[f"compression_score_{w}"] = (
            1.0 - (rng / (atr * float(w) + 1e-12))
        ).clip(lower=0.0, upper=1.0)

    # --- PA coarse regime scores (interpretable, not aggressively tuned) ---
    cloc = (
        out["close_location"].astype(float)
        if "close_location" in out.columns
        else pd.Series(0.5, index=out.index)
    )
    body_pct = (
        out["body_pct"].astype(float)
        if "body_pct" in out.columns
        else pd.Series(0.0, index=out.index)
    )
    overlap_b = (
        out["overlap_bar"].astype(float)
        if "overlap_bar" in out.columns
        else pd.Series(0.0, index=out.index)
    )
    bull_b = (
        out["bull_bar"].astype(float)
        if "bull_bar" in out.columns
        else out["is_green"].astype(float)
    )
    bear_b = (
        out["bear_bar"].astype(float)
        if "bear_bar" in out.columns
        else out["is_red"].astype(float)
    )

    for n in pa_spec.regime_windows:
        nn = int(n)
        brk_u = out.get(
            f"pa_breakout_up_{nn}", pd.Series(0, index=out.index, dtype=float)
        ).astype(float)
        brk_d = out.get(
            f"pa_breakout_down_{nn}", pd.Series(0, index=out.index, dtype=float)
        ).astype(float)
        rw_atr = out.get(
            f"pa_range_width_atr_{nn}", pd.Series(0.0, index=out.index)
        ).astype(float)

        reff_col = f"range_efficiency_{nn}"
        if reff_col in new_cols:
            reff = new_cols[reff_col].astype(float)
        elif reff_col in out.columns:
            reff = out[reff_col].astype(float)
        else:
            reff = _range_efficiency_session(g, nn, c)
        ts_col = f"trend_score_{nn}"
        if ts_col in new_cols:
            ts = new_cols[ts_col].astype(float)
        elif ts_col in out.columns:
            ts = out[ts_col].astype(float)
        else:
            ts = _trend_score_session(g, nn, c, atr)

        new_cols[f"pa_strong_breakout_score_{nn}"] = np.maximum(
            np.clip(brk_u * (0.5 + 0.5 * cloc) * np.clip(reff, 0.0, 1.0), 0.0, 1.0),
            np.clip(
                brk_d * (0.5 + 0.5 * (1.0 - cloc)) * np.clip(reff, 0.0, 1.0), 0.0, 1.0
            ),
        )

        trend_norm = np.clip(ts / (3.0 + np.abs(ts)), -1.0, 1.0)
        narrow = np.clip(1.0 - rw_atr / (float(nn) + 1e-12), 0.0, 1.0)
        new_cols[f"pa_tight_bull_channel_score_{nn}"] = np.clip(
            (0.5 + 0.5 * trend_norm) * narrow * np.clip(reff, 0.0, 1.0), 0.0, 1.0
        )
        new_cols[f"pa_tight_bear_channel_score_{nn}"] = np.clip(
            (0.5 - 0.5 * trend_norm) * narrow * np.clip(reff, 0.0, 1.0), 0.0, 1.0
        )

        brng = out["bar_range"].astype(float)
        mbr = g["bar_range"].transform(
            lambda s, w=nn: s.shift(1).rolling(w, min_periods=1).mean()
        )
        new_cols[f"pa_bar_range_expansion_{nn}"] = brng / (mbr.astype(float) + 1e-12)

        broad = np.clip(rw_atr / (2.0 + 0.05 * float(nn)), 0.0, 1.0)
        wide_pen = 1.0 - narrow * 0.65
        new_cols[f"pa_broad_bull_channel_score_{nn}"] = np.clip(
            (0.5 + 0.5 * trend_norm) * broad * wide_pen * np.clip(reff, 0.0, 1.0),
            0.0,
            1.0,
        )
        new_cols[f"pa_broad_bear_channel_score_{nn}"] = np.clip(
            (0.5 - 0.5 * trend_norm) * broad * wide_pen * np.clip(reff, 0.0, 1.0),
            0.0,
            1.0,
        )

        new_cols[f"pa_trading_range_score_{nn}"] = np.clip(
            (1.0 - np.abs(ts) / (4.0 + np.abs(ts)))
            * (0.5 + 0.5 * (1.0 - np.clip(reff, 0.0, 1.0))),
            0.0,
            1.0,
        )

        new_cols[f"pa_climax_score_{nn}"] = np.clip(
            body_pct * (1.0 + brk_u + brk_d), 0.0, 1.0
        )
        ov_roll = overlap_b.groupby(sd).transform(
            lambda s, ww=nn: s.rolling(ww, min_periods=1).mean()
        )
        new_cols[f"pa_overlap_score_{nn}"] = np.clip(ov_roll, 0.0, 1.0)

        prev_bull = bull_b.groupby(sd).shift(1).fillna(0.0)
        prev_bear = bear_b.groupby(sd).shift(1).fillna(0.0)
        prev_c1 = g["close"].shift(1)
        new_cols[f"pa_followthrough_up_{nn}"] = (
            (bull_b > 0.5) & (prev_bull > 0.5) & (c > prev_c1.fillna(c))
        ).astype(np.int8)
        new_cols[f"pa_followthrough_down_{nn}"] = (
            (bear_b > 0.5) & (prev_bear > 0.5) & (c < prev_c1.fillna(c))
        ).astype(np.int8)

        ts_arr = ts.to_numpy(dtype=float)
        reff_arr = reff.to_numpy(dtype=float)
        brk_arr = new_cols[f"pa_strong_breakout_score_{nn}"].to_numpy(dtype=float)
        tb_arr = new_cols[f"pa_tight_bull_channel_score_{nn}"].to_numpy(dtype=float)
        te_arr = new_cols[f"pa_tight_bear_channel_score_{nn}"].to_numpy(dtype=float)
        bb_arr = new_cols[f"pa_broad_bull_channel_score_{nn}"].to_numpy(dtype=float)
        be_arr = new_cols[f"pa_broad_bear_channel_score_{nn}"].to_numpy(dtype=float)
        tr_arr = new_cols[f"pa_trading_range_score_{nn}"].to_numpy(dtype=float)
        clx_arr = new_cols[f"pa_climax_score_{nn}"].to_numpy(dtype=float)
        ov_arr = new_cols[f"pa_overlap_score_{nn}"].to_numpy(dtype=float)

        always = np.where(
            (ts_arr > 1.0) & (bb_arr > 0.35),
            PA_ALWAYS_IN_LONG,
            np.where(
                (ts_arr < -1.0) & (be_arr > 0.35),
                PA_ALWAYS_IN_SHORT,
                PA_ALWAYS_IN_NEUTRAL,
            ),
        ).astype(np.int8)
        new_cols[f"pa_always_in_side_{nn}"] = pd.Series(
            always, index=out.index, dtype=np.int8
        )

        lab = np.full(len(out), PA_REGIME_UNKNOWN, dtype=np.int16)
        lab = np.where(
            (brk_arr >= 0.55) & (ts_arr > 0.15),
            PA_REGIME_STRONG_BULL_BREAKOUT,
            lab,
        )
        lab = np.where(
            (brk_arr >= 0.55) & (ts_arr < -0.15),
            PA_REGIME_STRONG_BEAR_BREAKOUT,
            lab,
        )
        lab = np.where(
            (tb_arr >= te_arr)
            & (tb_arr >= bb_arr * 0.85)
            & (tb_arr >= tr_arr)
            & (tb_arr >= 0.38),
            PA_REGIME_TIGHT_BULL_CHANNEL,
            lab,
        )
        lab = np.where(
            (te_arr > tb_arr)
            & (te_arr >= be_arr * 0.85)
            & (te_arr >= tr_arr)
            & (te_arr >= 0.38),
            PA_REGIME_TIGHT_BEAR_CHANNEL,
            lab,
        )
        lab = np.where(
            (bb_arr > be_arr + 0.08) & (bb_arr >= tr_arr) & (bb_arr >= 0.35),
            PA_REGIME_BROAD_BULL_CHANNEL,
            lab,
        )
        lab = np.where(
            (be_arr > bb_arr + 0.08) & (be_arr >= tr_arr) & (be_arr >= 0.35),
            PA_REGIME_BROAD_BEAR_CHANNEL,
            lab,
        )
        lab = np.where(
            (tr_arr > 0.48) & (np.abs(ts_arr) < 0.75),
            PA_REGIME_TRADING_RANGE,
            lab,
        )
        climax_pick = clx_arr * (1.0 - np.clip(reff_arr, 0.0, 1.0)) * (
            np.abs(ts_arr) + 0.25
        )
        lab = np.where(
            (climax_pick > 0.42) & (np.abs(ts_arr) > 0.45),
            PA_REGIME_LATE_TREND_CLIMAX,
            lab,
        )
        new_cols[f"pa_regime_label_{nn}"] = pd.Series(lab, index=out.index, dtype=np.int16)

        tm = np.full(len(out), PA_TRADE_MODE_NEUTRAL, dtype=np.int8)
        tm = np.where(
            (tr_arr > 0.52) & (np.abs(ts_arr) < 0.7),
            PA_TRADE_MODE_RANGE,
            tm,
        )
        tm = np.where((clx_arr > 0.55) & (reff_arr < 0.55), PA_TRADE_MODE_CLIMAX, tm)
        tm = np.where((ts_arr > 0.85) & (tr_arr < 0.45), PA_TRADE_MODE_TREND_LONG, tm)
        tm = np.where((ts_arr < -0.85) & (tr_arr < 0.45), PA_TRADE_MODE_TREND_SHORT, tm)
        new_cols[f"pa_trade_mode_{nn}"] = pd.Series(tm, index=out.index, dtype=np.int8)

        late = np.clip(
            out["body_pct"].astype(float).to_numpy(dtype=float)
            * (np.abs(ts_arr) / (4.0 + np.abs(ts_arr))),
            0.0,
            1.0,
        )
        new_cols[f"pa_late_trend_score_{nn}"] = pd.Series(
            late, index=out.index, dtype=float
        )
        trans = np.clip(
            (np.abs(ts_arr) / (3.0 + np.abs(ts_arr)))
            * (1.0 - np.clip(reff_arr, 0.0, 1.0))
            * np.clip(tr_arr, 0.0, 1.0),
            0.0,
            1.0,
        )
        new_cols[f"pa_trend_to_tr_transition_score_{nn}"] = pd.Series(
            trans, index=out.index, dtype=float
        )
        lim_mkt = np.clip(
            ov_arr * (1.0 - np.minimum(np.abs(ts_arr) / 4.0, 1.0)),
            0.0,
            1.0,
        )
        new_cols[f"pa_limit_order_market_score_{nn}"] = pd.Series(
            lim_mkt, index=out.index, dtype=float
        )

    new_cols["pa_distance_from_vwap_atr"] = (c - out["vwap"].astype(float)) / (
        atr + 1e-12
    )

    if new_cols:
        out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
