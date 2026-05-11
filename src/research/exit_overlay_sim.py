"""
Offline exit-overlay path simulation for Champion v0 trades (research-only).

- Entries, stops, and initial risk are taken from the local trade-context panel.
- Only post-entry bar paths (1-minute OHLC) influence overlay exits.
- Intrabar stop vs target ambiguity defaults to conservative ``stop_first``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import numpy as np
import pandas as pd

NY_TZ = "America/New_York"
EOD_EXIT_MINUTE = 389  # aligned with local replay combiner materialization


class AmbiguityPolicy(str, Enum):
    stop_first = "stop_first"
    target_first = "target_first"
    skip_ambiguous = "skip_ambiguous"


def ny_session_open(session_date: str) -> pd.Timestamp:
    d = pd.Timestamp(str(session_date)).tz_localize(NY_TZ)
    return d + pd.Timedelta(hours=9, minutes=30)


def minute_from_open(ts_ny: pd.Timestamp) -> int:
    if ts_ny.tzinfo is None:
        ts_ny = ts_ny.tz_localize(NY_TZ)
    else:
        ts_ny = ts_ny.tz_convert(NY_TZ)
    sess = ts_ny.normalize() + pd.Timedelta(hours=9, minutes=30)
    return int((ts_ny - sess) / pd.Timedelta(minutes=1))


def add_session_date_column(bars: pd.DataFrame) -> pd.DataFrame:
    out = bars.copy()
    if "ts_ny" not in out.columns:
        out["ts_ny"] = pd.to_datetime(out["ts_utc"], utc=True).dt.tz_convert(NY_TZ)
    out["session_date"] = out["ts_ny"].dt.strftime("%Y-%m-%d")
    return out


def causal_vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    typ = (high + low + close) / 3.0
    vol = np.maximum(volume.astype(float), 1.0)
    cum_num = np.cumsum(typ * vol)
    cum_den = np.cumsum(vol)
    return cum_num / cum_den


def causal_atr14(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    n = len(close)
    tr = np.zeros(n, dtype=float)
    for i in range(n):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    out = np.zeros(n, dtype=float)
    alpha = 1.0 / 14.0
    for i in range(n):
        if i == 0:
            out[i] = tr[i]
        else:
            out[i] = (1 - alpha) * out[i - 1] + alpha * tr[i]
    return out


def trend_swing_eligible(row: pd.Series) -> bool:
    ctx = str(row.get("context_bucket", "") or "")
    lab = str(row.get("decision_pa_always_in_side_20_label", "") or "")
    return ctx == "trend_long" or lab == "always_in_long"


def _decision_truthy(row: pd.Series, *keys: str) -> bool:
    for k in keys:
        if k not in row.index:
            continue
        v = row[k]
        if pd.isna(v):
            continue
        if isinstance(v, (bool, np.bool_)):
            if bool(v):
                return True
            continue
        s = str(v).strip().lower()
        if s in ("true", "1", "t", "yes"):
            return True
        try:
            if float(v) != 0.0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def trend_swing_2R_contextual_eligible(row: pd.Series) -> bool:
    if str(row.get("context_bucket", "") or "") == "late_climax":
        return False
    if not trend_swing_eligible(row):
        return False
    return _decision_truthy(row, "decision_close_above_vwap", "close_above_vwap")


def runner_contextual_eligible(row: pd.Series) -> bool:
    if str(row.get("context_bucket", "") or "") == "late_climax":
        return False
    if str(row.get("market_context_label", "") or "") == "range_chop":
        return False
    ctx = str(row.get("context_bucket", "") or "")
    lab = str(row.get("decision_pa_always_in_side_20_label", "") or "")
    return ctx == "trend_long" or lab == "always_in_long"


def no_followthrough_5bars_contextual_eligible(row: pd.Series) -> bool:
    cid = str(row.get("candidate_id", "") or "")
    if "GAP" in cid.upper():
        return True
    if str(row.get("context_bucket", "") or "") in ("trading_range", "late_climax"):
        return True
    m = str(row.get("market_context_label", "") or "")
    return "downtrend" in m


def _side_is_long(side: Any) -> bool:
    s = str(side).lower()
    if s in ("long", "1", "true"):
        return True
    try:
        return int(float(side)) == 1
    except (TypeError, ValueError):
        return False


def _intrabar_resolution(
    *,
    low: float,
    high: float,
    stop: float,
    target: float,
    policy: AmbiguityPolicy,
) -> tuple[Literal["stop", "target", "neither", "ambiguous_skip"], bool]:
    hit_stop = low <= stop
    hit_tgt = high >= target
    ambiguous = hit_stop and hit_tgt
    if ambiguous:
        if policy == AmbiguityPolicy.stop_first:
            return "stop", True
        if policy == AmbiguityPolicy.target_first:
            return "target", True
        return "ambiguous_skip", True
    if hit_stop:
        return "stop", False
    if hit_tgt:
        return "target", False
    return "neither", False


@dataclass
class SimResult:
    r_multiple: float
    exit_price: float
    exit_reason: str
    bars_held: int
    ambiguous_bar: bool
    changed_exit_vs_replay: bool


def simulate_long_overlay(
    *,
    session_bars: pd.DataFrame,
    entry_ts_utc: pd.Timestamp,
    entry_price: float,
    stop_price: float,
    target_price: float,
    risk_per_share: float,
    overlay_id: str,
    ambiguity: AmbiguityPolicy,
    row: pd.Series | None = None,
) -> SimResult:
    """
    Walk 1-minute bars from the entry bar forward until exit.

    ``session_bars`` must be sorted by ``ts_utc`` and cover the full session from open.
    """
    if not len(session_bars):
        return SimResult(0.0, float(entry_price), "no_bars", 0, False, False)

    ts = pd.to_datetime(session_bars["ts_utc"], utc=True)
    entry_ts = pd.Timestamp(entry_ts_utc)
    if entry_ts.tzinfo is None:
        entry_ts = entry_ts.tz_localize("UTC")
    else:
        entry_ts = entry_ts.tz_convert("UTC")

    pos = int(ts.searchsorted(entry_ts, side="left"))
    if pos >= len(session_bars):
        return SimResult(0.0, float(entry_price), "entry_not_found", 0, False, False)

    o = session_bars["open"].to_numpy(float)
    h = session_bars["high"].to_numpy(float)
    l = session_bars["low"].to_numpy(float)
    c = session_bars["close"].to_numpy(float)
    v = session_bars["volume"].to_numpy(float)

    vwap = causal_vwap(h, l, c, v)
    atr = causal_atr14(h, l, c)

    risk = float(risk_per_share)
    if risk <= 0 or not math.isfinite(risk):
        return SimResult(0.0, float(entry_price), "bad_risk", 0, False, False)

    entry = float(entry_price)
    stop = float(stop_price)
    target = float(target_price)

    # --- fixed replay (no overlay) uses row targets ---
    def fixed_walk(tgt: float, mx_hold: int | None) -> SimResult:
        amb = False
        peak = entry
        end_j = min(len(session_bars), pos + (mx_hold if mx_hold is not None else 10_000))
        for j in range(pos, end_j):
            bar = j - pos + 1
            ts_j = ts.iloc[j]
            ts_nyj = ts_j.tz_convert(NY_TZ) if ts_j.tzinfo else ts_j
            mfo = minute_from_open(pd.Timestamp(ts_nyj))
            if mfo >= EOD_EXIT_MINUTE:
                px = float(c[j])
                r = (px - entry) / risk
                return SimResult(r, px, "eod_exit", bar, amb, False)
            lo, hi = float(l[j]), float(h[j])
            res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop, target=tgt, policy=ambiguity)
            if is_amb:
                amb = True
            if res == "stop":
                return SimResult((stop - entry) / risk, stop, "stop", bar, amb, False)
            if res == "target":
                return SimResult((tgt - entry) / risk, tgt, "target", bar, amb, False)
            peak = max(peak, hi)
        last = end_j - 1 if end_j > pos else pos
        px = float(c[last])
        r = (px - entry) / risk
        return SimResult(r, px, "session_end", last - pos + 1, amb, False)

    replay = fixed_walk(target, None)

    oid = overlay_id
    if oid == "trend_swing_2R_contextual":
        if row is None or not trend_swing_2R_contextual_eligible(row):
            return replay
        oid = "trend_swing_2R"
    elif oid == "runner_after_1R_trail_vwap_contextual":
        if row is None or not runner_contextual_eligible(row):
            return replay
        oid = "runner_after_1R_trail_vwap"
    elif oid == "runner_after_1R_trail_atr_contextual":
        if row is None or not runner_contextual_eligible(row):
            return replay
        oid = "runner_after_1R_trail_atr"
    elif oid == "no_followthrough_exit_5bars_contextual":
        if row is None or not no_followthrough_5bars_contextual_eligible(row):
            return replay
        oid = "no_followthrough_exit_5bars"

    if overlay_id == "baseline_original":
        if row is None:
            return replay
        orig_r = float(pd.to_numeric(row.get("r_multiple"), errors="coerce"))
        return SimResult(
            orig_r,
            float(row.get("exit_price", replay.exit_price)),
            str(row.get("exit_reason", "original")),
            int(pd.to_numeric(row.get("bars_held"), errors="coerce") or replay.bars_held),
            False,
            False,
        )

    if overlay_id == "fixed_target_replay":
        return replay

    if oid in ("trend_swing_1p5R", "trend_swing_2R"):
        if row is None or not trend_swing_eligible(row):
            return replay
        mult = 1.5 if oid == "trend_swing_1p5R" else 2.0
        tgt2 = entry + mult * risk
        return fixed_walk(tgt2, None)

    if oid == "runner_after_1R_trail_vwap":
        active = False
        trail = stop
        amb = False
        peak = entry
        for j in range(pos, len(session_bars)):
            bar = j - pos + 1
            ts_j = ts.iloc[j]
            ts_nyj = ts_j.tz_convert(NY_TZ)
            if minute_from_open(pd.Timestamp(ts_nyj)) >= EOD_EXIT_MINUTE:
                px = float(c[j])
                return SimResult((px - entry) / risk, px, "eod_exit", bar, amb, True)
            lo, hi = float(l[j]), float(h[j])
            peak = max(peak, hi)
            if not active and peak >= entry + risk:
                active = True
            if active:
                vw = float(vwap[j])
                at = float(atr[j]) if math.isfinite(atr[j]) else risk
                trail = max(trail, vw - 0.25 * max(at, 1e-6))
                trail = max(trail, stop)
                res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=trail, target=1e9, policy=AmbiguityPolicy.stop_first)
                if is_amb:
                    amb = True
                if res == "stop":
                    return SimResult((trail - entry) / risk, trail, "trail_stop", bar, amb, True)
            else:
                res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop, target=target, policy=ambiguity)
                if is_amb:
                    amb = True
                if res == "stop":
                    return SimResult((stop - entry) / risk, stop, "stop", bar, amb, True)
                if res == "target":
                    return SimResult((target - entry) / risk, target, "target", bar, amb, True)
        px = float(c[-1])
        return SimResult((px - entry) / risk, px, "session_end", len(session_bars) - pos, amb, True)

    if oid == "runner_after_1R_trail_atr":
        active = False
        trail = stop
        amb = False
        peak = entry
        for j in range(pos, len(session_bars)):
            bar = j - pos + 1
            ts_j = ts.iloc[j]
            ts_nyj = ts_j.tz_convert(NY_TZ)
            if minute_from_open(pd.Timestamp(ts_nyj)) >= EOD_EXIT_MINUTE:
                px = float(c[j])
                return SimResult((px - entry) / risk, px, "eod_exit", bar, amb, True)
            lo, hi = float(l[j]), float(h[j])
            peak = max(peak, hi)
            if not active and peak >= entry + risk:
                active = True
            if active:
                at = float(atr[j]) if math.isfinite(atr[j]) else risk
                trail = max(trail, peak - 1.0 * max(at, risk))
                trail = max(trail, stop)
                res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=trail, target=1e9, policy=AmbiguityPolicy.stop_first)
                if is_amb:
                    amb = True
                if res == "stop":
                    return SimResult((trail - entry) / risk, trail, "trail_stop", bar, amb, True)
            else:
                res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop, target=target, policy=ambiguity)
                if is_amb:
                    amb = True
                if res == "stop":
                    return SimResult((stop - entry) / risk, stop, "stop", bar, amb, True)
                if res == "target":
                    return SimResult((target - entry) / risk, target, "target", bar, amb, True)
        px = float(c[-1])
        return SimResult((px - entry) / risk, px, "session_end", len(session_bars) - pos, amb, True)

    if oid in ("no_followthrough_exit_3bars", "no_followthrough_exit_5bars"):
        n_ft = 3 if "3bars" in oid else 5
        thr = 0.15 * risk
        for j in range(pos, len(session_bars)):
            bar = j - pos + 1
            ts_j = ts.iloc[j]
            ts_nyj = ts_j.tz_convert(NY_TZ)
            if minute_from_open(pd.Timestamp(ts_nyj)) >= EOD_EXIT_MINUTE:
                px = float(c[j])
                return SimResult((px - entry) / risk, px, "eod_exit", bar, False, True)
            lo, hi = float(l[j]), float(h[j])
            res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop, target=target, policy=ambiguity)
            if is_amb:
                pass
            if res == "stop":
                return SimResult((stop - entry) / risk, stop, "stop", bar, is_amb, True)
            if res == "target":
                return SimResult((target - entry) / risk, target, "target", bar, is_amb, True)
            if bar == n_ft:
                mfe = float(np.max(h[pos : j + 1]) - entry)
                if mfe < thr:
                    px = float(c[j])
                    return SimResult((px - entry) / risk, px, "no_followthrough", bar, False, True)
        px = float(c[min(len(session_bars) - 1, pos + 500)])
        return SimResult((px - entry) / risk, px, "session_end", len(session_bars) - pos, False, True)

    if oid in ("max_hold_tighten_30", "max_hold_tighten_60"):
        cap = 30 if "30" in oid else 60
        amb = False
        for j in range(pos, len(session_bars)):
            bar = j - pos + 1
            ts_j = ts.iloc[j]
            ts_nyj = ts_j.tz_convert(NY_TZ)
            if minute_from_open(pd.Timestamp(ts_nyj)) >= EOD_EXIT_MINUTE:
                px = float(c[j])
                return SimResult((px - entry) / risk, px, "eod_exit", bar, amb, True)
            lo, hi = float(l[j]), float(h[j])
            res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop, target=target, policy=ambiguity)
            if is_amb:
                amb = True
            if res == "stop":
                return SimResult((stop - entry) / risk, stop, "stop", bar, amb, True)
            if res == "target":
                return SimResult((target - entry) / risk, target, "target", bar, amb, True)
            if bar >= cap:
                px = float(c[j])
                return SimResult((px - entry) / risk, px, "max_hold_tighten", bar, amb, True)
        px = float(c[-1])
        return SimResult((px - entry) / risk, px, "session_end", len(session_bars) - pos, amb, True)

    return replay


def simulate_row(
    *,
    session_bars: pd.DataFrame,
    row: pd.Series,
    overlay_id: str,
    ambiguity: AmbiguityPolicy,
    clone_replay_cfg: Any | None = None,
) -> SimResult:
    if not _side_is_long(row.get("side", "long")):
        return SimResult(0.0, float(row.get("entry_price", 0.0)), "not_long_skipped", 0, False, False)
    if overlay_id == "combiner_clone_replay":
        if clone_replay_cfg is None:
            raise ValueError("combiner_clone_replay requires clone_replay_cfg=CloneReplayConfig(...)")
        from src.research.exit_overlay_alignment import combiner_clone_long_walk

        return combiner_clone_long_walk(session_bars=session_bars, row=row, cfg=clone_replay_cfg)
    return simulate_long_overlay(
        session_bars=session_bars,
        entry_ts_utc=pd.Timestamp(row["entry_ts_utc"]),
        entry_price=float(row["entry_price"]),
        stop_price=float(row["stop_price"]),
        target_price=float(row["target_price"]),
        risk_per_share=float(row["risk_per_share"]),
        overlay_id=overlay_id,
        ambiguity=ambiguity,
        row=row,
    )


def label_overlay_row(
    *,
    retention_pct: float,
    delta_total_r: float,
    delta_pf: float | None,
    delta_dd: float | None,
    amb_pct: float,
    weak_delta: float | None,
    late_oow_delta_pf: float | None = None,
    insample_delta_pf: float | None = None,
) -> str:
    """Coarse aggregate label for exit-overlay rows (diagnostic, not production)."""
    if amb_pct > 0.08:
        return "EXIT_OVERLAY_DATA_QUALITY_LIMITED"
    if retention_pct < 0.95 and delta_total_r < -50:
        return "EXIT_OVERLAY_TOO_AGGRESSIVE"
    if delta_pf is None or (abs(delta_pf) < 0.01 and (delta_dd is None or abs(delta_dd or 0) < 0.5)):
        return "EXIT_OVERLAY_NO_IMPROVEMENT"
    improved = (delta_pf is not None and delta_pf > 0.02) or (delta_dd is not None and delta_dd > 2.0)
    if not improved:
        return "EXIT_OVERLAY_NO_IMPROVEMENT"
    if weak_delta is not None and weak_delta < -25:
        return "EXIT_OVERLAY_REJECT"
    if delta_total_r < -30:
        return "EXIT_OVERLAY_TOO_AGGRESSIVE"
    if late_oow_delta_pf is not None and late_oow_delta_pf < -0.02 and (insample_delta_pf or 0) > 0.02:
        return "EXIT_OVERLAY_CONTEXT_SPECIFIC"
    return "EXIT_OVERLAY_PROMISING"
