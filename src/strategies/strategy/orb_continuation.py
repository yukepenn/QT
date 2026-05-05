"""ORB continuation strategy plugin (standard signal schema)."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from src.backtest.fast import TM_FIXED_R, TM_NONE
from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_arrays,
    apply_min_risk_filter_df,
    get_min_risk_per_share,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
    thin_per_side_per_session_numba,
)


@dataclass(frozen=True)
class ORBContinuationContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    vwap: np.ndarray
    vwap_slope_5: np.ndarray
    orb_high: np.ndarray
    orb_low: np.ndarray
    orb_mid: np.ndarray
    orb_width_pct: np.ndarray
    after_orb: np.ndarray
    above_orb_high: np.ndarray
    below_orb_low: np.ndarray


class ORBContinuationStrategy(BaseStrategy):
    name = "orb_continuation"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "vwap_slope_5",
            "orb_high",
            "orb_low",
            "orb_mid",
            "orb_width_pct",
            "after_orb",
            "above_orb_high",
            "below_orb_low",
        ]

    def generate_signals(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        sig_cfg = config.get("signal") or {}
        risk_cfg = config.get("risk") or {}

        side = str(sig_cfg.get("side", "both"))
        entry_start = int(sig_cfg["entry_start_minute"])
        entry_end = int(sig_cfg["entry_end_minute"])
        require_vwap_side = bool(sig_cfg.get("require_vwap_side", True))
        require_vwap_slope = bool(sig_cfg.get("require_vwap_slope", True))
        min_w = sig_cfg.get("min_orb_width_pct")
        max_w = sig_cfg.get("max_orb_width_pct")
        daily_mode = str(sig_cfg.get("daily_signal_mode", "first_signal"))

        stop_mode = str(risk_cfg.get("stop_mode", "orb_mid"))
        stop_buffer = float(risk_cfg.get("stop_buffer", 0.0))
        target_mode = str(risk_cfg.get("target_mode", "fixed_r"))
        target_r = float(risk_cfg["target_r"])
        max_trades = int(risk_cfg.get("max_trades_per_day", 1))

        if side not in ("long_only", "short_only", "both"):
            raise ValueError(f"side must be long_only, short_only, or both, got {side!r}")
        if daily_mode not in ("first_signal", "per_side"):
            raise ValueError(f"daily_signal_mode must be first_signal or per_side, got {daily_mode!r}")
        if stop_mode not in ("orb_mid", "orb_opposite"):
            raise ValueError(f"stop_mode must be orb_mid or orb_opposite, got {stop_mode!r}")
        if stop_buffer < 0:
            raise ValueError("stop_buffer must be >= 0")
        if target_mode != "fixed_r":
            raise ValueError(f"ORBContinuationStrategy only supports target_mode fixed_r, got {target_mode!r}")
        if target_r <= 0:
            raise ValueError("target_r must be > 0 when target_mode is fixed_r")
        if max_trades < 1:
            raise ValueError("max_trades_per_day must be >= 1")
        if entry_end <= entry_start:
            raise ValueError("entry_end_minute must be > entry_start_minute")

        missing = [c for c in self.required_features() if c not in df.columns]
        if missing:
            raise ValueError(f"ORBContinuationStrategy missing feature columns: {missing}")

        out = init_standard_signal_columns(df, strategy_name=self.name, copy=True)

        allow_long = side in ("long_only", "both")
        allow_short = side in ("short_only", "both")

        m = (
            out["after_orb"].astype(bool)
            & (out["minute_from_open"] >= entry_start)
            & (out["minute_from_open"] <= entry_end)
        )
        if min_w is not None and not (isinstance(min_w, float) and math.isnan(min_w)):
            m = m & (out["orb_width_pct"].astype(float) >= float(min_w))
        if max_w is not None and not (isinstance(max_w, float) and math.isnan(max_w)):
            m = m & (out["orb_width_pct"].astype(float) <= float(max_w))

        close = out["close"].astype(float)
        vw = out["vwap"].astype(float)
        slope = out["vwap_slope_5"].astype(float)

        orb_mid = out["orb_mid"].astype(float)
        orb_low = out["orb_low"].astype(float)
        orb_high = out["orb_high"].astype(float)

        base_stop_long = orb_mid if stop_mode == "orb_mid" else orb_low
        base_stop_short = orb_mid if stop_mode == "orb_mid" else orb_high
        stop_long = base_stop_long - stop_buffer
        stop_short = base_stop_short + stop_buffer

        long_raw = m & out["above_orb_high"].astype(bool) & pd.Series(allow_long, index=out.index)
        if require_vwap_side:
            long_raw = long_raw & (close > vw)
        if require_vwap_slope:
            long_raw = long_raw & (slope >= 0)

        short_raw = m & out["below_orb_low"].astype(bool) & pd.Series(allow_short, index=out.index)
        if require_vwap_side:
            short_raw = short_raw & (close < vw)
        if require_vwap_slope:
            short_raw = short_raw & (slope <= 0)

        out["orb_raw_long"] = long_raw.fillna(False)
        out["orb_raw_short"] = short_raw.fillna(False)

        risk_long = close - stop_long
        risk_short = stop_short - close

        cand_long = out["orb_raw_long"] & (risk_long > 0)
        cand_short = out["orb_raw_short"] & (risk_short > 0)
        out["orb_candidate_long"] = cand_long
        out["orb_candidate_short"] = cand_short

        if daily_mode == "per_side":
            keep_l = _thin_first_n_per_session(out, cand_long, max_n=max_trades)
            keep_s = _thin_first_n_per_session(out, cand_short, max_n=max_trades)
            final_long = cand_long & keep_l
            final_short = cand_short & keep_s
        else:
            keep_l, keep_s = _thin_first_signal_per_session(out, cand_long, cand_short, max_n=max_trades)
            final_long = cand_long & keep_l
            final_short = cand_short & keep_s

        tgt_long = close + target_r * risk_long
        tgt_short = close - target_r * risk_short

        long_ix = final_long
        out.loc[long_ix, "sig_side"] = 1
        out.loc[long_ix, "sig_entry_ref"] = close[long_ix]
        out.loc[long_ix, "sig_stop"] = stop_long[long_ix]
        out.loc[long_ix, "sig_target_mode"] = "fixed_r"
        out.loc[long_ix, "sig_target_r"] = target_r
        out.loc[long_ix, "sig_target"] = tgt_long[long_ix]
        out.loc[long_ix, "sig_risk_per_share"] = risk_long[long_ix]
        out.loc[long_ix, "sig_reason"] = "orb_long_continuation"
        out.loc[long_ix, "sig_valid"] = True

        short_ix = final_short & ~final_long
        out.loc[short_ix, "sig_side"] = -1
        out.loc[short_ix, "sig_entry_ref"] = close[short_ix]
        out.loc[short_ix, "sig_stop"] = stop_short[short_ix]
        out.loc[short_ix, "sig_target_mode"] = "fixed_r"
        out.loc[short_ix, "sig_target_r"] = target_r
        out.loc[short_ix, "sig_target"] = tgt_short[short_ix]
        out.loc[short_ix, "sig_risk_per_share"] = risk_short[short_ix]
        out.loc[short_ix, "sig_reason"] = "orb_short_continuation"
        out.loc[short_ix, "sig_valid"] = True

        return apply_min_risk_filter_df(out, config=config)

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        return ()

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        bt = config.get("backtest") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(feat.get("orb_open_minutes", 15)),
            str(sig.get("side", "both")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            bool(sig.get("require_vwap_side", True)),
            bool(sig.get("require_vwap_slope", True)),
            str(sig.get("daily_signal_mode", "first_signal")),
            nz(sig.get("min_orb_width_pct")),
            nz(sig.get("max_orb_width_pct")),
            str(risk.get("stop_mode", "orb_mid")),
            float(risk.get("stop_buffer", 0.0)),
            str(risk.get("target_mode", "fixed_r")),
            float(risk["target_r"]),
            int(risk.get("max_trades_per_day", 1)),
            int(bt.get("eod_exit_minute", 389)),
            float(bt.get("quantity", 1.0)),
            float(bt.get("commission_per_trade", 0.0)),
            float(bt.get("slippage_per_share", 0.0)),
            bool(bt.get("recompute_target_from_entry", True)),
            nz(bt.get("max_hold_minutes")),
            float(risk.get("min_risk_per_share") or 0.0),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> ORBContinuationContext:
        if "ts_utc" in df.columns:
            work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        else:
            work = df.reset_index(drop=True)
        missing = [c for c in self.required_features() if c not in work.columns]
        if missing:
            raise ValueError(f"ORBContinuationStrategy missing feature columns: {missing}")
        n = len(work)
        sid = session_id_from_dates(work["session_date"])
        return ORBContinuationContext(
            n=n,
            session_id=sid,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32, copy=False),
            open=work["open"].to_numpy(dtype=np.float64, copy=False),
            high=work["high"].to_numpy(dtype=np.float64, copy=False),
            low=work["low"].to_numpy(dtype=np.float64, copy=False),
            close=work["close"].to_numpy(dtype=np.float64, copy=False),
            vwap=work["vwap"].to_numpy(dtype=np.float64, copy=False),
            vwap_slope_5=work["vwap_slope_5"].to_numpy(dtype=np.float64, copy=False),
            orb_high=work["orb_high"].to_numpy(dtype=np.float64, copy=False),
            orb_low=work["orb_low"].to_numpy(dtype=np.float64, copy=False),
            orb_mid=work["orb_mid"].to_numpy(dtype=np.float64, copy=False),
            orb_width_pct=work["orb_width_pct"].to_numpy(dtype=np.float64, copy=False),
            after_orb=work["after_orb"].to_numpy(dtype=bool, copy=False),
            above_orb_high=work["above_orb_high"].to_numpy(dtype=bool, copy=False),
            below_orb_low=work["below_orb_low"].to_numpy(dtype=bool, copy=False),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if isinstance(ctx, pd.DataFrame):
            return super().generate_signal_arrays_from_context(ctx, config)
        if not isinstance(ctx, ORBContinuationContext):
            raise TypeError(f"expected ORBContinuationContext or DataFrame, got {type(ctx)}")
        return _orb_signal_arrays_from_context(ctx, config)

    def generate_signal_arrays(self, df: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
        return self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)


def _thin_first_n_per_session(
    df: pd.DataFrame,
    raw_mask: pd.Series,
    *,
    max_n: int,
) -> pd.Series:
    keep = pd.Series(False, index=df.index)
    tcol = "ts_utc" if "ts_utc" in df.columns else "ts_ny"
    for sid in df["session_date"].unique():
        sub = df[df["session_date"] == sid].sort_values(tcol)
        taken = 0
        for idx in sub.index:
            if bool(raw_mask.loc[idx]) and taken < max_n:
                keep.loc[idx] = True
                taken += 1
    return keep


def _thin_first_signal_per_session(
    df: pd.DataFrame,
    cand_long: pd.Series,
    cand_short: pd.Series,
    *,
    max_n: int,
) -> tuple[pd.Series, pd.Series]:
    keep_long = pd.Series(False, index=df.index)
    keep_short = pd.Series(False, index=df.index)
    tcol = "ts_utc" if "ts_utc" in df.columns else "ts_ny"
    for sid in df["session_date"].unique():
        sub = df[df["session_date"] == sid].sort_values(tcol)
        picked: list = []
        for idx in sub.index:
            cl = bool(cand_long.loc[idx])
            cs = bool(cand_short.loc[idx])
            if cl and cs:
                picked.append((idx, 1))
            elif cl:
                picked.append((idx, 1))
            elif cs:
                picked.append((idx, -1))
        for idx, sgn in picked[:max_n]:
            if sgn == 1:
                keep_long.loc[idx] = True
            else:
                keep_short.loc[idx] = True
    return keep_long, keep_short


def _orb_signal_arrays_from_context(ctx: ORBContinuationContext, config: dict[str, Any]) -> dict[str, np.ndarray]:
    sig_cfg = config.get("signal") or {}
    risk_cfg = config.get("risk") or {}

    side = str(sig_cfg.get("side", "both"))
    entry_start = int(sig_cfg["entry_start_minute"])
    entry_end = int(sig_cfg["entry_end_minute"])
    require_vwap_side = bool(sig_cfg.get("require_vwap_side", True))
    require_vwap_slope = bool(sig_cfg.get("require_vwap_slope", True))
    min_w = sig_cfg.get("min_orb_width_pct")
    max_w = sig_cfg.get("max_orb_width_pct")
    daily_mode = str(sig_cfg.get("daily_signal_mode", "first_signal"))

    stop_mode = str(risk_cfg.get("stop_mode", "orb_mid"))
    stop_buffer = float(risk_cfg.get("stop_buffer", 0.0))
    target_mode = str(risk_cfg.get("target_mode", "fixed_r"))
    target_r = float(risk_cfg["target_r"])
    max_trades = int(risk_cfg.get("max_trades_per_day", 1))

    if side not in ("long_only", "short_only", "both"):
        raise ValueError(f"side must be long_only, short_only, or both, got {side!r}")
    if daily_mode not in ("first_signal", "per_side"):
        raise ValueError(f"daily_signal_mode must be first_signal or per_side, got {daily_mode!r}")
    if stop_mode not in ("orb_mid", "orb_opposite"):
        raise ValueError(f"stop_mode must be orb_mid or orb_opposite, got {stop_mode!r}")
    if stop_buffer < 0:
        raise ValueError("stop_buffer must be >= 0")
    if target_mode != "fixed_r":
        raise ValueError(f"ORB continuation supports target_mode fixed_r only, got {target_mode!r}")
    if target_r <= 0:
        raise ValueError("target_r must be > 0 when target_mode is fixed_r")
    if max_trades < 1:
        raise ValueError("max_trades_per_day must be >= 1")
    if entry_end <= entry_start:
        raise ValueError("entry_end_minute must be > entry_start_minute")

    n = ctx.n
    after_orb = ctx.after_orb
    minute = ctx.minute
    orb_width = ctx.orb_width_pct
    close = ctx.close
    vw = ctx.vwap
    slope = ctx.vwap_slope_5
    orb_mid = ctx.orb_mid
    orb_low = ctx.orb_low
    orb_high = ctx.orb_high
    above_hi = ctx.above_orb_high
    below_lo = ctx.below_orb_low
    session_id = ctx.session_id

    m = after_orb & (minute >= entry_start) & (minute <= entry_end)
    if min_w is not None and not (isinstance(min_w, float) and math.isnan(min_w)):
        m = m & (orb_width >= float(min_w))
    if max_w is not None and not (isinstance(max_w, float) and math.isnan(max_w)):
        m = m & (orb_width <= float(max_w))

    allow_long = side in ("long_only", "both")
    allow_short = side in ("short_only", "both")

    if stop_mode == "orb_mid":
        base_sl = orb_mid
        base_ss = orb_mid
    else:
        base_sl = orb_low
        base_ss = orb_high
    stop_long = base_sl - stop_buffer
    stop_short = base_ss + stop_buffer

    if allow_long:
        long_raw = m & above_hi
        if require_vwap_side:
            long_raw = long_raw & (close > vw)
        if require_vwap_slope:
            long_raw = long_raw & (slope >= 0)
    else:
        long_raw = np.zeros(n, dtype=bool)

    if allow_short:
        short_raw = m & below_lo
        if require_vwap_side:
            short_raw = short_raw & (close < vw)
        if require_vwap_slope:
            short_raw = short_raw & (slope <= 0)
    else:
        short_raw = np.zeros(n, dtype=bool)

    risk_long = close - stop_long
    risk_short = stop_short - close
    cand_long = long_raw & (risk_long > 0)
    cand_short = short_raw & (risk_short > 0)

    if daily_mode == "per_side":
        final_long, final_short = thin_per_side_per_session_numba(
            cand_long, cand_short, session_id, max_trades
        )
    else:
        final_long, final_short = thin_first_signal_per_session_numba(
            cand_long, cand_short, session_id, max_trades
        )

    short_ix = final_short & (~final_long)

    side_a = np.zeros(n, dtype=np.int8)
    valid_a = np.zeros(n, dtype=bool)
    stop_a = np.zeros(n, dtype=np.float64)
    tgt_prev = np.zeros(n, dtype=np.float64)
    tmode = np.full(n, TM_NONE, dtype=np.int8)
    tr_a = np.zeros(n, dtype=np.float64)
    risk_a = np.zeros(n, dtype=np.float64)

    for i in np.flatnonzero(final_long):
        side_a[i] = 1
        valid_a[i] = True
        stop_a[i] = stop_long[i]
        rl = risk_long[i]
        risk_a[i] = rl
        tgt_prev[i] = close[i] + target_r * rl
        tmode[i] = TM_FIXED_R
        tr_a[i] = target_r

    for i in np.flatnonzero(short_ix):
        side_a[i] = -1
        valid_a[i] = True
        stop_a[i] = stop_short[i]
        rs = risk_short[i]
        risk_a[i] = rs
        tgt_prev[i] = close[i] - target_r * rs
        tmode[i] = TM_FIXED_R
        tr_a[i] = target_r

    min_rr = get_min_risk_per_share(config)
    valid_a, side_a = apply_min_risk_filter_arrays(valid_a, side_a, risk_a, min_rr)

    return {
        "side": side_a,
        "valid": valid_a,
        "stop": stop_a,
        "target_preview": tgt_prev,
        "target_mode_code": tmode,
        "target_r": tr_a,
        "risk_preview": risk_a,
    }


def build_orb_signal_arrays_fast(df: pd.DataFrame, config: dict[str, Any]) -> dict[str, np.ndarray]:
    """Compatibility wrapper (prepare + fast arrays). Prefer ORBContinuationStrategy + sweep context cache."""
    s = ORBContinuationStrategy()
    return s.generate_signal_arrays(df, config)


def main(argv: list[str] | None = None) -> int:
    from src.strategies.loader import load_strategy_config

    p = argparse.ArgumentParser(description="ORB continuation signal smoke test.")
    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--symbol", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)

    cfg = load_strategy_config("orb_continuation")
    feat_cfg = cfg.get("features") or {}
    raw = read_bars(
        asset=args.asset,
        symbol=args.symbol.upper().strip(),
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
    )
    if len(raw) == 0:
        print("ERROR empty bars", file=sys.stderr)
        return 1

    orb_m = int(feat_cfg.get("orb_open_minutes", 15))
    vb = tuple(feat_cfg.get("vwap_bands") or (1.0, 2.0))
    vw = tuple(feat_cfg.get("vol_windows") or (5, 15, 30))
    feat = build_basic_features(
        raw,
        orb_open_minutes=orb_m,
        vwap_bands=vb,
        vol_windows=vw,
        copy=True,
        allow_overwrite=False,
    )

    strat = ORBContinuationStrategy()
    if cfg.get("signal", {}).get("entry_start_minute") is None:
        cfg = dict(cfg)
        cfg["signal"] = dict(cfg.get("signal") or {})
        cfg["signal"]["entry_start_minute"] = orb_m
    out = strat.generate_signals(feat, cfg)

    v = out["sig_valid"].fillna(False)
    s = out["sig_side"].fillna(0)
    print(f"rows={len(out)}", flush=True)
    print(f"nonzero_signals={int((v & (s != 0)).sum())}", flush=True)
    print(f"long_signals={int((v & (s == 1)).sum())}", flush=True)
    print(f"short_signals={int((v & (s == -1)).sum())}", flush=True)
    print(f"sessions={out['session_date'].nunique()}", flush=True)
    print(f"sessions_with_signals={out.groupby('session_date')['sig_valid'].any().sum()}", flush=True)
    show = out[v][
        [
            "ts_ny",
            "session_date",
            "minute_from_open",
            "close",
            "sig_side",
            "sig_stop",
            "sig_target",
            "sig_target_mode",
            "sig_target_r",
            "sig_risk_per_share",
            "sig_reason",
            "sig_valid",
        ]
    ].head(15)
    print("sample:", flush=True)
    print(show.to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
