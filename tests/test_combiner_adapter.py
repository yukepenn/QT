"""Synthetic tests for execution-backed combiner adapter (no heavy market data)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.combiner.adapter import simulate_combiner_canonical
from src.combiner.candidate import Candidate
from src.combiner.selection import choose_highest_priority
from src.combiner.simulator import CombinerConfig, simulate_combiner_numba
from src.combiner.trade_intent_adapter import (
    COMBINER_ADAPTER_VERSION,
    build_trade_intent_from_candidate,
    simulate_selected_trade,
    trade_result_to_combiner_row,
)
from src.execution.types import ExitReason, TM_FIXED_R


def _candidate(*, cid: str = "C_TEST_001", priority: int = 10) -> Candidate:
    return Candidate(
        candidate_id=cid,
        strategy="synthetic",
        asset="equity",
        symbol="QQQ",
        candidate_rank=1,
        source_sweep_path="",
        source_results_csv="",
        params_hash="00",
        config={},
        metrics={},
        metadata={},
        selection={},
        family="test_family",
        conflict_group="g",
        default_priority=priority,
        default_active_start_minute=0,
        default_active_end_minute=389,
        warning="",
    )


def _uptrend_bars(*, n: int = 40, start: float = 100.0) -> pd.DataFrame:
    t = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    ny = pd.date_range("2024-01-02 09:30", periods=n, freq="min")
    close = np.linspace(start, start + 5.0, n)
    return pd.DataFrame(
        {
            "open": close - 0.02,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "minute_from_open": np.arange(n, dtype=np.int32),
            "ts_utc": t,
            "session_date": np.array(["2024-01-02"] * n, dtype=object),
        }
    )


def _down_bars_after_entry(*, n: int = 40) -> pd.DataFrame:
    t = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    close = np.concatenate([np.linspace(100, 100.5, 8), np.linspace(100.4, 96.0, n - 8)])
    return pd.DataFrame(
        {
            "open": close - 0.02,
            "high": close + 0.15,
            "low": close - 0.5,
            "close": close,
            "minute_from_open": np.arange(n, dtype=np.int32),
            "ts_utc": t,
            "session_date": np.array(["2024-01-02"] * n, dtype=object),
        }
    )


def test_build_trade_intent_rejects_bad_entry_signal_order():
    c = _candidate()
    with pytest.raises(ValueError, match="entry_bar"):
        build_trade_intent_from_candidate(
            candidate=c,
            ci=0,
            signal_bar=5,
            entry_bar=5,
            side=1,
            stop_price=99.0,
            target_preview=float("nan"),
            target_mode_code=int(TM_FIXED_R),
            target_r=2.0,
            risk_preview=1.0,
            max_hold_bars=None,
            qty=1.0,
        )


def test_long_target_hit_uptrend():
    bars = _uptrend_bars()
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=5,
        entry_bar=6,
        side=1,
        stop_price=99.0,
        target_preview=float("nan"),
        target_mode_code=int(TM_FIXED_R),
        target_r=2.0,
        risk_preview=1.0,
        max_hold_bars=None,
        qty=1.0,
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg)
    assert res.ok
    assert res.exit_reason == ExitReason.TARGET


def test_long_stop_hit():
    bars = _down_bars_after_entry()
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=5,
        entry_bar=6,
        side=1,
        stop_price=99.0,
        target_preview=float("nan"),
        target_mode_code=int(TM_FIXED_R),
        target_r=5.0,
        risk_preview=1.0,
        max_hold_bars=None,
        qty=1.0,
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg)
    assert res.ok
    assert res.exit_reason == ExitReason.STOP


def test_max_hold_exit_flat():
    n = 25
    t = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    close = np.full(n, 100.5)
    bars = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.05,
            "low": close - 0.05,
            "close": close,
            "minute_from_open": np.arange(n, dtype=np.int32),
            "ts_utc": t,
            "session_date": np.array(["2024-01-02"] * n, dtype=object),
        }
    )
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=3,
        entry_bar=4,
        side=1,
        stop_price=98.0,
        target_preview=float("nan"),
        target_mode_code=int(TM_FIXED_R),
        target_r=10.0,
        risk_preview=1.0,
        max_hold_bars=4,
        qty=1.0,
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg, max_hold_override=4)
    assert res.ok
    assert res.exit_reason == ExitReason.MAX_HOLD


def test_invalid_target_r_raises_on_build():
    c = _candidate()
    with pytest.raises(ValueError, match="target_r"):
        build_trade_intent_from_candidate(
            candidate=c,
            ci=0,
            signal_bar=2,
            entry_bar=3,
            side=1,
            stop_price=99.0,
            target_preview=float("nan"),
            target_mode_code=int(TM_FIXED_R),
            target_r=0.0,
            risk_preview=1.0,
            max_hold_bars=None,
            qty=1.0,
        )


def test_selection_deterministic_priority():
    competing = [("a", _candidate(cid="low", priority=1)), ("b", _candidate(cid="high", priority=99))]
    idx = choose_highest_priority(competing, priority_key=lambda x: float(x[1].default_priority))
    assert idx == 1
    assert competing[idx][1].candidate_id == "high"


def test_trade_row_schema_has_version_stamps():
    bars = _uptrend_bars()
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=5,
        entry_bar=6,
        side=1,
        stop_price=99.0,
        target_preview=float("nan"),
        target_mode_code=int(TM_FIXED_R),
        target_r=2.0,
        risk_preview=1.0,
        max_hold_bars=None,
        qty=1.0,
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg)
    from src.combiner.trade_intent_adapter import execution_policy_from_combiner_cfg

    pol = execution_policy_from_combiner_cfg(cfg)
    row = trade_result_to_combiner_row(
        trade_id=1,
        candidate=c,
        intent=intent,
        result=res,
        symbol="QQQ",
        session_date="2024-01-02",
        signal_ts_utc="x",
        entry_ts_utc="y",
        exit_ts_utc="z",
        exit_bar_idx=10,
        stop_at_signal=99.0,
        target_preview_at_signal=float("nan"),
        target_mode_code_at_signal=int(TM_FIXED_R),
        target_r_at_signal=2.0,
        priority=10.0,
        daily_trade_number=1,
        policy=pol,
        engine="execution_backed",
    )
    assert row["combiner_adapter_version"] == COMBINER_ADAPTER_VERSION
    assert row["adapter_semantics_version"] == COMBINER_ADAPTER_VERSION
    assert row["result_lineage"] == "mainline_layer2"
    assert row["engine"] == "execution_backed"
    assert "execution_semantics_version" in row


def test_simulate_combiner_canonical_smoke_one_candidate():
    n = 35
    o = np.linspace(100.0, 104.0, n)
    bt = {
        "open": o,
        "high": o + 0.2,
        "low": o - 0.2,
        "close": o + 0.05,
        "minute": np.arange(n, dtype=np.int32),
        "session_id": np.zeros(n, dtype=np.int32),
        "n": n,
    }
    ts = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    sd = np.array(["2024-01-02"] * n, dtype=object)
    meta = {"ts_utc": ts.to_numpy(), "session_date": sd, "minute_from_open": bt["minute"]}
    nc = 1
    side = np.zeros((nc, n), dtype=np.int8)
    valid = np.zeros((nc, n), dtype=np.int8)
    stop = np.full((nc, n), np.nan)
    tp = np.full((nc, n), np.nan)
    tmc = np.full((nc, n), int(TM_FIXED_R), dtype=np.int8)
    tr = np.full((nc, n), 2.0)
    risk = np.full((nc, n), 1.0)
    sig = 8
    side[0, sig] = 1
    valid[0, sig] = 1
    stop[0, sig] = 99.0
    mats = {"side": side, "valid": valid, "stop": stop, "target_preview": tp, "target_mode_code": tmc, "target_r": tr, "risk_preview": risk}
    cand = _candidate()
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, max_trades_per_day=5)
    out = simulate_combiner_canonical(
        backtest_arrays=bt,
        candidate_arrays=mats,
        candidates=[cand],
        meta_arrays=meta,
        combiner_cfg=cfg,
        enabled_mask=np.ones(nc, dtype=np.int8),
        max_hold_per_candidate=np.array([-1], dtype=np.int32),
        recompute_target=np.zeros(nc, dtype=np.int8),
        quantity_per_candidate=np.ones(nc),
        min_risk_per_candidate=np.zeros(nc),
        priority_float=np.array([10.0]),
        score_float=np.zeros(nc),
        rank_int=np.zeros(nc, dtype=np.int32),
        active_start=np.zeros(nc, dtype=np.int32),
        active_end=np.full(nc, 389, dtype=np.int32),
    )
    df = out["trades_df"]
    assert len(df) >= 1
    assert "combiner_adapter_version" in out
    assert out.get("combiner_engine") == "execution_backed"
    if len(df) and "engine" in df.columns:
        assert (df["engine"] == "execution_backed").all()


def test_legacy_numba_still_callable_with_minimal_stub():
    """Legacy requires full matrix shapes; smoke-import only."""
    assert callable(simulate_combiner_numba)
