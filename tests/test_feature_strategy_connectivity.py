"""Loader + metadata smoke for Champion-related strategies (no bar data)."""

import pytest

from src.strategies.loader import available_strategies, load_strategy
from src.strategies.metadata import get_strategy_metadata, get_strategy_output_contract


def test_available_strategies_count_35():
    names = available_strategies()
    assert len(names) == 35


@pytest.mark.parametrize(
    "strategy_id",
    [
        "pa_buy_sell_close_trend",
        "gap_acceptance_failure",
        "cci_extreme_snapback",
    ],
)
def test_champion_related_strategies_load(strategy_id: str):
    s = load_strategy(strategy_id)
    assert s is not None
    feats = s.required_features()
    assert isinstance(feats, (list, tuple))
    meta = get_strategy_metadata(strategy_id)
    assert "family" in meta
    get_strategy_output_contract(strategy_id)

