from src.combiner.simulator import CombinerConfig, simulate_combiner_numba


def test_combiner_exports():
    assert CombinerConfig is not None
    assert callable(simulate_combiner_numba)
