from src.combiner.simulator import CombinerConfig, simulate_combiner_canonical, simulate_combiner_numba


def test_combiner_exports():
    assert CombinerConfig is not None
    assert callable(simulate_combiner_numba)
    assert callable(simulate_combiner_canonical)


def test_legacy_reference_loads():
    from src.combiner import simulator as sim

    m = sim._legacy_reference()
    assert hasattr(m, "simulate_combiner_numba")
