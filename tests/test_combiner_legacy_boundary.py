"""Combiner simulator remains an explicit legacy shim."""

import importlib.util
from pathlib import Path


def test_simulator_docstring_flags_legacy():
    import src.combiner.simulator as sim

    doc = (sim.__doc__ or "").lower()
    assert "legacy" in doc
    assert "canonical" in doc or "not" in doc


def test_simulator_reexports_reference_legacy_module():
    import src.combiner.simulator as sim
    import src.combiner.legacy.simulator_legacy as leg

    assert sim.simulate_combiner_numba is leg.simulate_combiner_numba
    assert sim.CombinerConfig is leg.CombinerConfig


def test_simulator_has_no_star_export():
    spec = importlib.util.find_spec("src.combiner.simulator")
    assert spec and spec.origin
    body = Path(spec.origin).read_text(encoding="utf-8")
    assert " import *" not in body
