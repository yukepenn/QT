"""PA Batch A strategies: load, validate, keys, no LOOKAHEAD."""

from __future__ import annotations

import pytest

from src.strategies.loader import apply_overrides, load_strategy, load_strategy_config, strategy_root
from tests.pa_batch_a_fixtures import merged_focused_config

PA_BATCH_A = (
    "pa_trading_range_bls_hs",
    "pa_failed_range_breakout_trap",
    "pa_tight_channel_pullback",
    "pa_mtr_reversal",
)

PA_BATCH_B = (
    "pa_broad_channel_zone",
    "pa_climax_reversal",
    "pa_second_entry_pullback",
    "pa_wedge_reversal",
)

PA_BATCH_C = (
    "pa_buy_sell_close_trend",
    "pa_generic_breakout_pullback",
)

PA_ALL = PA_BATCH_A + PA_BATCH_B + PA_BATCH_C


@pytest.mark.parametrize("name", PA_ALL)
def test_load_strategy(name: str) -> None:
    s = load_strategy(name)
    assert s.name == name
    assert s.supports_fast is True
    bad = [c for c in s.required_features() if "LOOKAHEAD" in str(c)]
    assert not bad, bad


@pytest.mark.parametrize("name", PA_ALL)
def test_validate_default_and_focused_yaml(name: str) -> None:
    s = load_strategy(name)
    s.validate_config(load_strategy_config(name))
    s.validate_config(merged_focused_config(name))


@pytest.mark.parametrize("name", PA_ALL)
def test_context_and_param_keys_react_to_config(name: str) -> None:
    s = load_strategy(name)
    cfg0 = load_strategy_config(name)
    assert s.context_key(cfg0) == s.context_key(cfg0)
    assert s.normalized_param_key(cfg0) == s.normalized_param_key(cfg0)
    cfg1 = apply_overrides(cfg0, {"risk.target_r": 9.99})
    assert s.normalized_param_key(cfg0) != s.normalized_param_key(cfg1)


def test_focused_yaml_files_exist() -> None:
    base = strategy_root() / "testing_parameters"
    for name in PA_ALL:
        assert (base / f"{name}_focused.yaml").is_file()
