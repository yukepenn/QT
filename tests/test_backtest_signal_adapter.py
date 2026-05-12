"""Tests for src.backtest.signal_adapter."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.signal_adapter import (
    canonicalize_signal_frame,
    infer_signal_mapping,
    validate_canonical_signal_frame,
)
from src.strategies.strategy.base import init_standard_signal_columns


def test_infer_signal_mapping_empty_without_contract():
    assert infer_signal_mapping("orb_continuation") == {}


def test_canonicalize_renames_columns():
    df = pd.DataFrame({"my_stop": [99.0], "sig_side": [0]})
    # incomplete frame on purpose — only rename path
    out = canonicalize_signal_frame(df, {"my_stop": "sig_stop"}, copy=True)
    assert "sig_stop" in out.columns and out["sig_stop"].iloc[0] == 99.0


def test_validate_accepts_direct_canonical_columns():
    df = init_standard_signal_columns(
        pd.DataFrame({"x": [1]}), strategy_name="t", copy=True
    )
    df.loc[0, "sig_valid"] = True
    df.loc[0, "sig_side"] = 1
    df.loc[0, "sig_stop"] = 10.0
    df.loc[0, "sig_target_mode"] = "fixed_r"
    df.loc[0, "sig_target_r"] = 1.5
    assert validate_canonical_signal_frame(df) == []


def test_validate_raises_on_missing_standard_columns():
    df = pd.DataFrame({"sig_valid": [True]})
    with pytest.raises(ValueError, match="missing standard signal columns"):
        validate_canonical_signal_frame(df)


def test_validate_reports_invalid_target_mode_on_valid_row():
    df = init_standard_signal_columns(
        pd.DataFrame({"x": [1]}), strategy_name="t", copy=True
    )
    df.loc[0, "sig_valid"] = True
    df.loc[0, "sig_side"] = 1
    df.loc[0, "sig_stop"] = 10.0
    df.loc[0, "sig_target_mode"] = "not_a_mode"
    issues = validate_canonical_signal_frame(df)
    assert issues and "sig_target_mode" in issues[0]
