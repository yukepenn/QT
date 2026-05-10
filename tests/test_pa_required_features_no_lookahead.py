"""PA strategies: required_features stay LOOKAHEAD-free and build on default configs."""

from __future__ import annotations

import pytest

from src.features.feature_key import build_features_from_config
from src.strategies.loader import load_strategy, load_strategy_config

PA_ALL = (
    "pa_trading_range_bls_hs",
    "pa_failed_range_breakout_trap",
    "pa_tight_channel_pullback",
    "pa_mtr_reversal",
    "pa_broad_channel_zone",
    "pa_climax_reversal",
    "pa_second_entry_pullback",
    "pa_wedge_reversal",
    "pa_buy_sell_close_trend",
    "pa_generic_breakout_pullback",
)


@pytest.mark.parametrize("name", PA_ALL)
def test_pa_required_features_no_lookahead(name: str) -> None:
    s = load_strategy(name)
    bad = [c for c in s.required_features() if "LOOKAHEAD" in str(c)]
    assert not bad, bad


@pytest.mark.parametrize("name", PA_ALL)
def test_pa_default_config_builds_required_columns(name: str) -> None:
    import pandas as pd

    s = load_strategy(name)
    cfg = load_strategy_config(name)
    raw = pd.DataFrame(
        {
            "ts_utc": pd.date_range(
                "2025-01-02 14:30", periods=120, freq="1min", tz="UTC"
            ),
            "open": 400.0,
            "high": 401.0,
            "low": 399.0,
            "close": 400.5,
            "volume": 1e6,
        }
    )
    df = build_features_from_config(raw, cfg)
    missing = [c for c in s.required_features() if c not in df.columns]
    assert not missing, missing
    assert s.supports_fast is True
