from src.strategies import loader
from src.strategies.metadata import get_strategy_metadata, get_strategy_output_contract


def test_loader_lists_strategies():
    names = loader.available_strategies()
    assert len(names) >= 1


def test_metadata_defaults():
    names = loader.available_strategies()
    name = names[0]
    m = get_strategy_metadata(name)
    assert "family" in m
    assert isinstance(get_strategy_output_contract(name), dict)
