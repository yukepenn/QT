"""NumPy/Numba helpers for strategy fast signal generation (not execution — see backtest/fast.py)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.constants import TM_FIXED_PX, TM_FIXED_R, TM_NONE


def session_id_from_dates(session_date: pd.Series) -> np.ndarray:
    codes, _ = pd.factorize(session_date, sort=False)
    return codes.astype(np.int32)


@njit(cache=True)
def prev_by_session(values: np.ndarray, session_id: np.ndarray) -> np.ndarray:
    n = len(values)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        if i == 0 or session_id[i] != session_id[i - 1]:
            out[i] = np.nan
        else:
            out[i] = values[i - 1]
    return out


@njit(cache=True)
def rolling_min_by_session(values: np.ndarray, session_id: np.ndarray, lookback: int) -> np.ndarray:
    n = len(values)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        sid = session_id[i]
        mn = values[i]
        cnt = 0
        for j in range(i, -1, -1):
            if session_id[j] != sid:
                break
            v = values[j]
            if v < mn:
                mn = v
            cnt += 1
            if cnt >= lookback:
                break
        out[i] = mn
    return out


@njit(cache=True)
def rolling_max_by_session(values: np.ndarray, session_id: np.ndarray, lookback: int) -> np.ndarray:
    n = len(values)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        sid = session_id[i]
        mx = values[i]
        cnt = 0
        for j in range(i, -1, -1):
            if session_id[j] != sid:
                break
            v = values[j]
            if v > mx:
                mx = v
            cnt += 1
            if cnt >= lookback:
                break
        out[i] = mx
    return out


@njit(cache=True)
def thin_first_signal_per_session_numba(
    cand_long: np.ndarray,
    cand_short: np.ndarray,
    session_id: np.ndarray,
    max_trades_per_day: int,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(session_id)
    final_long = np.zeros(n, dtype=np.bool_)
    final_short = np.zeros(n, dtype=np.bool_)
    cur_sid = session_id[0] - 1
    taken = 0
    for i in range(n):
        sid = session_id[i]
        if sid != cur_sid:
            cur_sid = sid
            taken = 0
        if taken >= max_trades_per_day:
            continue
        cl = cand_long[i]
        cs = cand_short[i]
        if cl and cs:
            final_long[i] = True
            taken += 1
        elif cl:
            final_long[i] = True
            taken += 1
        elif cs:
            final_short[i] = True
            taken += 1
    return final_long, final_short


@njit(cache=True)
def thin_per_side_per_session_numba(
    cand_long: np.ndarray,
    cand_short: np.ndarray,
    session_id: np.ndarray,
    max_trades_per_day: int,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(session_id)
    final_long = np.zeros(n, dtype=np.bool_)
    final_short = np.zeros(n, dtype=np.bool_)
    cur_sid = session_id[0] - 1
    long_taken = 0
    short_taken = 0
    for i in range(n):
        sid = session_id[i]
        if sid != cur_sid:
            cur_sid = sid
            long_taken = 0
            short_taken = 0
        if cand_long[i] and long_taken < max_trades_per_day:
            final_long[i] = True
            long_taken += 1
        if cand_short[i] and short_taken < max_trades_per_day:
            final_short[i] = True
            short_taken += 1
    return final_long, final_short


def get_min_risk_per_share(config: dict) -> float:
    risk = config.get("risk") or {}
    v = risk.get("min_risk_per_share")
    if v is None or v == 0:
        return 0.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return f if f > 0 else 0.0


def apply_min_risk_filter_arrays(
    valid: np.ndarray,
    side: np.ndarray,
    risk: np.ndarray,
    min_risk: float,
) -> tuple[np.ndarray, np.ndarray]:
    if min_risk <= 0:
        return valid, side
    m = valid & (risk >= min_risk)
    out_s = side.copy()
    out_s[~m] = 0
    return m, out_s


def apply_min_risk_filter_df(
    df: pd.DataFrame,
    *,
    risk_col: str = "sig_risk_per_share",
    valid_col: str = "sig_valid",
    side_col: str = "sig_side",
    config: dict | None = None,
) -> pd.DataFrame:
    if config is None:
        return df
    min_r = get_min_risk_per_share(config)
    if min_r <= 0:
        return df
    out = df.copy()
    rs = pd.to_numeric(out[risk_col], errors="coerce")
    ok = rs.fillna(0.0).astype(float) >= min_r
    bad = out[valid_col].fillna(False) & ~ok
    out.loc[bad, valid_col] = False
    out.loc[bad, side_col] = 0
    return out


def pack_signal_arrays_from_df(df: pd.DataFrame) -> dict[str, Any]:
    """Map standard signal columns to fast backtest array dict (preview fields)."""
    side = df["sig_side"].fillna(0).to_numpy(dtype=np.float64).astype(np.int8)
    valid = df["sig_valid"].fillna(False).to_numpy(dtype=bool)
    stp = pd.to_numeric(df["sig_stop"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    tgt = pd.to_numeric(df["sig_target"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    tr = pd.to_numeric(df["sig_target_r"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    risk = pd.to_numeric(df["sig_risk_per_share"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    mode_str = df["sig_target_mode"].fillna("").astype(str).str.strip().str.lower()
    tmc = np.full(len(df), TM_NONE, dtype=np.int8)
    tmc[mode_str == "fixed_r"] = TM_FIXED_R
    tmc[mode_str == "fixed_price"] = TM_FIXED_PX
    return {
        "side": side,
        "valid": valid,
        "stop": stp,
        "target_preview": tgt,
        "target_mode_code": tmc,
        "target_r": tr,
        "risk_preview": risk,
    }


def build_empty_signal_arrays(n: int) -> dict[str, Any]:
    """Standard zero-filled signal arrays (length n)."""
    return {
        "side": np.zeros(n, dtype=np.int8),
        "valid": np.zeros(n, dtype=np.bool_),
        "stop": np.zeros(n, dtype=np.float64),
        "target_preview": np.zeros(n, dtype=np.float64),
        "target_mode_code": np.full(n, TM_NONE, dtype=np.int8),
        "target_r": np.zeros(n, dtype=np.float64),
        "risk_preview": np.zeros(n, dtype=np.float64),
    }


@njit(cache=True)
def past_any_bool_in_prior_fw_session(pred: np.ndarray, session_id: np.ndarray, fw: int) -> np.ndarray:
    """True at i if any pred[j] in previous fw bars of same session (strictly before i)."""
    n = len(pred)
    out = np.zeros(n, dtype=np.bool_)
    for i in range(n):
        sid = session_id[i]
        for k in range(1, fw + 1):
            j = i - k
            if j < 0:
                break
            if session_id[j] != sid:
                break
            if pred[j]:
                out[i] = True
                break
    return out


@njit(cache=True)
def recent_any_bool_in_window_session(pred: np.ndarray, session_id: np.ndarray, window: int) -> np.ndarray:
    """True at i if any pred[j] in the last ``window`` bars of the session ending at i (inclusive)."""
    n = len(pred)
    out = np.zeros(n, dtype=np.bool_)
    for i in range(n):
        sid = session_id[i]
        cnt = 0
        for j in range(i, -1, -1):
            if session_id[j] != sid:
                break
            if pred[j]:
                out[i] = True
            cnt += 1
            if cnt >= window:
                break
    return out


@njit(cache=True)
def rolling_sum_by_session_int(
    values: np.ndarray,
    session_id: np.ndarray,
    window: int,
) -> np.ndarray:
    """Sum of last ``window`` integer/float values within session including current bar."""
    n = len(values)
    out = np.zeros(n, dtype=np.float64)
    for i in range(n):
        sid = session_id[i]
        s = 0.0
        cnt = 0
        for j in range(i, -1, -1):
            if session_id[j] != sid:
                break
            s += float(values[j])
            cnt += 1
            if cnt >= window:
                break
        out[i] = s
    return out


@njit(cache=True)
def rolling_min_by_session_prior_exclusive(
    values: np.ndarray,
    session_id: np.ndarray,
    lookback: int,
) -> np.ndarray:
    """Min of previous ``lookback`` values in session (excludes current index)."""
    n = len(values)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        sid = session_id[i]
        mn = np.inf
        cnt = 0
        for j in range(i - 1, -1, -1):
            if session_id[j] != sid:
                break
            v = values[j]
            if v < mn:
                mn = v
            cnt += 1
            if cnt >= lookback:
                break
        out[i] = mn if cnt > 0 and mn < np.inf else np.nan
    return out


@njit(cache=True)
def rolling_max_by_session_prior_exclusive(
    values: np.ndarray,
    session_id: np.ndarray,
    lookback: int,
) -> np.ndarray:
    """Max of previous ``lookback`` values in session (excludes current index)."""
    n = len(values)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        sid = session_id[i]
        mx = -np.inf
        cnt = 0
        for j in range(i - 1, -1, -1):
            if session_id[j] != sid:
                break
            v = values[j]
            if v > mx:
                mx = v
            cnt += 1
            if cnt >= lookback:
                break
        out[i] = mx if cnt > 0 and mx > -np.inf else np.nan
    return out


@njit(cache=True)
def rolling_max_high_prior_n(high: np.ndarray, session_id: np.ndarray, nbar: int) -> np.ndarray:
    """Max of previous ``nbar`` highs (excludes current bar). Same as pandas rolling(n).max().shift(1)."""
    return rolling_max_by_session_prior_exclusive(high, session_id, nbar)


@njit(cache=True)
def first_value_when_minute_ge(
    values: np.ndarray,
    minute: np.ndarray,
    session_id: np.ndarray,
    target_minute: int,
) -> np.ndarray:
    """Per session, broadcast first ``values[i]`` where ``minute[i] >= target_minute`` to all rows."""
    n = len(values)
    n_sess = int(session_id.max()) + 1 if n else 0
    anchors = np.full(n_sess, np.nan)
    for i in range(n):
        sid = session_id[i]
        if minute[i] >= target_minute and np.isnan(anchors[sid]):
            anchors[sid] = values[i]
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = anchors[session_id[i]]
    return out


@njit(cache=True)
def first_value_when_minute_ge_with_known(
    values: np.ndarray,
    minute: np.ndarray,
    session_id: np.ndarray,
    target_minute: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Per session:
    - `anchor`: broadcast first values[i] where minute[i] >= target_minute
    - `known`: False before target_minute; True at/after target_minute if anchor exists for that session
    """
    n = len(values)
    n_sess = int(session_id.max()) + 1 if n else 0
    anchors = np.full(n_sess, np.nan)
    for i in range(n):
        sid = session_id[i]
        if minute[i] >= target_minute and np.isnan(anchors[sid]):
            anchors[sid] = values[i]
    anchor_out = np.empty(n, dtype=np.float64)
    known_out = np.zeros(n, dtype=np.bool_)
    for i in range(n):
        sid = session_id[i]
        anchor_out[i] = anchors[sid]
        known_out[i] = (minute[i] >= target_minute) and (anchors[sid] == anchors[sid])
    return anchor_out, known_out


@njit(cache=True)
def apply_min_risk_filter_numba_kernel(
    valid: np.ndarray,
    side: np.ndarray,
    risk: np.ndarray,
    min_risk: float,
) -> None:
    """In-place: clear side and valid where risk < min_risk."""
    if min_risk <= 0.0:
        return
    n = len(valid)
    for i in range(n):
        if valid[i] and risk[i] < min_risk:
            valid[i] = False
            side[i] = 0
