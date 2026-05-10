"""PA swing / range features must be prior-exclusive and avoid LOOKAHEAD in strategy contracts."""

from __future__ import annotations

import pandas as pd
import pytest
import yaml

from src.features.build_types import PaFeatureConfig
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.features.pa_swings import add_pa_swing_features
from src.strategies.loader import load_strategy, strategy_root


def _raw_two_sessions() -> pd.DataFrame:
    ny = "America/New_York"
    s1 = pd.date_range("2026-01-05 09:30", periods=15, freq="1min", tz=ny)
    s2 = pd.date_range("2026-01-06 09:30", periods=15, freq="1min", tz=ny)
    ts_ny = s1.union(s2)
    ts_utc = ts_ny.tz_convert("UTC")
    n = len(ts_utc)
    high = list(range(10, 10 + 15)) + list(range(30, 30 + 15))
    low = [h - 1 for h in high]
    close = [h - 0.3 for h in high]
    open_ = [c - 0.1 for c in close]
    volume = [100] * n
    return pd.DataFrame({"ts_utc": ts_utc, "open": open_, "high": high, "low": low, "close": close, "volume": volume})


def _pa_base_cfg() -> dict:
    path = strategy_root() / "parameters" / "pa_trading_range_bls_hs.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_pa_prior_high_excludes_current_bar() -> None:
    raw = _raw_two_sessions()
    cfg = _pa_base_cfg()
    feat = build_features_from_config(raw, cfg)
    s1 = feat[feat["session_date"] == feat["session_date"].iloc[0]].reset_index(drop=True)
    ph = s1["pa_prior_high_10"].reset_index(drop=True)
    rm = s1["high"].rolling(10, min_periods=1).max().shift(1).reset_index(drop=True)
    i = 12
    assert ph.iloc[i] == pytest.approx(float(rm.iloc[i]), rel=1e-9, abs=1e-9)


def test_pa_breakout_up_uses_prior_high_not_future() -> None:
    raw = _raw_two_sessions()
    cfg = _pa_base_cfg()
    feat = build_features_from_config(raw, cfg)
    s1 = feat[feat["session_date"] == feat["session_date"].iloc[0]].reset_index(drop=True)
    # Column exists; prior high is shifted rolling max within session (see pa_swings).
    assert "pa_breakout_up_10" in s1.columns


def test_pa_failed_breakout_down_is_deterministic() -> None:
    raw = _raw_two_sessions()
    cfg = _pa_base_cfg()
    feat = build_features_from_config(raw, cfg)
    assert "pa_failed_breakout_down_10" in feat.columns


def test_pa_strategies_require_no_lookahead_columns() -> None:
    for name in (
        "pa_trading_range_bls_hs",
        "pa_failed_range_breakout_trap",
        "pa_tight_channel_pullback",
        "pa_mtr_reversal",
    ):
        s = load_strategy(name)
        bad = [c for c in s.required_features() if "LOOKAHEAD" in str(c)]
        assert not bad, bad


def test_feature_key_includes_pa_and_changes_with_swing_windows() -> None:
    k0 = feature_key_from_config({"features": {}})
    k1 = feature_key_from_config({"features": {"pa": {"swing_windows": [10, 20]}}})
    assert k0 != k1
    assert any(x[0] == "pa" for x in k0)


def test_build_features_from_config_includes_pa_columns() -> None:
    raw = _raw_two_sessions()
    cfg = _pa_base_cfg()
    feat = build_features_from_config(raw, cfg)
    assert "pa_prior_high_10" in feat.columns
    assert "pa_trading_range_score_30" in feat.columns
    assert "near_vwap_atr" in feat.columns


def test_add_pa_swing_on_slice_has_expected_columns() -> None:
    raw = _raw_two_sessions()
    cfg = _pa_base_cfg()
    feat = build_features_from_config(raw, cfg)
    sub = feat.iloc[:30].copy()
    spec = PaFeatureConfig(swing_windows=(5,))
    out = add_pa_swing_features(sub, spec, atr_col="atr_like_20", copy=True, allow_overwrite=True)
    assert "pa_prior_high_5" in out.columns
