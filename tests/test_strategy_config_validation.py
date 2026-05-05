"""Strategy and combiner config validation (synthetic, no parquet)."""

from __future__ import annotations

import copy
import pytest

from src.strategies.loader import load_strategy, load_strategy_config
from src.utils.config_validation import (
    validate_common_combiner_config,
    validate_common_strategy_config,
)


def _base_strategy_cfg(name: str) -> dict:
    return copy.deepcopy(load_strategy_config(name))


def test_common_strategy_target_r_positive():
    cfg = _base_strategy_cfg("failed_orb")
    cfg.setdefault("risk", {})["target_r"] = 0.0
    with pytest.raises(ValueError, match="target_r"):
        validate_common_strategy_config(cfg)


def test_common_strategy_max_trades_per_day():
    cfg = _base_strategy_cfg("failed_orb")
    cfg.setdefault("risk", {})["max_trades_per_day"] = 0
    with pytest.raises(ValueError, match="max_trades_per_day"):
        validate_common_strategy_config(cfg)


def test_common_strategy_entry_window():
    cfg = _base_strategy_cfg("failed_orb")
    cfg.setdefault("signal", {})["entry_start_minute"] = 100
    cfg["signal"]["entry_end_minute"] = 50
    with pytest.raises(ValueError, match="entry_end_minute"):
        validate_common_strategy_config(cfg)


def test_common_combiner_daily_max_loss_non_negative():
    cfg = {
        "execution": {
            "slippage_per_share": 0.01,
            "commission_per_trade": 0.0,
            "eod_exit_minute": 389,
            "no_new_after_minute": 360,
            "min_risk_per_share": 0.0,
        },
        "system": {
            "max_open_positions": 1,
            "max_trades_per_day": 2,
            "daily_max_loss_r": 1.0,
            "cooldown_after_loss_minutes": 0,
        },
        "conflict": {"priority_policy": "metadata_priority"},
    }
    with pytest.raises(ValueError, match="daily_max_loss_r"):
        validate_common_combiner_config(cfg)


def test_common_combiner_max_open_positions():
    cfg = {
        "execution": {
            "slippage_per_share": 0.01,
            "commission_per_trade": 0.0,
            "eod_exit_minute": 389,
            "no_new_after_minute": 360,
            "min_risk_per_share": 0.0,
        },
        "system": {
            "max_open_positions": 2,
            "max_trades_per_day": 2,
            "daily_max_loss_r": -1.0,
            "cooldown_after_loss_minutes": 0,
        },
        "conflict": {"priority_policy": "metadata_priority"},
    }
    with pytest.raises(NotImplementedError, match="max_open_positions"):
        validate_common_combiner_config(cfg)


def test_common_combiner_negative_slippage():
    cfg = {
        "execution": {
            "slippage_per_share": -0.01,
            "commission_per_trade": 0.0,
            "eod_exit_minute": 389,
            "no_new_after_minute": 360,
            "min_risk_per_share": 0.0,
        },
        "system": {
            "max_open_positions": 1,
            "max_trades_per_day": 2,
            "daily_max_loss_r": -1.0,
            "cooldown_after_loss_minutes": 0,
        },
        "conflict": {"priority_policy": "metadata_priority"},
    }
    with pytest.raises(ValueError, match="slippage"):
        validate_common_combiner_config(cfg)


def test_common_combiner_no_new_after_eod():
    cfg = {
        "execution": {
            "slippage_per_share": 0.01,
            "commission_per_trade": 0.0,
            "eod_exit_minute": 360,
            "no_new_after_minute": 389,
            "min_risk_per_share": 0.0,
        },
        "system": {
            "max_open_positions": 1,
            "max_trades_per_day": 2,
            "daily_max_loss_r": -1.0,
            "cooldown_after_loss_minutes": 0,
        },
        "conflict": {"priority_policy": "metadata_priority"},
    }
    with pytest.raises(ValueError, match="no_new_after_minute"):
        validate_common_combiner_config(cfg)


def test_gap_acceptance_rejects_short_only():
    s = load_strategy("gap_acceptance_failure")
    cfg = _base_strategy_cfg("gap_acceptance_failure")
    cfg.setdefault("signal", {})["side"] = "short_only"
    with pytest.raises(ValueError, match="long-only"):
        s.validate_config(cfg)


def test_prior_day_rejects_level_type():
    s = load_strategy("prior_day_level_trap")
    cfg = _base_strategy_cfg("prior_day_level_trap")
    cfg.setdefault("signal", {})["level_type"] = "prior_day_high"
    with pytest.raises(ValueError, match="prior_day_low"):
        s.validate_config(cfg)


def test_afternoon_rejects_midday_window():
    s = load_strategy("afternoon_continuation")
    cfg = _base_strategy_cfg("afternoon_continuation")
    cfg.setdefault("features", {})["midday_window"] = 60
    with pytest.raises(ValueError, match="midday_window"):
        s.validate_config(cfg)


def test_vwap_reversal_rejects_confirm_mode():
    s = load_strategy("vwap_reversal")
    cfg = _base_strategy_cfg("vwap_reversal")
    cfg.setdefault("signal", {})["confirm_mode"] = "not_a_mode"
    with pytest.raises(ValueError, match="confirm_mode"):
        s.validate_config(cfg)


def test_orb_continuation_rejects_stop_mode():
    s = load_strategy("orb_continuation")
    cfg = _base_strategy_cfg("orb_continuation")
    cfg.setdefault("risk", {})["stop_mode"] = "invalid"
    with pytest.raises(ValueError, match="stop_mode"):
        s.validate_config(cfg)


def test_vwap_trend_rejects_trend_window():
    s = load_strategy("vwap_trend_pullback")
    cfg = _base_strategy_cfg("vwap_trend_pullback")
    cfg.setdefault("signal", {})["trend_window"] = 0
    with pytest.raises(ValueError, match="trend_window"):
        s.validate_config(cfg)


def test_midday_compression_rejects_window():
    s = load_strategy("midday_compression_breakout")
    cfg = _base_strategy_cfg("midday_compression_breakout")
    cfg.setdefault("features", {})["compression_window"] = 0
    with pytest.raises(ValueError, match="compression_window"):
        s.validate_config(cfg)
