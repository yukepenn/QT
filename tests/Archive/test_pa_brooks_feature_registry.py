"""Brooks PA primitives present after build; feature_key reacts to PA knobs."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.features.feature_config import FEATURE_COLUMNS
from src.features.pa_magnet_columns import pa_magnet_level_column_names
from src.features.pa_swings import pa_swing_column_names
from src.features.regime import regime_column_names
from src.features.build_types import PaFeatureConfig, RegimeFeatureConfig
from src.strategies.loader import load_strategy, load_strategy_config


def _raw_session() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts_utc": pd.date_range(
                "2025-01-02 14:30", periods=200, freq="1min", tz="UTC"
            ),
            "open": 400.0,
            "high": 401.0,
            "low": 399.0,
            "close": 400.5,
            "volume": 1e6,
        }
    )


@pytest.fixture
def pa_cfg() -> dict:
    return load_strategy_config("pa_buy_sell_close_trend")


def test_expected_columns_after_build(pa_cfg: dict) -> None:
    df = build_features_from_config(_raw_session(), pa_cfg)
    for col in (
        "strong_bull_close",
        "bull_micro_channel_3",
        "pa_second_entry_buy_proxy_20",
        "pa_failed_breakout_down_age_20",
        "pa_failed_breakout_up_age_20",
        "pa_always_in_side_30",
        "pa_regime_label_30",
        "pa_trade_mode_30",
        "near_orb_high_known_atr",
        "near_pa_mm_range_up_atr_20",
    ):
        assert col in df.columns, f"missing {col}"


def test_feature_key_changes_swing_windows(pa_cfg: dict) -> None:
    a = deepcopy(pa_cfg)
    b = deepcopy(pa_cfg)
    b.setdefault("features", {}).setdefault("pa", {})["swing_windows"] = [10, 20]
    assert feature_key_from_config(a) != feature_key_from_config(b)


def test_feature_key_changes_regime_windows(pa_cfg: dict) -> None:
    a = deepcopy(pa_cfg)
    b = deepcopy(pa_cfg)
    b.setdefault("features", {}).setdefault("pa", {})["regime_windows"] = [20, 60]
    assert feature_key_from_config(a) != feature_key_from_config(b)


def test_registry_lists_include_new_swing_names() -> None:
    spec = PaFeatureConfig(swing_windows=(20,))
    names = pa_swing_column_names(spec)
    assert "pa_failed_breakout_down_age_20" in names
    assert "pa_failed_breakout_up_age_20" in names
    assert "pa_failed_breakout_age_20" in names


def test_price_action_registry_has_strong_bull_close() -> None:
    assert "strong_bull_close" in FEATURE_COLUMNS["price_action"]


def test_regime_and_magnet_registry() -> None:
    pa = PaFeatureConfig(swing_windows=(20,), regime_windows=(30,))
    reg = RegimeFeatureConfig(windows=(20,))
    assert any(c.startswith("pa_always_in_side_30") for c in regime_column_names(reg, pa))
    assert "near_pa_mm_range_up_atr_20" in pa_magnet_level_column_names((20,))


def test_pa_strategies_no_lookahead_in_required() -> None:
    for name in (
        "pa_buy_sell_close_trend",
        "pa_failed_range_breakout_trap",
    ):
        s = load_strategy(name)
        bad = [c for c in s.required_features() if "LOOKAHEAD" in str(c)]
        assert not bad
