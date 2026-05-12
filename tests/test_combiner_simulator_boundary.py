"""Combiner simulator re-exports reference Numba Layer 2 implementation."""

import importlib.util
from pathlib import Path

import src.combiner.reference_simulator as ref
import src.combiner.simulator as sim


def test_simulator_docstring_describes_reference_path():
    doc = (sim.__doc__ or "").lower()
    assert "numba" in doc or "reference" in doc


def test_simulator_reexports_reference_module():
    assert sim.simulate_combiner_numba is ref.simulate_combiner_numba
    assert sim.CombinerConfig is ref.CombinerConfig


def test_simulator_has_no_star_export():
    spec = importlib.util.find_spec("src.combiner.simulator")
    assert spec and spec.origin
    body = Path(spec.origin).read_text(encoding="utf-8")
    assert " import *" not in body
