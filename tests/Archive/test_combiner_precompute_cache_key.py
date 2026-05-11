"""Context cache key semantics for Layer 2 precompute (Layer 1–aligned)."""

from __future__ import annotations

import copy

from src.combiner.precompute import build_context_cache_key, normalize_for_context_cache_key
from src.features.feature_key import feature_key_from_config
from src.strategies.loader import load_strategy, load_strategy_config


def test_build_context_cache_key_is_hashable_dict_key() -> None:
    k = build_context_cache_key("failed_orb", (("orb_open_minutes", 15),), (1, 2, 3))
    d = {k: "ok"}
    assert d[k] == "ok"
    assert k[0] == "failed_orb"


def test_normalize_nested_dict_stable() -> None:
    a = normalize_for_context_cache_key({"z": 1, "y": {"b": 2, "a": 1}})
    b = normalize_for_context_cache_key({"y": {"a": 1, "b": 2}, "z": 1})
    assert a == b


def test_different_strategies_do_not_share_context_bucket() -> None:
    fk = (("orb_open_minutes", 15),)
    ctx = ("ctx", 1)
    assert build_context_cache_key("strategy_a", fk, ctx) != build_context_cache_key("strategy_b", fk, ctx)


def test_failed_orb_same_context_different_risk_reuses_cache_key() -> None:
    strat = load_strategy("failed_orb")
    base = load_strategy_config("failed_orb")
    c1 = copy.deepcopy(base)
    c2 = copy.deepcopy(base)
    c1.setdefault("risk", {})["_test_stop_r_only"] = 1.0
    c2.setdefault("risk", {})["_test_stop_r_only"] = 99.0
    assert strat.context_key(c1) == strat.context_key(c2)
    fk1 = feature_key_from_config(c1)
    fk2 = feature_key_from_config(c2)
    assert fk1 == fk2
    k1 = build_context_cache_key("failed_orb", fk1, strat.context_key(c1))
    k2 = build_context_cache_key("failed_orb", fk2, strat.context_key(c2))
    assert k1 == k2


def test_failed_orb_context_driving_signal_change_changes_key() -> None:
    strat = load_strategy("failed_orb")
    base = load_strategy_config("failed_orb")
    c1 = copy.deepcopy(base)
    c2 = copy.deepcopy(base)
    c1.setdefault("signal", {})["fail_window_bars"] = 5
    c2.setdefault("signal", {})["fail_window_bars"] = 12
    assert strat.context_key(c1) != strat.context_key(c2)
    fk = feature_key_from_config(c1)
    assert fk == feature_key_from_config(c2)
    assert build_context_cache_key("failed_orb", fk, strat.context_key(c1)) != build_context_cache_key(
        "failed_orb", fk, strat.context_key(c2)
    )
