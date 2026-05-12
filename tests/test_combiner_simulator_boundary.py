"""Combiner simulator: legacy lazy-load + canonical adapter entry."""

import importlib.util
from pathlib import Path

import src.combiner.simulator as sim


def test_simulator_docstring_mentions_execution_path():
    doc = (sim.__doc__ or "").lower()
    assert "legacy" in doc or "canonical" in doc or "execution" in doc


def test_simulator_canonical_is_callable():
    assert callable(sim.simulate_combiner_canonical)


def test_simulator_has_no_star_export():
    spec = importlib.util.find_spec("src.combiner.simulator")
    assert spec and spec.origin
    body = Path(spec.origin).read_text(encoding="utf-8")
    assert " import *" not in body
