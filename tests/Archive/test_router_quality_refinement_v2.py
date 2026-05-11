"""Unit tests for router_quality_refinement_v2_lib (no heavy local panel)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.router_quality_refinement_v2_lib import (
    DECISION_LABELS,
    ROUTER_VARIANTS,
    add_quality_variants,
    label_router_row,
    max_drawdown_r_proxy,
    profit_factor_r,
    retention_pct,
    router_keep_mask,
    threshold_keep_mask,
)


def test_profit_factor_r_zero_losses_inf_wins() -> None:
    s = pd.Series([1.0, 2.0])
    assert profit_factor_r(s) == float("inf")


def test_profit_factor_r_normal() -> None:
    s = pd.Series([2.0, -1.0])
    assert profit_factor_r(s) == pytest.approx(2.0)


def test_max_drawdown_r_proxy_deterministic() -> None:
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, -2.0, 3.0, -1.0],
            "signal_ts_utc": pd.date_range("2024-01-01", periods=4, freq="min", tz="UTC"),
            "session_date": ["2024-01-01"] * 4,
        }
    )
    v1 = max_drawdown_r_proxy(df)
    v2 = max_drawdown_r_proxy(df.sort_values("signal_ts_utc", ascending=False))
    assert v1 is not None and v1 == v2


def test_retention_pct() -> None:
    assert retention_pct(6, 10) == 0.6


def test_router_variants_no_production_router_string() -> None:
    for v in ROUTER_VARIANTS:
        assert "combiner" not in v
        assert "production" not in v


def test_router_keep_mask_baseline_all_true() -> None:
    df = pd.DataFrame({"context_bucket": ["late_climax"], "candidate_id": ["X"], "window": ["late_oow"]})
    m = router_keep_mask(df, "baseline_all")
    assert bool(m.all())


def test_threshold_fixed_ab() -> None:
    df = pd.DataFrame({"profile_id": ["a"], "quality_score_v2": [80.0]})
    m = threshold_keep_mask(df, "quality_score_v2", "fixed_AB")
    assert bool(m.iloc[0])


def test_decision_labels_unique_set() -> None:
    assert len(DECISION_LABELS) == len(set(DECISION_LABELS))


def test_add_quality_variants_columns_exist() -> None:
    df = pd.DataFrame(
        {
            "candidate_id": ["PA_BUY_SELL_CLOSE_TREND_003"],
            "context_bucket": ["trend_long"],
            "decision_pa_distance_from_vwap_atr": [0.5],
            "decision_trend_score_20": [1.0],
            "risk_per_share": [0.05],
            "entry_trade_number_of_day": [1],
            "entry_prior_trade_was_loss": [False],
            "r_multiple": [0.1],
            "session_date": ["2024-01-02"],
            "signal_ts_utc": ["2024-01-02T14:30:00+00:00"],
            "profile_id": ["pa_only_mtp1_meta"],
            "window": ["insample_ref"],
            "weak_period_flag": [False],
        }
    )
    out = add_quality_variants(df)
    assert "score_regime_level_cost_only" in out.columns


def test_label_router_too_destructive_low_retention() -> None:
    lab = label_router_row(
        retention=0.4,
        delta_pf=0.05,
        delta_dd=2.0,
        delta_weak_r=0.0,
        delta_total_r=-5.0,
        profile_id="pa_gap_mtp2_meta",
    )
    assert lab == "ROUTER_V2_TOO_DESTRUCTIVE"
