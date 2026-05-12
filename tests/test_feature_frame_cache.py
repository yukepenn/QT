"""FeatureFrameCache reuses feature rows when feature key matches."""

from __future__ import annotations

from unittest import mock

import pandas as pd

from src.backtest.strategy_runner import FeatureFrameCache


def test_feature_cache_hits_on_second_identical_feature_config(monkeypatch):
    bars = pd.DataFrame({"x": [1, 2]})
    c = FeatureFrameCache(bars)
    feat_df = pd.DataFrame({"x": [1, 2], "f": [0.0, 0.0]})
    sig_df = pd.DataFrame({"sig_valid": [False, False]})

    def fake_build(*_a, **_k):
        return feat_df

    def fake_gen(_s, _f, _c):
        return sig_df

    monkeypatch.setattr(
        "src.backtest.strategy_runner.build_features_for_strategy",
        fake_build,
    )
    monkeypatch.setattr(
        "src.backtest.strategy_runner.generate_strategy_signals",
        fake_gen,
    )
    monkeypatch.setattr(
        "src.backtest.strategy_runner.prepare_canonical_signals",
        lambda _n, raw, metadata=None: raw,
    )

    class S:
        name = "dummy"
        required_features = staticmethod(lambda: ["f"])

    monkeypatch.setattr("src.backtest.strategy_runner.load_strategy", lambda _n: S())

    cfg_a = {"features": {"orb_open_minutes": 15}, "strategy": "dummy"}
    cfg_b = {"features": {"orb_open_minutes": 20}, "strategy": "dummy"}
    cfg_a_dup = {"features": {"orb_open_minutes": 15}, "strategy": "dummy"}

    c.build_signals("dummy", cfg_a, "equity", "QQQ", "2024-01-02", "2024-01-02", None)
    c.build_signals("dummy", cfg_b, "equity", "QQQ", "2024-01-02", "2024-01-02", None)
    c.build_signals("dummy", cfg_a_dup, "equity", "QQQ", "2024-01-02", "2024-01-02", None)

    assert c.misses == 2
    assert c.hits == 1
    assert c.combo_count == 3
