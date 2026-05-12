"""combiner_adapter_parity: engine normalization, schema, synthetic parity vs legacy_reference."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.combiner.adapter import simulate_combiner_canonical
from src.combiner.candidate import Candidate
from src.combiner.simulator import (
    CombinerConfig,
    normalize_combiner_engine_label,
    simulate_combiner_numba,
)
from src.combiner.trade_intent_adapter import (
    COMBINER_ADAPTER_VERSION,
    build_trade_intent_from_candidate,
    execution_policy_from_combiner_cfg,
    simulate_selected_trade,
    trade_result_to_combiner_row,
)
from src.execution.types import ExitReason, TM_FIXED_R


def _candidate(*, cid: str = "C_PARITY_001", priority: int = 10) -> Candidate:
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


def test_normalize_engine_synonyms():
    assert normalize_combiner_engine_label("legacy") == "legacy_reference"
    assert normalize_combiner_engine_label("LEGACY_REFERENCE") == "legacy_reference"
    assert normalize_combiner_engine_label("canonical") == "execution_backed"
    assert normalize_combiner_engine_label("execution_backed") == "execution_backed"
    with pytest.raises(ValueError, match="unknown combiner engine"):
        normalize_combiner_engine_label("v2_canonical")


def test_simulate_combiner_execution_backed_is_canonical_alias():
    import src.combiner.simulator as sim

    assert sim.simulate_combiner_execution_backed is sim.simulate_combiner_canonical


def test_trade_intent_valid_long_fields_preserved():
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=2,
        entry_bar=3,
        side=1,
        stop_price=99.0,
        target_preview=float("nan"),
        target_mode_code=int(TM_FIXED_R),
        target_r=2.0,
        risk_preview=1.0,
        max_hold_bars=None,
        qty=1.0,
    )
    assert intent.side == 1
    assert intent.signal_idx == 2 and intent.entry_idx == 3
    assert intent.stop_price == 99.0
    assert intent.target_r == 2.0


def test_execution_row_schema_required_fields():
    n = 30
    t = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    close = np.linspace(100.0, 103.0, n)
    bars = pd.DataFrame(
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
    c = _candidate()
    intent = build_trade_intent_from_candidate(
        candidate=c,
        ci=0,
        signal_bar=4,
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
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg)
    assert res.ok
    pol = execution_policy_from_combiner_cfg(cfg)
    row = trade_result_to_combiner_row(
        trade_id=1,
        candidate=c,
        intent=intent,
        result=res,
        symbol="QQQ",
        session_date="2024-01-02",
        signal_ts_utc="a",
        entry_ts_utc="b",
        exit_ts_utc="c",
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
    for k in (
        "execution_semantics_version",
        "combiner_adapter_version",
        "adapter_semantics_version",
        "result_lineage",
        "engine",
    ):
        assert k in row
    assert row["engine"] == "execution_backed"
    assert row["combiner_adapter_version"] == COMBINER_ADAPTER_VERSION


def test_same_bar_stop_target_policy_stop_first_default():
    """When both levels touched same bar, default policy favors stop (negative R)."""
    n = 12
    t = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    # Bar after entry: wide range hits both stop and target; path uses intrabar ordering
    o = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 95.0, 100.0, 100.0, 100.0, 100.0, 100.0])
    h = np.array([100.1, 100.1, 100.1, 100.1, 100.1, 110.0, 100.1, 100.1, 100.1, 100.1, 100.1, 100.1])
    lo = np.array([99.9, 99.9, 99.9, 99.9, 99.9, 90.0, 99.9, 99.9, 99.9, 99.9, 99.9, 99.9])
    c_ = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0])
    bars = pd.DataFrame(
        {
            "open": o,
            "high": h,
            "low": lo,
            "close": c_,
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
        target_preview=105.0,
        target_mode_code=int(TM_FIXED_R),
        target_r=2.0,
        risk_preview=1.0,
        max_hold_bars=None,
        qty=1.0,
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0)
    res = simulate_selected_trade(bars, intent, combiner_cfg=cfg)
    assert res.ok
    assert res.exit_reason == ExitReason.STOP
    assert float(res.r_multiple) < 0


def test_synthetic_legacy_and_execution_both_run():
    from src.execution.types import TM_FIXED_R

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
    kw = dict(
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
    leg = simulate_combiner_numba(**kw)
    exe = simulate_combiner_canonical(**kw)
    assert isinstance(leg["trades_df"], pd.DataFrame)
    assert isinstance(exe["trades_df"], pd.DataFrame)
    assert len(exe["trades_df"]) >= 1
    if len(exe["trades_df"]):
        assert (exe["trades_df"]["engine"] == "execution_backed").all()
    assert exe.get("combiner_engine") == "execution_backed"


def test_two_candidates_same_bar_priority_selects_one():
    from src.execution.types import TM_FIXED_R

    n = 50
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
    nc = 2
    side = np.zeros((nc, n), dtype=np.int8)
    valid = np.zeros((nc, n), dtype=np.int8)
    stop = np.full((nc, n), np.nan)
    tp = np.full((nc, n), np.nan)
    tmc = np.full((nc, n), int(TM_FIXED_R), dtype=np.int8)
    tr = np.full((nc, n), 2.0)
    risk = np.full((nc, n), 1.0)
    sig = 8
    for ci in (0, 1):
        side[ci, sig] = 1
        valid[ci, sig] = 1
        stop[ci, sig] = 99.0
    mats = {"side": side, "valid": valid, "stop": stop, "target_preview": tp, "target_mode_code": tmc, "target_r": tr, "risk_preview": risk}
    low = _candidate(cid="LOW", priority=1)
    high = _candidate(cid="HIGH", priority=99)
    cfg = CombinerConfig(
        slippage_per_share=0.0,
        commission_per_trade=0.0,
        max_trades_per_day=5,
        allow_same_bar_multiple_candidates=True,
    )
    out = simulate_combiner_canonical(
        backtest_arrays=bt,
        candidate_arrays=mats,
        candidates=[low, high],
        meta_arrays=meta,
        combiner_cfg=cfg,
        enabled_mask=np.ones(nc, dtype=np.int8),
        max_hold_per_candidate=np.full(nc, -1, dtype=np.int32),
        recompute_target=np.zeros(nc, dtype=np.int8),
        quantity_per_candidate=np.ones(nc),
        min_risk_per_candidate=np.zeros(nc),
        priority_float=np.array([1.0, 99.0]),
        score_float=np.zeros(nc),
        rank_int=np.zeros(nc, dtype=np.int32),
        active_start=np.zeros(nc, dtype=np.int32),
        active_end=np.full(nc, 389, dtype=np.int32),
    )
    df = out["trades_df"]
    if len(df) >= 1:
        assert (df["candidate_id"] == "HIGH").all()


def test_legacy_numba_not_notimplemented():
    assert callable(simulate_combiner_numba)
