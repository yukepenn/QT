"""Session-scoped technical indicators (no cross-session leakage)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import IndicatorsFeatureConfig
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def indicator_column_names(spec: IndicatorsFeatureConfig) -> list[str]:
    cols: list[str] = []
    for w in spec.ema_windows:
        cols.extend([f"ema_{w}", f"ema_slope_{w}"])
    for w in spec.sma_windows:
        cols.extend([f"sma_{w}", f"sma_slope_{w}"])
    for w in spec.rsi_windows:
        cols.extend([f"rsi_{w}", f"rsi_slope_{w}"])
    for fast, slow, sig in spec.macd_tuples:
        cols.extend(
            [
                f"macd_line_{fast}_{slow}",
                f"macd_signal_{fast}_{slow}_{sig}",
                f"macd_hist_{fast}_{slow}_{sig}",
                f"macd_hist_slope_{fast}_{slow}_{sig}",
                f"macd_cross_up_{fast}_{slow}_{sig}",
            ]
        )
    for k_w, d_s in spec.stochastic_tuples:
        cols.extend(
            [
                f"stoch_k_{k_w}",
                f"stoch_d_{k_w}_{d_s}",
                f"stoch_cross_up_{k_w}_{d_s}",
            ]
        )
    for w in spec.cci_windows:
        cols.extend([f"cci_{w}", f"cci_slope_{w}"])
    for w in spec.adx_windows:
        cols.extend(
            [
                f"plus_di_{w}",
                f"minus_di_{w}",
                f"adx_{w}",
                f"adx_slope_{w}",
            ]
        )
    return cols


def _rsi_wilder(close: pd.Series, window: int, grouper: pd.Series) -> pd.Series:
    def _one(s: pd.Series, ww: int) -> pd.Series:
        d = s.diff()
        gain = d.clip(lower=0.0)
        loss = (-d).clip(lower=0.0)
        ag = gain.ewm(alpha=1.0 / ww, adjust=False, min_periods=ww).mean()
        al = loss.ewm(alpha=1.0 / ww, adjust=False, min_periods=ww).mean()
        rs = ag / (al + 1e-12)
        return 100.0 - (100.0 / (1.0 + rs))

    return close.groupby(grouper, sort=False).transform(lambda s, ww=window: _one(s, ww))


def _wilder_smooth_series(s: pd.Series, length: int, grouper: pd.Series) -> pd.Series:
    return s.groupby(grouper, sort=False).transform(
        lambda x, n=length: x.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    )


def add_indicator_features(
    df: pd.DataFrame,
    spec: IndicatorsFeatureConfig,
    *,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    cols = indicator_column_names(spec)
    if not cols:
        return safe_copy(df, copy)

    module_name = "indicators"
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)
    ensure_columns(df, ["session_date", "open", "high", "low", "close"], context="indicators")

    out = safe_copy(df, copy)
    sd = out["session_date"]
    g = out.groupby(sd, sort=False)
    c = out["close"].astype(float)
    h = out["high"].astype(float)
    lo = out["low"].astype(float)

    new_cols: dict[str, pd.Series] = {}

    for w in spec.ema_windows:
        ema = g["close"].transform(lambda s, sp=w: s.ewm(span=sp, adjust=False, min_periods=1).mean())
        new_cols[f"ema_{w}"] = ema
        new_cols[f"ema_slope_{w}"] = ema.groupby(sd).transform(lambda s: s - s.shift(1))

    for w in spec.sma_windows:
        sma = g["close"].transform(lambda s, ww=w: s.rolling(ww, min_periods=1).mean())
        new_cols[f"sma_{w}"] = sma
        new_cols[f"sma_slope_{w}"] = sma.groupby(sd).transform(lambda s: s - s.shift(1))

    for w in spec.rsi_windows:
        rsi = _rsi_wilder(c, w, sd)
        new_cols[f"rsi_{w}"] = rsi
        new_cols[f"rsi_slope_{w}"] = rsi.groupby(sd).transform(lambda s: s - s.shift(1))

    for fast, slow, sig in spec.macd_tuples:
        ema_f = g["close"].transform(lambda s, sp=fast: s.ewm(span=sp, adjust=False, min_periods=1).mean())
        ema_s = g["close"].transform(lambda s, sp=slow: s.ewm(span=sp, adjust=False, min_periods=1).mean())
        line = ema_f - ema_s
        ln = f"macd_line_{fast}_{slow}"
        new_cols[ln] = line
        sig_line = line.groupby(sd).transform(
            lambda s, sp=sig: s.ewm(span=sp, adjust=False, min_periods=1).mean()
        )
        new_cols[f"macd_signal_{fast}_{slow}_{sig}"] = sig_line
        hist = line - sig_line
        hn = f"macd_hist_{fast}_{slow}_{sig}"
        new_cols[hn] = hist
        new_cols[f"macd_hist_slope_{fast}_{slow}_{sig}"] = hist.groupby(sd).transform(lambda s: s - s.shift(1))
        prev = hist.groupby(sd).transform(lambda s: s.shift(1))
        new_cols[f"macd_cross_up_{fast}_{slow}_{sig}"] = ((hist > 0) & (prev <= 0)).astype(np.int8)

    for k_w, d_s in spec.stochastic_tuples:
        roll_lo = g["low"].transform(lambda s, kw=k_w: s.rolling(kw, min_periods=1).min())
        roll_hi = g["high"].transform(lambda s, kw=k_w: s.rolling(kw, min_periods=1).max())
        rng = (roll_hi - roll_lo).replace(0, np.nan)
        k = 100.0 * (c - roll_lo) / (rng + 1e-12)
        new_cols[f"stoch_k_{k_w}"] = k
        d = k.groupby(sd).transform(lambda s, ds=d_s: s.rolling(ds, min_periods=1).mean())
        new_cols[f"stoch_d_{k_w}_{d_s}"] = d
        prev_k = k.groupby(sd).transform(lambda s: s.shift(1))
        prev_d = d.groupby(sd).transform(lambda s: s.shift(1))
        new_cols[f"stoch_cross_up_{k_w}_{d_s}"] = ((k > d) & (prev_k <= prev_d)).astype(np.int8)

    for w in spec.cci_windows:
        tp = (h + lo + c) / 3.0
        ma_tp = tp.groupby(sd).transform(lambda s, ww=w: s.rolling(ww, min_periods=1).mean())
        md = tp.groupby(sd).transform(
            lambda s, ww=w: (s - s.rolling(ww, min_periods=1).mean())
            .abs()
            .rolling(ww, min_periods=1)
            .mean()
        )
        cci = (tp - ma_tp) / (0.015 * md.replace(0, np.nan) + 1e-12)
        new_cols[f"cci_{w}"] = cci
        new_cols[f"cci_slope_{w}"] = cci.groupby(sd).transform(lambda s: s - s.shift(1))

    for w in spec.adx_windows:
        prev_c = g["close"].transform(lambda s: s.shift(1))
        tr = pd.concat([h - lo, (h - prev_c).abs(), (lo - prev_c).abs()], axis=1).max(axis=1)
        up_move = g["high"].transform(lambda s: s - s.shift(1))
        down_move = g["low"].transform(lambda s: s.shift(1) - s)
        plus_dm = np.where((up_move > down_move) & (up_move > 0.0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0.0), down_move, 0.0)
        pdm = pd.Series(plus_dm, index=out.index, dtype=float)
        mdm = pd.Series(minus_dm, index=out.index, dtype=float)
        atr_tr = _wilder_smooth_series(tr, w, sd)
        p_dm_s = _wilder_smooth_series(pdm, w, sd)
        m_dm_s = _wilder_smooth_series(mdm, w, sd)
        plus_di = 100.0 * (p_dm_s / (atr_tr + 1e-12))
        minus_di = 100.0 * (m_dm_s / (atr_tr + 1e-12))
        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-12)
        adx = _wilder_smooth_series(dx, w, sd)
        new_cols[f"plus_di_{w}"] = plus_di
        new_cols[f"minus_di_{w}"] = minus_di
        new_cols[f"adx_{w}"] = adx
        new_cols[f"adx_slope_{w}"] = adx.groupby(sd).transform(lambda s: s - s.shift(1))

    if new_cols:
        out = pd.concat([out, pd.DataFrame(new_cols)], axis=1)
    return out
