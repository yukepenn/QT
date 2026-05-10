"""PA shared helpers (pa_common)."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy_config
from src.strategies.strategy.pa_common import (
    build_pa_reason,
    pa_context_windows,
    pa_family_from_strategy_name,
    safe_bool_array,
    safe_float_array,
)


def test_pa_context_windows_defaults() -> None:
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    rw, regw, ac = pa_context_windows(cfg)
    assert rw == 60 and regw == 30 and ac == "atr_like_20"


def test_pa_context_windows_overrides() -> None:
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    cfg.setdefault("features", {})["pa_range_window"] = 30
    cfg.setdefault("signal", {})["atr_column"] = "atr_like_15"
    rw, regw, ac = pa_context_windows(cfg)
    assert rw == 30 and ac == "atr_like_15"


def test_build_pa_reason() -> None:
    assert "pa_buy" in build_pa_reason("pa_buy_sell_close_trend", "close_trend", extra="x")


def test_safe_arrays() -> None:
    n = 5
    assert safe_bool_array([0, 1, 0, 2, 0], n).shape == (n,)
    assert np.isnan(safe_float_array("bad", n)).all()


def test_pa_family() -> None:
    assert pa_family_from_strategy_name("pa_climax_reversal") == "pa_mvp"
