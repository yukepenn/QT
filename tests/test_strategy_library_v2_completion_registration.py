from __future__ import annotations

import copy

import yaml

from src.strategies.loader import available_strategies, load_strategy, strategy_root
from src.strategies.metadata import get_strategy_metadata

V2_COMPLETION = [
    "sma20_reclaim_reject",
    "macd_momentum_turn",
    "stochastic_oversold_cross",
    "cci_extreme_snapback",
    "adx_dmi_trend_continuation",
    "supertrend_atr_flip",
    "large_candle_failure",
    "multi_day_level_trap",
    "prior_close_reclaim",
]


def test_strategy_count_after_completion() -> None:
    assert len(available_strategies()) == 25


def test_v2_completion_registered() -> None:
    names = available_strategies()
    for s in V2_COMPLETION:
        assert s in names


def test_v2_completion_supports_fast() -> None:
    for s in V2_COMPLETION:
        assert load_strategy(s).supports_fast is True


def test_v2_yaml_and_metadata() -> None:
    base = strategy_root()
    for s in V2_COMPLETION:
        assert (base / "parameters" / f"{s}.yaml").is_file()
        assert (base / "testing_parameters" / f"{s}_focused.yaml").is_file()
        m = get_strategy_metadata(s)
        assert m.get("family") not in (None, "unknown")
        assert m.get("conflict_group") == "QQQ_directional"


def test_v2_no_lookahead_required_features() -> None:
    for s in V2_COMPLETION:
        st = load_strategy(s)
        for c in st.required_features():
            assert "LOOKAHEAD" not in c


def test_v2_validate_defaults() -> None:
    for s in V2_COMPLETION:
        st = load_strategy(s)
        path = strategy_root() / "parameters" / f"{s}.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        st.validate_config(cfg)


def test_v2_validate_rejects_bad_side() -> None:
    st = load_strategy("sma20_reclaim_reject")
    path = strategy_root() / "parameters" / "sma20_reclaim_reject.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg.setdefault("signal", {})["side"] = "both"
    try:
        st.validate_config(cfg)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_macd_fast_ge_slow_rejected() -> None:
    st = load_strategy("macd_momentum_turn")
    path = strategy_root() / "parameters" / "macd_momentum_turn.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg.setdefault("features", {})["macd_fast"] = 30
    cfg.setdefault("features", {})["macd_slow"] = 12
    try:
        st.validate_config(cfg)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_v2_context_and_arrays_smoke() -> None:
    import numpy as np
    import pandas as pd

    from src.features.feature_key import build_features_from_config

    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=120, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    r = pd.Series(range(120), dtype=float)
    raw = pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100 + r * 0.01,
            "high": 100.5 + r * 0.01,
            "low": 99.5 + r * 0.01,
            "close": 100 + r * 0.012,
            "volume": 1000 + r * 2,
            "asset": "equity",
            "symbol": "QQQ",
            "root": None,
            "contract": None,
            "average": np.nan,
            "barCount": np.nan,
            "source": "test",
            "useRTH": True,
            "bar_size": "1 min",
        }
    )
    for s in V2_COMPLETION:
        st = load_strategy(s)
        cfg = yaml.safe_load((strategy_root() / "parameters" / f"{s}.yaml").read_text(encoding="utf-8"))
        feat = build_features_from_config(raw, cfg)
        ctx = st.prepare_signal_context(feat, cfg)
        arr = st.generate_signal_arrays_from_context(ctx, cfg)
        assert len(arr["side"]) == len(feat)
        for k in ("side", "valid", "stop", "target_preview", "target_mode_code", "target_r", "risk_preview"):
            assert k in arr
