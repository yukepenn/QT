"""Combiner simulator stub: constants only; accounting pending mainline."""

import importlib.util
from pathlib import Path

import pytest

import src.combiner.simulator as sim


def test_simulator_docstring_describes_pending_path():
    doc = (sim.__doc__ or "").lower()
    assert "pending" in doc or "archive" in doc


def test_simulator_numba_entry_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        sim.simulate_combiner_numba()


def test_simulator_has_no_star_export():
    spec = importlib.util.find_spec("src.combiner.simulator")
    assert spec and spec.origin
    body = Path(spec.origin).read_text(encoding="utf-8")
    assert " import *" not in body
