"""Execution-backed Layer 2 combiner loop (sequential, max one open position)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.combiner.candidate import Candidate
from src.combiner.selection import choose_highest_priority
from src.combiner.state import CombinerState
from src.combiner.trade_intent_adapter import (
    COMBINER_ADAPTER_VERSION,
    build_trade_intent_from_candidate,
    execution_policy_from_combiner_cfg,
    trade_result_to_combiner_row,
    simulate_selected_trade,
)

def _bars_dataframe(backtest_arrays: dict[str, Any], meta_arrays: dict[str, np.ndarray]) -> pd.DataFrame:
    n = int(backtest_arrays["n"])
    ts = meta_arrays["ts_utc"]
    sd = meta_arrays["session_date"]
    return pd.DataFrame(
        {
            "open": backtest_arrays["open"][:n].astype(float),
            "high": backtest_arrays["high"][:n].astype(float),
            "low": backtest_arrays["low"][:n].astype(float),
            "close": backtest_arrays["close"][:n].astype(float),
            "minute_from_open": backtest_arrays["minute"].astype(np.int32)[:n],
            "ts_utc": ts[:n],
            "session_date": sd[:n],
        }
    )


def _daily_loss_budget_r(cfg: Any) -> float:
    v = float(getattr(cfg, "daily_max_loss_r", 2.0))
    return abs(v) if v < 0 else v


def simulate_combiner_canonical(
    *,
    backtest_arrays: dict[str, Any],
    candidate_arrays: dict[str, np.ndarray],
    candidates: list[Candidate],
    meta_arrays: dict[str, np.ndarray],
    combiner_cfg: Any,
    enabled_mask: np.ndarray,
    max_hold_per_candidate: np.ndarray,
    recompute_target: np.ndarray,
    quantity_per_candidate: np.ndarray,
    min_risk_per_candidate: np.ndarray,
    priority_float: np.ndarray,
    score_float: np.ndarray,
    rank_int: np.ndarray,
    active_start: np.ndarray,
    active_end: np.ndarray,
) -> dict[str, Any]:
    """Sequential combiner: one position; selection by priority; exits via ``simulate_trade_path``.

    Simplifications vs archived Numba (documented for parity work):
    - Resolves same-bar conflicts only among candidates **valid on the same signal bar**;
      does not replicate every legacy rejection code path.
    - ``recompute_target`` is ignored here (execution materializes fixed-R at entry).
    - ``min_risk_per_candidate`` is applied only when ``risk_preview`` is missing (via execution).
    """
    del score_float, rank_int, recompute_target, min_risk_per_candidate  # parity / future use
    n = int(backtest_arrays["n"])
    nc = len(candidates)
    if nc == 0:
        raise ValueError("no candidates")

    bars_df = _bars_dataframe(backtest_arrays, meta_arrays)
    side_m = candidate_arrays["side"]
    valid_m = candidate_arrays["valid"]
    stop_m = candidate_arrays["stop"]
    tp_m = candidate_arrays["target_preview"]
    tmc_m = candidate_arrays["target_mode_code"]
    tr_m = candidate_arrays["target_r"]
    risk_m = candidate_arrays["risk_preview"]

    st = CombinerState()
    trade_rows: list[dict[str, Any]] = []
    trade_id = 0
    cursor = 0
    sym0 = candidates[0].symbol

    while cursor < n:
        minute_b = int(backtest_arrays["minute"][cursor])
        if minute_b > int(combiner_cfg.no_new_after_minute):
            cursor += 1
            continue

        sess_day = meta_arrays["session_date"][cursor]
        st.ensure_day(sess_day)
        if not st.can_enter_bar(cursor):
            cursor += 1
            continue
        if st.max_trades_per_day_exceeded(int(combiner_cfg.max_trades_per_day)):
            cursor += 1
            continue
        if st.daily_loss_exceeded(_daily_loss_budget_r(combiner_cfg)):
            cursor += 1
            continue

        competing: list[tuple[int, Candidate]] = []
        sides_seen: set[int] = set()
        for ci in range(nc):
            if int(enabled_mask[ci]) == 0:
                continue
            if int(valid_m[ci, cursor]) == 0 or int(side_m[ci, cursor]) == 0:
                continue
            if minute_b < int(active_start[ci]) or minute_b > int(active_end[ci]):
                continue
            competing.append((ci, candidates[ci]))
            sides_seen.add(int(side_m[ci, cursor]))

        if not competing:
            cursor += 1
            continue

        if combiner_cfg.opposite_direction_skip_all and len(sides_seen) > 1:
            cursor += 1
            continue

        def prio(item: tuple[int, Candidate]) -> float:
            ci, _c = item
            return float(priority_float[ci])

        def tie(item: tuple[int, Candidate], idx: int) -> tuple[str, int]:
            _ci, c = item
            return (c.candidate_id, idx)

        win_idx = choose_highest_priority(competing, priority_key=prio, tie_key=tie)
        if win_idx is None:
            cursor += 1
            continue
        ci, cand = competing[win_idx]
        entry_bar = cursor + 1
        if entry_bar >= n:
            cursor += 1
            continue

        side = int(side_m[ci, cursor])
        stop_px = float(stop_m[ci, cursor])
        tmc = int(tmc_m[ci, cursor])
        trv = float(tr_m[ci, cursor])
        tpv = float(tp_m[ci, cursor])
        risk_pv = float(risk_m[ci, cursor]) if np.isfinite(risk_m[ci, cursor]) else None
        mh = int(max_hold_per_candidate[ci])
        max_hold = None if mh < 0 else mh
        qty = float(quantity_per_candidate[ci])

        try:
            intent = build_trade_intent_from_candidate(
                candidate=cand,
                ci=ci,
                signal_bar=cursor,
                entry_bar=entry_bar,
                side=side,
                stop_price=stop_px,
                target_preview=tpv,
                target_mode_code=tmc,
                target_r=trv,
                risk_preview=risk_pv,
                max_hold_bars=max_hold,
                qty=qty,
            )
        except ValueError:
            cursor += 1
            continue

        res = simulate_selected_trade(bars_df, intent, combiner_cfg=combiner_cfg, max_hold_override=max_hold)
        if not res.ok:
            cursor += 1
            continue

        exit_bar = int(intent.entry_idx) + int(res.bars_held) - 1
        exit_bar = min(exit_bar, n - 1)
        pol = execution_policy_from_combiner_cfg(combiner_cfg)
        st.register_trade_open()
        dtn = int(st.trades_today)
        trade_id += 1
        ts_sig = pd.Timestamp(meta_arrays["ts_utc"][cursor]).isoformat()
        ts_ent = pd.Timestamp(meta_arrays["ts_utc"][intent.entry_idx]).isoformat()
        ts_ex = pd.Timestamp(meta_arrays["ts_utc"][exit_bar]).isoformat()
        sdate = str(meta_arrays["session_date"][cursor])

        trade_rows.append(
            trade_result_to_combiner_row(
                trade_id=trade_id,
                candidate=cand,
                intent=intent,
                result=res,
                symbol=sym0,
                session_date=sdate,
                signal_ts_utc=ts_sig,
                entry_ts_utc=ts_ent,
                exit_ts_utc=ts_ex,
                exit_bar_idx=exit_bar,
                stop_at_signal=stop_px,
                target_preview_at_signal=tpv,
                target_mode_code_at_signal=tmc,
                target_r_at_signal=trv,
                priority=float(priority_float[ci]),
                daily_trade_number=dtn,
                policy=pol,
                engine="execution_backed",
            )
        )

        st.register_trade_close(float(res.r_multiple))
        if float(res.r_multiple) < 0 and int(combiner_cfg.cooldown_after_loss_minutes) > 0:
            st.start_cooldown(from_bar=exit_bar, cooldown_bars=int(combiner_cfg.cooldown_after_loss_minutes))

        cursor = exit_bar + 1

    trades_df = pd.DataFrame(trade_rows) if trade_rows else pd.DataFrame()
    equity = np.zeros(n, dtype=np.float64)
    run = 0.0
    ti = 0
    for bi in range(n):
        while ti < len(trade_rows) and int(trade_rows[ti]["exit_idx"]) == bi:
            run += float(trade_rows[ti]["net_pnl"])
            ti += 1
        equity[bi] = run
    equity_df = pd.DataFrame({"bar_idx": np.arange(n, dtype=np.int32), "equity": equity})

    return {
        "trades_df": trades_df,
        "equity_df": equity_df,
        "candidate_signal_log_df": pd.DataFrame(),
        "rejected_signals_df": pd.DataFrame(),
        "rejection_counts": np.zeros(32, dtype=np.int64),
        "combiner_adapter_version": COMBINER_ADAPTER_VERSION,
        "combiner_engine": "execution_backed",
    }
