"""Tests for trade enrichment helpers (small synthetic frames)."""
from __future__ import annotations

import pandas as pd

from src.research.enrich_combiner_trades import enrich_trades_frame
from src.research.trade_quality_helpers import (
    add_prior_trade_columns,
    enum_label,
    exit_reason_flags,
    merge_features_asof_backward,
    profit_factor_r,
    REGIME_LABEL_MAP,
)


def test_merge_asof_backward_no_lookahead():
    trades = pd.DataFrame(
        {
            "entry_ts_utc": pd.to_datetime(
                ["2023-01-03T14:31:00Z", "2023-01-03T15:00:00Z"], utc=True
            ),
            "session_date": ["2023-01-03", "2023-01-03"],
            "strategy": ["a", "a"],
            "strategy_family": ["f", "f"],
            "r_multiple": [1.0, -0.5],
        }
    )
    feats = pd.DataFrame(
        {
            "ts_utc": pd.to_datetime(
                ["2023-01-03T14:30:00Z", "2023-01-03T14:35:00Z", "2023-01-03T14:59:00Z"], utc=True
            ),
            "minute_from_open": [1, 6, 30],
            "pa_regime_label_20": [4, 4, 4],
        }
    )
    m = merge_features_asof_backward(trades, feats)
    assert int(m.iloc[0]["minute_from_open"]) == 1
    assert int(m.iloc[1]["minute_from_open"]) == 30


def test_prior_trade_columns():
    df = pd.DataFrame(
        {
            "session_date": ["d1", "d1", "d1"],
            "entry_ts_utc": pd.to_datetime(
                ["2023-01-03T14:31:00Z", "2023-01-03T15:01:00Z", "2023-01-03T16:01:00Z"], utc=True
            ),
            "strategy": ["s", "s", "t"],
            "strategy_family": ["f", "f", "g"],
            "r_multiple": [1.0, -0.5, 0.25],
        }
    )
    out = add_prior_trade_columns(df)
    assert list(out["entry_trade_number_of_day"]) == [1, 2, 3]
    assert out.iloc[1]["entry_prior_trade_pnl_r"] == 1.0
    assert out.iloc[1]["entry_prior_trade_same_strategy"] is True
    assert out.iloc[2]["entry_prior_trade_same_family"] is False


def test_exit_reason_flags():
    assert exit_reason_flags("target")[0] is True
    assert exit_reason_flags("stop")[1] is True
    assert exit_reason_flags("eod")[2] is True


def test_profit_factor_zero_losses():
    assert profit_factor_r(pd.Series([1.0, 2.0])) == float("inf")


def test_enum_label_regime():
    assert enum_label(REGIME_LABEL_MAP, 4) == "trading_range"


def test_enrich_trades_frame_empty():
    out, meta = enrich_trades_frame(pd.DataFrame(), pd.DataFrame())
    assert out.empty
    assert meta["rows_in"] == 0
